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
    cache_root=Path(cache_root);jobs_root=Path(jobs_root);output=Path(output)
    rows=[];sources=[];cache={};failures=[]
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
                'kind':task['kind'],'gamma':task['gamma'],'old_schema':1,'new_schema':2,
                'source_job_sha256':sha(jobfile),'fitted_graph_hash':fitted_hash,
                'former_within_class_components_mean':job['graph']['within_class_components_mean'],
                **graph_diagnostics(F,Wfit,y)})
        except Exception as exc:failures.append({'job':str(jobfile),'status':'NOT_REGENERATED','error':repr(exc)})
    if not rows:raise ValueError('No hash-verified historical graphs; no output written')
    output.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (output/'graph_diagnostics_schema2.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        writer.writerows({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)
    manifest={'schema':2,'rows':len(rows),'unchanged_historical_records':True,'failures':failures,
        'recovered_sources':sources,'output_sha256':sha(output/'graph_diagnostics_schema2.csv'),
        'correction':'The old statistic counted whole-graph components covering a class. Schema 2 computes components in the class-induced subgraph, including isolates.'}
    (output/'graph_diagnostic_correction_manifest.json').write_text(json.dumps(json_ready(manifest),indent=2)+'\n')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-root',required=True);parser.add_argument('--jobs-root',default='results/next_round/jobs')
    parser.add_argument('--output',default='results/submission_refresh')
    args=parser.parse_args();print(json.dumps(regenerate(cache_root=args.cache_root,jobs_root=args.jobs_root,output=args.output),indent=2))


if __name__=='__main__':main()
