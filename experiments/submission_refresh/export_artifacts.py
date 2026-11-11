"""Atomically export/recover scientific objects and logical metadata.

Archives can contain restricted source-derived arrays. Keep them outside Git
unless redistribution rights are established; public access is not a license.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import re
import tarfile
import tempfile
import shutil
from .core import ROOT,ArtifactStore,atomic_json,digest


def references(value):
    if isinstance(value,dict):
        if {'sha256','path','kind'}<=set(value):yield value
        else:
            for child in value.values():yield from references(child)
    elif isinstance(value,(list,tuple)):
        for child in value:yield from references(child)


def _name(name):
    if not isinstance(name,str) or not name or '\\' in name:raise ValueError('unsafe archive path')
    path=PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or str(path)!=name or name=='.':raise ValueError('unsafe archive path')
    return name


def _object_reference(ref):
    name=_name(ref['path']);sha=ref['sha256']
    if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha):raise ValueError('invalid object hash')
    if not name.startswith('objects/'+sha[:2]+'/') or Path(name).name.split('.')[0]!=sha:
        raise ValueError('object path does not match its content identity')
    return name


def _validate_logical(logical,object_refs,extras):
    seen={};object_paths={ref['path'] for ref in object_refs};object_keys={(ref['path'],ref['sha256']) for ref in object_refs};extra_paths={ref['relative_path'] for ref in extras}
    reserved_paths=object_paths|extra_paths
    for record in logical:
        name=_name(record.get('record',''));ref=record['object'];_object_reference(ref)
        if name.startswith('objects/') or name in {'EXPORT_MANIFEST.json','RECOVERED_EXPORT.json'} or name in reserved_paths:
            raise ValueError('logical recovery path conflicts with a reserved scientific object')
        if name in seen and seen[name]!=ref['sha256']:raise ValueError('conflicting logical recovery paths')
        seen[name]=ref['sha256']
        if (ref['path'],ref['sha256']) not in object_keys:
            raise ValueError('logical record refers to an unlisted object')


def _archive_manifest(stream):
    members=stream.getmembers();names=[member.name for member in members]
    if len(names)!=len(set(names)):raise ValueError('duplicate archive member path')
    for member in members:
        _name(member.name)
        if not member.isfile():raise ValueError('archive members must be regular files')
    handle=stream.extractfile('EXPORT_MANIFEST.json')
    if handle is None:raise ValueError('missing export manifest')
    payload=handle.read();manifest=json.loads(payload)
    if manifest.get('schema')!='recoverable-scientific-export-v1':raise ValueError('unknown export schema')
    manifest_sha=hashlib.sha256(payload).hexdigest();manifest_path='objects/'+manifest_sha[:2]+'/'+manifest_sha+'.json'
    objects=manifest['objects'];extra=manifest['extra_files'];logical=manifest['logical_records']
    object_names=[]
    for ref in objects:object_names.append(_object_reference(ref))
    extra_names=[_name(ref['relative_path']) for ref in extra]
    if len(object_names+extra_names)!=len(set(object_names+extra_names)):raise ValueError('conflicting object/extra paths')
    if any(name.startswith('objects/') or name in ['EXPORT_MANIFEST.json','RECOVERED_EXPORT.json'] for name in extra_names):raise ValueError('extra file conflicts with reserved object namespace')
    _validate_logical(logical,objects,extra)
    allowed=set(object_names+extra_names+['EXPORT_MANIFEST.json',manifest_path])
    if set(names)!=allowed:raise ValueError('archive has missing or unlisted scientific members')
    return manifest,payload,manifest_path


def _verify(stream,manifest,payload,manifest_path):
    expected={ref.get('path',ref.get('relative_path')):ref for ref in manifest['objects']+manifest['extra_files']}
    expected[manifest_path]={'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload)}
    expected['EXPORT_MANIFEST.json']=expected[manifest_path]
    # Iterate in archive order to avoid quadratic seeking in gzip archives.
    for member in stream.getmembers():
        ref=expected[member.name]
        if ref.get('bytes') is not None and member.size!=ref['bytes']:raise ValueError('corrupt archive object size')
        handle=stream.extractfile(member)
        if handle is None or hashlib.file_digest(handle,'sha256').hexdigest()!=ref['sha256']:raise ValueError('corrupt archive object')


def export(artifact_root,output,manifest_paths=None):
    store=ArtifactStore(artifact_root);objects={};logical=[];input_manifests=[];declared_extra=[]
    def visit(value):
        for ref in references(value):
            _object_reference(ref)
            if ref['sha256'] in objects:
                previous=objects[ref['sha256']]
                if any(previous.get(key)!=ref.get(key) for key in ['path','kind']):raise ValueError('one hash has conflicting object references')
                continue
            item=store.get(ref);objects[ref['sha256']]=ref
            if isinstance(item,(dict,list)):visit(item)
    for name in (manifest_paths or ['results/submission_refresh/artifact_manifest.json','results/subset_search/artifact_manifest.json','results/extension_verification/artifact_manifest.json']):
        path=ROOT/name
        if not path.exists():continue
        manifest=json.loads(path.read_text());visit(manifest)
        input_manifests.append({'path':name,'sha256':digest(path)})
        logical.extend(record for record in manifest.get('records',[]) if 'object'in record)
        declared_extra.extend(manifest.get('extra_files',[]))
    extra=list(declared_extra);audit=store.root/'usps_audit'
    if audit.exists():
        for path in sorted(audit.rglob('*')):
            if path.is_file():extra.append({'relative_path':str(path.relative_to(store.root)),'sha256':digest(path),'bytes':path.stat().st_size})
    by_extra={}
    for ref in extra:
        relative=_name(ref['relative_path']);path=(store.root/relative).resolve()
        if store.root not in path.parents or not path.is_file() or digest(path)!=ref['sha256'] or path.stat().st_size!=ref['bytes']:
            raise ValueError('declared raw scientific file missing or changed: '+relative)
        if relative in by_extra and by_extra[relative]!=ref:raise ValueError('conflicting raw scientific file records')
        by_extra[relative]=ref
    extra=list(by_extra.values())
    if not objects and not extra:raise ValueError('empty scientific export')
    _validate_logical(logical,list(objects.values()),extra)
    manifest={'schema':'recoverable-scientific-export-v1','logical_records':logical,'objects':list(objects.values()),
        'extra_files':extra,'input_manifests':input_manifests,'restriction':'Local scientific archive; redistribution rights not inferred'}
    manifest_ref=store.put(manifest);objects[manifest_ref['sha256']]=manifest_ref
    output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    descriptor,name=tempfile.mkstemp(prefix='.scientific-export-',suffix='.tar.gz',dir=output.parent);os.close(descriptor);tmp=Path(name)
    try:
        # Array objects already use compressed NPZ. A fast outer gzip pass
        # keeps archive packaging within the shared finalization allowance.
        with tarfile.open(tmp,'w:gz',compresslevel=1) as stream:
            for ref in objects.values():stream.add(store.root/ref['path'],arcname=ref['path'])
            for ref in extra:stream.add(store.root/ref['relative_path'],arcname=ref['relative_path'])
            stream.add(store.root/manifest_ref['path'],arcname='EXPORT_MANIFEST.json')
        with tarfile.open(tmp) as stream:
            checked,payload,manifest_path=_archive_manifest(stream);_verify(stream,checked,payload,manifest_path)
        result={'path':str(output),'sha256':digest(tmp),'object_count':len(objects),'extra_files':len(extra),
            'bytes':tmp.stat().st_size,'export_manifest_object':manifest_ref,'verified':True}
        os.replace(tmp,output);atomic_json(output.with_suffix(output.suffix+'.json'),result)
        return result
    finally:tmp.unlink(missing_ok=True)


def recover(archive,output):
    """Verify all members before atomically publishing a new recovered store."""
    archive=Path(archive);output=Path(output).resolve()
    if output.exists():raise ValueError('recovery output must not already exist')
    output.parent.mkdir(parents=True,exist_ok=True);tmp=Path(tempfile.mkdtemp(prefix='.recover-',dir=output.parent))
    try:
        with tarfile.open(archive) as stream:
            manifest,payload,manifest_path=_archive_manifest(stream);_verify(stream,manifest,payload,manifest_path)
            members_by_name={member.name:member for member in stream.getmembers()}
            for ref in manifest['objects']+manifest['extra_files']:
                name=ref.get('path',ref.get('relative_path'));target=tmp/name
                source=stream.extractfile(members_by_name[name])
                target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('wb') as dest:shutil.copyfileobj(source,dest)
            # The manifest's own content-addressed object is deliberately not
            # recursively listed inside itself, but is available after recovery.
            path=tmp/manifest_path;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
            store=ArtifactStore(tmp)
            for record in manifest['logical_records']:
                atomic_json(tmp/record['record'],store.get(record['object']))
            atomic_json(tmp/'RECOVERED_EXPORT.json',{'archive_sha256':digest(archive),
                'objects_verified':len(manifest['objects'])+1,'export_manifest_object_verified':True,
                'extra_files_verified':len(manifest['extra_files'])})
        tmp.rename(output)
    finally:
        if tmp.exists():shutil.rmtree(tmp)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase',choices=['export','recover']);parser.add_argument('--artifact-root');parser.add_argument('--archive',required=True);parser.add_argument('--output');parser.add_argument('--manifest',action='append',dest='manifest_paths',help='Explicit checkout-relative scientific manifest; repeat to define archive scope');args=parser.parse_args()
    if args.phase=='export':print(json.dumps(export(args.artifact_root,args.archive,args.manifest_paths),indent=2))
    else:recover(args.archive,args.output)
if __name__=='__main__':main()
