"""Verified durable scientific archive and streaming recovery validation."""
from __future__ import annotations
import argparse,hashlib,tarfile
from .common import *


def archive(root,output):
    root=Path(root).resolve();output=Path(output).resolve()
    if not (root/'numerical_freeze.json').exists() or read(root/'terminal_evaluation.json')['stage']!='TERMINAL_SCORING_COMPLETE':raise RuntimeError('scientific closure is not complete')
    if output.exists():raise FileExistsError('archive destination must be fresh')
    # Mutable resource/command accounting has a separately saved final receipt.
    folders=['objects','profiles','evaluations','evidence','paths','evidence_checkpoints','attempts']
    names=['cohort_lock.json','numerical_freeze.json','terminal_evaluation.json','clock.json','optional_gate.json','reference_identity_audit.json']
    files=sorted({p for folder in folders for p in (root/folder).rglob('*') if p.is_file()}|{root/n for n in names if (root/n).exists()})
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
    receipt={'archive_name':output.name,'sha256':digest(output),'bytes':output.stat().st_size,'objects_and_records':len(inventory),'inventory_sha256':digest(root/'artifact_inventory.json'),'payload_bytes':sum(r['bytes'] for r in inventory),'scope':'All retained numerical objects, source snapshots, fixed inputs, predictions, duals, checkpoints and scalar histories; final resource ledger supplied separately'}
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


def main():
    p=argparse.ArgumentParser();p.add_argument('--artifact-root',required=True);p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(archive(a.artifact_root,a.output)))
if __name__=='__main__':main()
