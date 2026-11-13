"""Verified durable scientific archive and streaming recovery validation."""
from __future__ import annotations
import argparse,hashlib,tarfile
from .common import *


def retain_reference_closure(store,input_artifact_root=None):
    """Keep exact legacy warm/reference states as available objects, not hashes."""
    imported=[];fallback=ArtifactStore(input_artifact_root) if input_artifact_root else None
    if fallback is not None:
        expected=read(ROOT/'configs/extension_round2/cohort_lock.json')
        for p in sorted((fallback.root/'endpoints').glob('*.json')):
            r=read(p)
            if r['method'] not in ['historical','SSC_reference','QSSC','E1_v2','E5']:continue
            if r['method'] in ['QSSC','E1_v2','E5'] and r['rho']!=.1:continue
            c=expected['cohorts'][r['benchmark']]
            if r['H_sha256']!=c['objects']['H']['sha256'] or r['W_sha256']!=c['objects']['W0']['sha256'] or r['source_fingerprint']!=expected['source_fingerprint'] or r['protocol_sha256']!=expected['protocol_sha256']:raise ValueError('legacy input/source/protocol identity differs')
            target=store.root/'endpoints'/p.name
            if target.exists() and digest(target)!=digest(p):raise ValueError('legacy endpoint collision')
            if not target.exists():atomic_json(target,r)
            imported.append({'path':str(target.relative_to(store.root)),'sha256':digest(target),'benchmark':r['benchmark'],'method':r['method'],'rho':r['rho']})
    pending=list((store.root/'objects').glob('*/*.json'))+list((store.root/'endpoints').glob('*.json'));seen=set();linked=0
    while pending:
        p=pending.pop();key=str(p.relative_to(store.root))
        if key in seen:continue
        seen.add(key)
        for ref in collect_refs(read(p)):
            rel=Path(ref['path'])
            if rel.is_absolute() or '..' in rel.parts or not rel.parts or rel.parts[0]!='objects':raise ValueError('invalid provenance reference path')
            target=store.root/rel
            if not target.exists():
                if fallback is None or not (fallback.root/rel).exists():raise FileNotFoundError('unavailable provenance object: '+str(rel))
                link_ref(fallback,store,ref);linked+=1
            if digest(target)!=ref['sha256']:raise ValueError('provenance object hash mismatch')
            if ref['kind']=='json':pending.append(target)
    receipt={'schema':'ssc-round3-reference-closure-v1','legacy_endpoints':imported,'linked_objects':linked,'qualification':'Exact prior numerical reference/warm states; their old qualification flags are not adopted for new fits. Current results remain in profiles/.'}
    atomic_json(store.root/'imported_reference_manifest.json',receipt);return receipt


def archive(root,output,input_artifact_root=None):
    root=Path(root).resolve();output=Path(output).resolve()
    if not (root/'numerical_freeze.json').exists() or read(root/'terminal_evaluation.json')['stage']!='TERMINAL_SCORING_COMPLETE':raise RuntimeError('scientific closure is not complete')
    if output.exists():raise FileExistsError('archive destination must be fresh')
    retain_reference_closure(ArtifactStore(root),input_artifact_root)
    # Mutable resource/command accounting has a separately saved final receipt.
    folders=['objects','endpoints','profiles','evaluations','evidence','paths','evidence_checkpoints','attempts']
    names=['cohort_lock.json','numerical_freeze.json','terminal_evaluation.json','clock.json','optional_gate.json','reference_identity_audit.json','imported_reference_manifest.json','scheduler_log.jsonl']
    files=sorted({p for folder in folders for p in (root/folder).rglob('*') if p.is_file()}|{root/n for n in names if (root/n).exists()})
    for entry in ResourceLedger(root).state()['entries']:
        completed=root/'command_jobs'/entry['run_id']
        if completed.exists():files.extend(p for p in completed.rglob('*') if p.is_file())
    files=sorted(set(files))
    inventory=[]
    for p in files:
        sha=digest(p)
        if p.parent.parent.name=='objects' and p.stem!=sha:raise ValueError('corrupt content-addressed object')
        inventory.append({'path':str(p.relative_to(root)),'sha256':sha,'bytes':p.stat().st_size})
    atomic_json(root/'artifact_inventory.json',{'schema':'ssc-round3-artifact-inventory-v1','files':inventory,'bytes':sum(r['bytes'] for r in inventory),'resource_ledger':'Final accounting is retained as a separate receipt; no live reservation is archived as a completed ledger'})
    output.parent.mkdir(parents=True,exist_ok=True)
    with tarfile.open(output,'w:gz',compresslevel=1) as tar:
        tar.add(root/'artifact_inventory.json',arcname='artifact_inventory.json')
        for p in files:tar.add(p,arcname=str(p.relative_to(root)),recursive=False)
    receipt={'archive_name':output.name,'sha256':digest(output),'bytes':output.stat().st_size,'objects_and_records':len(inventory),'inventory_sha256':digest(root/'artifact_inventory.json'),'payload_bytes':sum(r['bytes'] for r in inventory),'scope':'All retained numerical objects, source snapshots, fixed inputs, predictions, duals, checkpoints and scalar histories plus completed command records; final accounting and later acceptance records supplied separately'}
    validate(output);atomic_json(root/'archive_receipt.json',receipt);return receipt


def validate(path):
    with tarfile.open(path,'r:gz') as tar:
        first=tar.next()
        if first is None or first.name!='artifact_inventory.json':raise ValueError('missing archive inventory')
        inventory=json.loads(tar.extractfile(first).read());expected={r['path']:r for r in inventory['files']};seen=set()
        while True:
            member=tar.next()
            if member is None:break
            p=Path(member.name)
            if p.is_absolute() or '..' in p.parts or not member.isfile() or member.name not in expected or member.name in seen:raise ValueError('unsafe, extra or duplicate archive member')
            stream=tar.extractfile(member);sha=hashlib.file_digest(stream,'sha256').hexdigest();r=expected[member.name]
            if member.size!=r['bytes'] or sha!=r['sha256']:raise ValueError('archive content hash mismatch')
            seen.add(member.name)
        if seen!=set(expected):raise ValueError('incomplete archive')
    return {'verified_files':len(seen)}


def recover(archive_path,output,ledger_path=None):
    """Validate before extraction; commit only a complete, verified fresh tree."""
    import os,shutil,tempfile
    output=Path(output).resolve()
    if output.exists():raise FileExistsError('recovery destination must be fresh')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tarfile.open(archive_path,'r:gz') as tar:
        first=tar.next()
        if first is None or first.name!='artifact_inventory.json':raise ValueError('missing inventory')
        inventory=json.loads(tar.extractfile(first).read())
    if shutil.disk_usage(output.parent).free<inventory['bytes']+5*2**30:raise OSError('insufficient space for verified recovery plus 5 GiB headroom')
    validate(archive_path);temp=Path(tempfile.mkdtemp(prefix='.round3-recovery-',dir=output.parent))
    try:
        with tarfile.open(archive_path,'r:gz') as tar:tar.extractall(temp,filter='data')
        for entry in inventory['files']:
            p=temp/entry['path']
            if digest(p)!=entry['sha256'] or p.stat().st_size!=entry['bytes']:raise ValueError('recovered object differs')
        if ledger_path:
            state=read(ledger_path)
            if state.get('active'):raise ValueError('resource receipt must contain closed reservations')
            shutil.copyfile(ledger_path,temp/'resource_ledger.json')
        os.replace(temp,output)
    except BaseException:
        shutil.rmtree(temp,ignore_errors=True);raise
    return {'verified_files':len(inventory['files']),'resource_receipt_restored':bool(ledger_path)}


def main():
    p=argparse.ArgumentParser();p.add_argument('command',nargs='?',choices=['archive','recover','validate'],default='archive');p.add_argument('--artifact-root');p.add_argument('--output');p.add_argument('--input-artifact-root');p.add_argument('--archive');p.add_argument('--ledger');a=p.parse_args()
    if a.command=='archive':
        if not a.artifact_root or not a.output:p.error('archive requires --artifact-root and --output')
        result=archive(a.artifact_root,a.output,a.input_artifact_root)
    elif a.command=='recover':
        if not a.archive or not a.output:p.error('recover requires --archive and --output')
        result=recover(a.archive,a.output,a.ledger)
    else:
        if not a.archive:p.error('validate requires --archive')
        result=validate(a.archive)
    print(json.dumps(result))
if __name__=='__main__':main()
