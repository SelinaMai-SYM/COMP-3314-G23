"""No-data scalar reconstruction with fail-before-write identity validation."""
import gzip,hashlib,os,shutil,tempfile
from .common import read,digest,Path
from .report import render


def rebuild(manifest_path,output):
    manifest_path=Path(manifest_path);manifest=read(manifest_path);root=manifest_path.parent
    for name,sha in manifest['files'].items():
        p=(root/name).resolve()
        if root.resolve() not in p.parents or digest(p)!=sha:raise ValueError('release payload hash mismatch')
    compressed=(root/manifest['records']).read_bytes()
    if hashlib.sha256(compressed).hexdigest()!=manifest['compressed_sha256']:raise ValueError('compressed hash mismatch')
    payload=gzip.decompress(compressed)
    if hashlib.sha256(payload).hexdigest()!=manifest['uncompressed_sha256']:raise ValueError('uncompressed hash mismatch')
    import json
    records=json.loads(payload);ids=[r['id'] for r in records['profiles']]
    if not ids or len(ids)!=len(set(ids)):raise ValueError('empty or duplicate profile primary keys')
    for p in records['profiles']:
        for v in p['panels'].values():
            if v['complete'] and [r['seed'] for r in v['trials']]!=list(range(50)):raise ValueError('missing/duplicate complete trials')
    output=Path(output).resolve()
    if output.exists():raise FileExistsError('reconstruction destination must be fresh')
    output.parent.mkdir(parents=True,exist_ok=True);temp=Path(tempfile.mkdtemp(prefix='.round3-rebuild-',dir=output.parent))
    try:
        counts=render(records,temp,plots=False)
        for p in temp.rglob('*'):
            if not p.is_file() or (p.suffix not in ['.csv','.md'] and p.name!='trials.csv.gz'):continue
            name=str(p.relative_to(temp))
            if name in manifest['files'] and digest(p)!=manifest['files'][name]:raise ValueError('reconstructed table differs: '+name)
        os.replace(temp,output);return counts
    except BaseException:
        shutil.rmtree(temp,ignore_errors=True);raise
