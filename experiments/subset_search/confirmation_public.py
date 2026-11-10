"""Explicit archival seed evidence for a completed, immutable confirmation.

Preparation runs before presentation canonicalization. Public projection runs
only after verified archival. Neither operation selects winners or seed blocks.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import tempfile

from experiments.submission_refresh.core import ROOT,atomic_json,digest,identity

PREPARED='seed_inventory_proof.v1.json'
PROOF='confirmation_seed_proof.public.v1.json'
TRANSFORM='confirmation_namespace_transformation.v1.json'


def _inside(root,relative):
    relative=Path(relative);path=(root/relative).resolve()
    if relative.is_absolute() or root not in path.parents:raise ValueError('public confirmation proof path escapes checkout')
    return path


def _seed_set(values):
    if not isinstance(values,list) or not values or any(type(v) is not int or v<0 for v in values):
        raise ValueError('invalid observed historical rounding-seed set')
    if values!=sorted(set(values)):raise ValueError('historical rounding seeds must be sorted and unique')
    return set(values)


def _block(namespace,used):
    first=namespace.get('first');count=namespace.get('count');seeds=namespace.get('seeds')
    if type(first) is not int or first<1000000 or (first-1000000)%50 or count!=50 or seeds!=list(range(first,first+50)):
        raise ValueError('invalid immutable confirmation seed block')
    if namespace.get('overlap') is not False or namespace.get('no_reselection') is not True or used.intersection(seeds):
        raise ValueError('confirmation seed proof overlaps or permits reselection')
    if first>1000000+50*len(used):raise ValueError('confirmation block is not the first unused block')
    candidate=1000000
    while used.intersection(range(candidate,candidate+50)):candidate+=50
    if candidate!=first:raise ValueError('confirmation block changed from the first unused block')


def _original(artifact_root,output):
    output=Path(output).resolve();private=Path(artifact_root).resolve()/'confirmation'/'seed_namespace.json'
    public=output/'confirmation_seed_namespace.json'
    if not private.is_file() or not public.is_file():raise ValueError('both frozen namespace copies are required')
    raw=public.read_bytes();namespace=json.loads(raw)
    if private.read_bytes()!=raw:raise ValueError('frozen confirmation namespace copies disagree')
    if namespace.get('version')!=2 or namespace.get('winner_lock_sha256')!=digest(output/'winner_lock.json'):
        raise ValueError('an original version-2 namespace bound to the existing winner lock is required')
    inventory=namespace.get('historical_inventory')
    if not isinstance(inventory,dict) or identity(inventory)!=namespace.get('historical_inventory_sha256'):
        raise ValueError('original historical inventory identity mismatch')
    return private,public,raw,namespace


def _prepared_valid(prepared,namespace,namespace_hash):
    if (prepared.get('schema')!='archival-confirmation-seed-preparation-v1'
        or prepared.get('original_namespace_sha256')!=namespace_hash
        or prepared.get('original_namespace_identity')!=identity(namespace)
        or prepared.get('winner_lock_sha256')!=namespace['winner_lock_sha256']
        or prepared.get('original_historical_inventory_sha256')!=namespace['historical_inventory_sha256']
        or identity(prepared.get('original_historical_inventory'))!=namespace['historical_inventory_sha256']
        or prepared.get('preparation_identity')!=identity({k:v for k,v in prepared.items() if k!='preparation_identity'})):
        raise ValueError('archival seed preparation provenance or payload identity mismatch')
    used=_seed_set(prepared.get('observed_historical_rounding_seeds'))
    inventory=namespace['historical_inventory']
    if (prepared.get('observed_seed_set_sha256')!=identity(sorted(used))
        or len(used)!=inventory['unique_used_seed_count'] or min(used)!=inventory['minimum_used_seed']
        or max(used)!=inventory['maximum_used_seed']
        or prepared.get('seed_block')!={key:namespace[key] for key in ['first','count','seeds','overlap','no_reselection']}):
        raise ValueError('archival seed preparation does not preserve the complete seed set and block')
    _block(namespace,used)
    return used


def _seed_sources_valid(prepared,artifact_root):
    """Exact archived bytes are separate from semantic JSON/CAS records."""
    store=Path(artifact_root).resolve();sources=prepared['original_historical_inventory']['sources']
    refs=prepared.get('archived_seed_sources',[])
    if len(refs)!=len(sources):raise ValueError('archival seed-source byte inventory is incomplete')
    for source,reference in zip(sources,refs):
        expected='confirmation/historical_seed_sources/'+source['sha256']+'.bin'
        suffixes=Path(source['path']).suffixes;format=''.join(suffixes[-2:]) if suffixes[-1:]==['.gz'] else Path(source['path']).suffix
        if (reference.get('original_path')!=source['path'] or reference.get('original_format')!=format
            or reference.get('relative_path')!=expected or reference.get('sha256')!=source['sha256']
            or reference.get('bytes')!=source['bytes']):
            raise ValueError('archival seed-source byte identity mismatch')
        path=(store/expected).resolve()
        if store not in path.parents or not path.is_file() or path.stat().st_size!=source['bytes'] or digest(path)!=source['sha256']:
            raise ValueError('archival seed-source bytes are missing or corrupt')


def _copy_seed_sources(artifact_root,sources):
    store=Path(artifact_root).resolve();folder=store/'confirmation/historical_seed_sources';folder.mkdir(parents=True,exist_ok=True)
    result=[]
    for source in sources:
        original=_inside(ROOT,source['path']);target=folder/(source['sha256']+'.bin')
        if not target.exists():
            fd,name=tempfile.mkstemp(prefix='.seed-source-',dir=folder);temporary=Path(name)
            try:
                with os.fdopen(fd,'wb') as output,original.open('rb') as stream:
                    shutil.copyfileobj(stream,output);output.flush();os.fsync(output.fileno())
                if digest(temporary)!=source['sha256'] or temporary.stat().st_size!=source['bytes']:
                    raise ValueError('historical source changed during exact-byte archival copying')
                try:os.link(temporary,target)
                except FileExistsError:pass
            finally:temporary.unlink(missing_ok=True)
        if target.stat().st_size!=source['bytes'] or digest(target)!=source['sha256']:
            raise ValueError('existing archived seed-source object differs')
        suffixes=Path(source['path']).suffixes;format=''.join(suffixes[-2:]) if suffixes[-1:]==['.gz'] else Path(source['path']).suffix
        result.append({'original_path':source['path'],'original_format':format,
            'relative_path':str(target.relative_to(store)),'sha256':source['sha256'],'bytes':source['bytes']})
    return result


def prepare_seed_inventory_proof(artifact_root,output):
    """Verify exact historical sources once, before raw-tree canonicalization.

    Writes a private, archival preparation record. Execution and resource
    accounting belong to the calling finalization controller.
    """
    from .aggregate import scan_historical_rounding_seeds
    private,public,raw,namespace=_original(artifact_root,output)
    target=private.parent/PREPARED;namespace_hash=digest(public)
    if target.exists():
        prepared=json.loads(target.read_text())
        _prepared_valid(prepared,namespace,namespace_hash)
        _seed_sources_valid(prepared,artifact_root)
        return prepared
    sources=namespace['historical_inventory']['sources']
    for source in sources:
        path=_inside(ROOT,source['path'])
        if not path.is_file() or digest(path)!=source['sha256']:raise ValueError('historical seed source changed before archival preparation')
    used,inventory=scan_historical_rounding_seeds(ROOT,[entry['path'] for entry in sources])
    if inventory['sources']!=sources:raise ValueError('historical seed source metadata changed before archival preparation')
    original=namespace['historical_inventory']
    for key in ['sources_with_rounding_seeds','unique_used_seed_count','minimum_used_seed','maximum_used_seed']:
        if inventory[key]!=original[key]:raise ValueError('historical seed inventory aggregate changed before archival preparation')
    _block(namespace,used)
    prepared={'schema':'archival-confirmation-seed-preparation-v1','original_namespace_sha256':namespace_hash,
        'original_namespace_identity':identity(namespace),'winner_lock_sha256':namespace['winner_lock_sha256'],
        'original_historical_inventory_sha256':namespace['historical_inventory_sha256'],
        'original_historical_inventory':original,'observed_historical_rounding_seeds':sorted(used),
        'observed_seed_set_sha256':identity(sorted(used)),
        'seed_block':{key:namespace[key] for key in ['first','count','seeds','overlap','no_reselection']},
        'archived_seed_sources':_copy_seed_sources(artifact_root,sources),
        'qualification':'Exact source bytes and seed-column inventories verified before canonicalization; no new seed selection or rounding.'}
    prepared['preparation_identity']=identity(prepared)
    _prepared_valid(prepared,namespace,namespace_hash)
    _seed_sources_valid(prepared,artifact_root)
    if digest(public)!=namespace_hash or private.read_bytes()!=raw:raise ValueError('namespace changed during archival preparation')
    atomic_json(target,prepared)
    return prepared


def validate_public_namespace(namespace,output,*,root=ROOT):
    """Verify an archival proof without accessing any removed raw source path."""
    output=Path(output).resolve();root=Path(root).resolve()
    if namespace.get('version')!=3 or namespace.get('winner_lock_sha256')!=digest(output/'winner_lock.json'):
        raise ValueError('public confirmation namespace does not match its immutable winner lock')
    reference=namespace.get('public_seed_proof',{});path=_inside(root,reference.get('path',''))
    if not path.is_file() or digest(path)!=reference.get('sha256'):raise ValueError('public confirmation seed proof hash mismatch')
    proof=json.loads(path.read_text())
    if proof.get('schema')!='public-confirmation-seed-proof-v1':raise ValueError('unknown public confirmation seed-proof schema')
    used=_seed_set(proof.get('observed_historical_rounding_seeds'))
    if proof.get('observed_seed_set_sha256')!=identity(sorted(used)):raise ValueError('public historical seed-set hash mismatch')
    for key in ['winner_lock_sha256','original_namespace_sha256','original_namespace_identity','original_historical_inventory_sha256']:
        namespace_key='historical_inventory_sha256' if key=='original_historical_inventory_sha256' else key
        if proof.get(key)!=namespace.get(namespace_key):raise ValueError('public seed-proof provenance mismatch: '+key)
    if proof.get('seed_block')!={key:namespace.get(key) for key in ['first','count','seeds','overlap','no_reselection']}:
        raise ValueError('public confirmation seed block differs from archived block')
    _block(namespace,used)
    return proof


def project_confirmation_namespace(artifact_root,output,*,archive_receipt,root=None):
    """Replace live-path verification with hash-locked, archived seed evidence."""
    from experiments.submission_refresh.public_records import read_archive_receipt
    from experiments.submission_refresh.scalar_evidence import _publish_files
    root=Path(root or ROOT).resolve();output=Path(output).resolve();store=Path(artifact_root).resolve()
    receipt=read_archive_receipt(archive_receipt);public=output/'confirmation_seed_namespace.json'
    current=json.loads(public.read_text())
    if current.get('version')==3:
        proof=validate_public_namespace(current,output,root=root)
        if proof.get('archive_id')!=receipt['archive_id'] or proof.get('archive_sha256')!=receipt['archive_sha256']:
            raise ValueError('public confirmation proof belongs to a different private archive')
        return current
    private,public,raw,namespace=_original(store,output);namespace_hash=digest(public)
    prepared_path=private.parent/PREPARED
    if not prepared_path.is_file():raise ValueError('verified pre-canonicalization seed preparation is required')
    prepared=json.loads(prepared_path.read_text());expected=receipt['raw_release_inputs']
    if digest(prepared_path)!=expected['seed_inventory_proof']['sha256'] or namespace_hash!=expected['original_namespace']['sha256']:
        raise ValueError('archive receipt does not cover exact seed preparation and original namespace')
    used=_prepared_valid(prepared,namespace,namespace_hash)
    _seed_sources_valid(prepared,store)
    proof={'schema':'public-confirmation-seed-proof-v1','original_namespace_sha256':namespace_hash,
        'original_namespace_identity':identity(namespace),'winner_lock_sha256':namespace['winner_lock_sha256'],
        'original_historical_inventory_sha256':namespace['historical_inventory_sha256'],
        'original_inventory_source_count':len(namespace['historical_inventory']['sources']),
        'archived_exact_seed_source_objects':len({item['sha256'] for item in prepared['archived_seed_sources']}),
        'archived_seed_preparation_sha256':digest(prepared_path),
        'observed_historical_rounding_seeds':sorted(used),'observed_seed_set_sha256':identity(sorted(used)),
        'seed_block':{key:namespace[key] for key in ['first','count','seeds','overlap','no_reselection']},
        'archive_id':receipt['archive_id'],'archive_sha256':receipt['archive_sha256'],
        'recovery_proof_sha256':receipt['recovery_proof_sha256'],
        'qualification':'Historical seed set verified before canonicalization and preserved in the verified private archive. Public resume verifies this proof, not deleted raw-file paths; no winner or seed-block reselection.'}
    target=output/PROOF;transformation=output/TRANSFORM;backup=private.parent/('seed_namespace.original.'+namespace_hash+'.v2.json')
    if target.exists() or transformation.exists():raise ValueError('public confirmation projection outputs already exist')
    if backup.exists() and backup.read_bytes()!=raw:raise ValueError('private original namespace backup differs')
    stage=Path(tempfile.mkdtemp(prefix='.public-confirmation-',dir=output))
    try:
        proof_file=stage/PROOF;atomic_json(proof_file,proof)
        projected={'version':3,**{key:namespace[key] for key in ['first','count','seeds','overlap','no_reselection','winner_lock_sha256']},
            'historical_inventory_sha256':namespace['historical_inventory_sha256'],'original_namespace_sha256':namespace_hash,
            'original_namespace_identity':identity(namespace),
            'public_seed_proof':{'path':str(target.relative_to(root)),'sha256':digest(proof_file)},
            'resume_rule':'Reuse the archived fixed block and verify the public seed proof; never rescan a pruned tree or reselect.'}
        namespace_file=stage/'public_namespace.json';atomic_json(namespace_file,projected)
        transform={'schema':'public-confirmation-namespace-transformation-v1','original_namespace_sha256':namespace_hash,
            'public_namespace_sha256':digest(namespace_file),'public_seed_proof_sha256':digest(proof_file),
            'original_historical_inventory_sha256':namespace['historical_inventory_sha256'],
            'archive_id':receipt['archive_id'],'seed_block_unchanged':True,'winner_lock_unchanged':True}
        transform_file=stage/TRANSFORM;atomic_json(transform_file,transform)
        original_file=stage/'original_namespace.json';original_file.write_bytes(raw)
        if digest(public)!=namespace_hash or private.read_bytes()!=raw:raise ValueError('namespace changed during public projection')
        files=[(proof_file,target),(transform_file,transformation),(namespace_file,public)]
        # _publish_files consumes its sources, so use a distinct staged copy.
        private_file=stage/'private_namespace.json';private_file.write_bytes(namespace_file.read_bytes())
        files.append((private_file,private))
        if not backup.exists():files.append((original_file,backup))
        _publish_files(files,stage)
        return projected
    finally:shutil.rmtree(stage)
