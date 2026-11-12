"""Validate and atomically rebuild a round-two scalar release without data.

This recomputes trial statistics and paired contrasts. Revalidating a solver
certificate requires the separately archived numerical objects and report.py.
"""
from __future__ import annotations
import argparse,csv,gzip,hashlib,io,json,math,shutil,tempfile
from pathlib import Path,PurePosixPath
import numpy as np
from .report import paired
from .common import atomic_json,digest


def validate(manifest_path):
    manifest_path=Path(manifest_path).resolve();root=manifest_path.parent;manifest=json.loads(manifest_path.read_text())
    if manifest['schema']!='ssc-round2-scalar-release-v1' or not manifest['files']:raise ValueError('invalid or empty scalar release')
    for name,record in manifest['files'].items():
        relative=PurePosixPath(name);path=root/name
        if relative.is_absolute() or '..' in relative.parts or not path.is_file() or path.is_symlink() or path.stat().st_size!=record['bytes'] or digest(path)!=record['sha256']:raise ValueError('release identity mismatch: '+name)
    payload=gzip.decompress((root/'trials.csv.gz').read_bytes())
    if hashlib.sha256(payload).hexdigest()!=manifest['trials_uncompressed_sha256']:raise ValueError('uncompressed trial identity mismatch')
    points=list(csv.DictReader((root/'all_points.csv').open()));trials=list(csv.DictReader(io.StringIO(payload.decode())));grouped={};keys=set()
    if not points or not trials:raise ValueError('empty scientific scalar release')
    for trial in trials:
        key=(trial['point_id'],int(trial['seed']))
        if key in keys:raise ValueError('duplicate point/seed')
        keys.add(key);grouped.setdefault(key[0],[]).append(trial)
    point_ids=set();designs=set();count=0
    def near(a,b):
        if not math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-9):raise ValueError(f'scalar statistic mismatch: {a} versus {b}')
    for point in points:
        design=tuple(point[n] for n in ['benchmark','method','variant','rho'])
        if design in designs:raise ValueError('duplicate endpoint design')
        designs.add(design);point_id=point['point_id'];rows=grouped.get(point_id,[])
        if point_id:
            if point_id in point_ids:raise ValueError('duplicate endpoint identity')
            point_ids.add(point_id)
        if rows:
            rows.sort(key=lambda r:int(r['seed']))
            if [int(r['seed']) for r in rows]!=list(range(50)):raise ValueError('incomplete seed set')
            for metric in ['acc','nmi']:
                values=np.array([float(r[metric]) for r in rows])
                if not np.isfinite(values).all() or np.any((values<0)|(values>1)):raise ValueError('invalid trial metric')
                near(100*values.mean(),point[metric+'_mean']);near(100*values.std(ddof=1),point[metric+'_sd'])
            if int(point['trial_count'])!=50:raise ValueError('trial count mismatch')
            count+=1
        elif int(point['trial_count'])!=0 or any(point[n] for n in ['acc_mean','nmi_mean','acc_sd','nmi_sd']):raise ValueError('missing measured trials')
    if set(grouped)-point_ids:raise ValueError('orphaned trial records')
    if count!=manifest['counts']['complete_50_seed_endpoints'] or len(points)!=manifest['counts']['planned_endpoints']:raise ValueError('coverage count mismatch')
    contrasts=list(csv.DictReader((root/'paired_differences.csv').open()))
    for contrast in contrasts:
        target=grouped[contrast['target_point_id']];control=grouped[contrast['control_point_id']]
        def evaluation(rows):return {'trials':[{m:float(r[m]) for m in ['acc','nmi']} for r in rows]}
        actual=paired(evaluation(target),evaluation(control))
        for key in ['ACC_delta_pp','NMI_delta_pp','ACC_lower_pp','ACC_upper_pp','NMI_lower_pp','NMI_upper_pp']:near(actual[key],contrast[key])
    return {'files_verified':len(manifest['files']),'planned_endpoints':len(points),'complete_seed_sets':count,'paired_contrasts_recomputed':len(contrasts),'trials':len(trials),'manifest_sha256':digest(manifest_path),'scope':'Byte integrity, coverage, mean/sample SD and paired bootstrap; numerical certificates require archived arrays'}


def rebuild(manifest_path,output):
    manifest_path=Path(manifest_path).resolve();output=Path(output).resolve();root=manifest_path.parent
    if output==root or root in output.parents:raise ValueError('rebuild destination must be outside the scalar source')
    verification=validate(manifest_path);manifest=json.loads(manifest_path.read_text());output.parent.mkdir(parents=True,exist_ok=True)
    temporary=Path(tempfile.mkdtemp(prefix='.round2-rebuild-',dir=output.parent));previous=None
    try:
        for name in [*manifest['files'],'release_manifest.json']:
            target=temporary/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,target)
        atomic_json(temporary/'REBUILD_VERIFICATION.json',verification)
        if output.exists():
            previous=Path(tempfile.mkdtemp(prefix='.round2-previous-',dir=output.parent));previous.rmdir();output.rename(previous)
        try:temporary.rename(output)
        except BaseException:
            if previous:previous.rename(output)
            raise
        if previous:shutil.rmtree(previous)
    finally:
        if temporary.exists():shutil.rmtree(temporary)
    return verification


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--release-manifest',required=True);parser.add_argument('--output');args=parser.parse_args()
    print(json.dumps(rebuild(args.release_manifest,args.output) if args.output else validate(args.release_manifest),indent=2))
if __name__=='__main__':main()
