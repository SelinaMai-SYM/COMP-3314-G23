"""Recompute schema-2 diagnostics without changing historical measurements."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy import sparse
from experiments.next_round.evaluate import graph_diagnostics
from experiments.v3_reproduction.provenance import sha256_array,json_ready
from experiments.next_round.campaign import _graph_for


def sha(path):return hashlib.file_digest(open(path,'rb'),'sha256').hexdigest()


def regenerate(*,cache_root,jobs_root,output):
    cache_root=Path(cache_root).expanduser().resolve();jobs_root=Path(jobs_root).expanduser().resolve();output=Path(output).expanduser().resolve()
    if not cache_root.is_dir() or not jobs_root.is_dir():raise FileNotFoundError('explicit cache/jobs root is unavailable')
    rows=[];sources=[];cache={};failures=[]
    # A belongs to input X, not the spectral representation F. Audit one A
    # per recovered cache folder, independently of the fitted-W job count.
    for meta_path in sorted(cache_root.glob('*/meta.json')):
        folder=meta_path.parent
        try:
            meta=json.loads(meta_path.read_text());X=np.load(folder/'X.npy');y=np.load(folder/'y.npy');A=sparse.load_npz(folder/'A.npz')
            if sha256_array(X)!=meta['feature_hash'] or sha256_array(y)!=meta['label_hash'] or sha(folder/'A.npz')!=meta['A_hash']:
                raise ValueError('Recovered A/X/labels do not match the saved metadata hashes')
            if A.shape!=(len(X),len(X)) or len(y)!=len(X):raise ValueError('A/X/labels shape mismatch')
            for name in ['X.npy','A.npz','y.npy','meta.json']:
                sources.append({'path':str(folder/name),'sha256':sha(folder/name)})
            rows.append({'run_id':'representation::'+folder.name+'::A','dataset':meta['dataset'],'prep':meta['prep'],
                'phase':'recovered_representation_audit','kind':'upstream_A','gamma':None,'old_schema':1,'new_schema':2,
                'graph_role':'A','length_space':'X','source_meta_sha256':sha(meta_path),'original_graph_file_sha256':meta['A_hash'],
                'input_feature_hash':meta['feature_hash'],'label_hash':meta['label_hash'],
                'former_within_class_components_mean':None,**graph_diagnostics(X,A,y)})
        except Exception as exc:failures.append({'cache_folder':str(folder),'graph_role':'A','status':'NOT_REGENERATED','error':repr(exc)})
    for jobfile in sorted(jobs_root.glob('*.json')):
        job=json.loads(jobfile.read_text())
        if job.get('status')!='COMPLETED':continue
        task=job['task'];folder=cache_root/(task['dataset']+'__'+task['prep'])
        try:
            if folder not in cache:
                F=np.load(folder/'F.npy');W=sparse.load_npz(folder/'W.npz');y=np.load(folder/'y.npy')
                meta=json.loads((folder/'meta.json').read_text());cache[folder]=(F,W,y,meta)
                for name in ['F.npy','W.npz','y.npy','meta.json']:
                    sources.append({'path':str(folder/name),'sha256':sha(folder/name)})
            F,W,y,meta=cache[folder];rep=job['representation']
            if sha256_array(F)!=rep['F_hash'] or sha(folder/'W.npz')!=rep['W_hash'] or sha256_array(y)!=rep['label_hash']:
                raise ValueError('Recovered representation does not match historical job hashes')
            Wfit=_graph_for(task,F,W,y)
            fitted_hash=hashlib.sha256(np.ascontiguousarray(Wfit.data).tobytes()+np.ascontiguousarray(Wfit.indices).tobytes()+np.ascontiguousarray(Wfit.indptr).tobytes()).hexdigest()
            if fitted_hash!=job['fitted_graph_hash']:raise ValueError('Reconstructed fitted graph does not match historical hash')
            rows.append({'run_id':job['run_id'],'dataset':task['dataset'],'prep':task['prep'],'phase':task['phase'],
                'kind':task['kind'],'gamma':task['gamma'],'old_schema':1,'new_schema':2,'graph_role':'W','length_space':'F',
                'source_job_sha256':sha(jobfile),'fitted_graph_hash':fitted_hash,
                'former_within_class_components_mean':job['graph']['within_class_components_mean'],
                **graph_diagnostics(F,Wfit,y)})
        except Exception as exc:failures.append({'job':str(jobfile),'graph_role':'W','status':'NOT_REGENERATED','error':repr(exc)})
    if not rows:raise ValueError('No hash-verified historical graphs; no output written')
    output.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (output/'graph_diagnostics_schema2.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        writer.writerows({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)
    manifest={'schema':2,'rows':len(rows),'rows_by_graph_role':{role:sum(r['graph_role']==role for r in rows) for role in ['A','W']},
        'A_length_space':'X','W_length_space':'F','unchanged_historical_records':True,'failures':failures,
        'recovered_sources':list({(r['path'],r['sha256']):r for r in sources}.values()),'output_sha256':sha(output/'graph_diagnostics_schema2.csv'),
        'correction':'The old statistic counted whole-graph components covering a class. Schema 2 computes class-induced components including isolates. Upstream A edge lengths are now evaluated in saved input X; fitted W edge lengths are evaluated in saved F. A/W pollution and geometry are separate.'}
    (output/'graph_diagnostic_correction_manifest.json').write_text(json.dumps(json_ready(manifest),indent=2)+'\n')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-root',required=True);parser.add_argument('--jobs-root',default='results/next_round/jobs')
    parser.add_argument('--output',default='results/submission_refresh')
    args=parser.parse_args();print(json.dumps(regenerate(cache_root=args.cache_root,jobs_root=args.jobs_root,output=args.output),indent=2))


if __name__=='__main__':main()
