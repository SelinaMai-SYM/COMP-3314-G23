"""Budgeted, append-only performance mechanism campaign. See frozen protocol.yaml."""
from __future__ import annotations
import argparse,csv,hashlib,json,multiprocessing as mp,os,resource,subprocess,time,traceback
from pathlib import Path
import numpy as np
import yaml
from scipy import sparse
from threadpoolctl import threadpool_limits
from SSC_method.graph_construction import knn_affinity
from SSC_method.spectral_embedding import spectral_embedding
from experiments.v3_reproduction.dataset_registry import load_spec,resolve_data_root,l2_normalize_rows,row_normalize
from experiments.v3_reproduction.protocol_registry import load_campaign
from experiments.v3_reproduction.provenance import source_fingerprint,environment_record,sha256_array,json_ready
from method_extension.next_round.certified_solver import solve,graph_arrays,objective,certificate,threshold
from method_extension.next_round.capped_fusion import fit as capped_fit
from .evaluate import evaluate,graph_diagnostics,paired

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/next_round';CACHE=ROOT/'runs/next_round/cache';ARRAYS=ROOT/'runs/next_round/arrays';JOBS=OUT/'jobs'
PRIMARY=['ORL_att92','JAFFE','YaleB_cropped2414','USPS'];KMAP={'ORL_att92':40,'JAFFE':10,'YaleB_cropped2414':38,'YaleB_dengcai32':38,'USPS':10}


def protocol():
    p=yaml.safe_load((ROOT/'configs/next_round/protocol.yaml').read_text())
    for key in ['gamma5','gamma15','tau_over_sF']:p[key]=list(map(float,p[key]))
    return p
def commit():return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(json_ready(data),sort_keys=True,indent=2)+'\n');tmp.replace(path)
def filehash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save_sparse(path,W):sparse.save_npz(path,sparse.csr_matrix(W))
def ident(task):return hashlib.sha256(json.dumps(task,sort_keys=True,default=str).encode()).hexdigest()[:24]
def load_track(dataset,prep='Y0'):
    folder=CACHE/(dataset+'__'+prep);meta=json.loads((folder/'meta.json').read_text());return folder,meta,np.load(folder/'F.npy'),sparse.load_npz(folder/'W.npz'),np.load(folder/'y.npy')


def prepare(data_root):
    campaign=load_campaign(ROOT/'configs/v3/campaign.yaml');campaign['data_root']=data_root;results=[]
    with threadpool_limits(limits=1):
        for dataset,prep in [(d,'Y0') for d in PRIMARY+['YaleB_dengcai32']]+[('YaleB_dengcai32','Y3')]:
            spec=next(s for s in campaign['_datasets']['specs'] if s['dataset_id']==dataset);record=load_spec(resolve_data_root(campaign),spec)
            if not record['available']:results.append({'dataset':dataset,'status':'NOT_RUN_DATA_BLOCKED','reason':record['reason']});continue
            X=record['X'];y=record['y'];X=l2_normalize_rows(X) if prep in ['Y1','Y3'] else X
            folder=CACHE/(dataset+'__'+prep);folder.mkdir(parents=True,exist_ok=True)
            F,info=spectral_embedding(X,KMAP[dataset]);A,_=knn_affinity(X,k=5)
            if prep in ['Y2','Y3']:F=row_normalize(F)
            W,_=knn_affinity(F,k=5);t=threshold(F,W)
            for name,array in [('X',X),('y',y),('F',F)]:np.save(folder/(name+'.npy'),array)
            save_sparse(folder/'A.npz',A);save_sparse(folder/'W.npz',W)
            meta={'dataset':dataset,'prep':prep,'K':KMAP[dataset],'shape':list(X.shape),'feature_hash':sha256_array(X),'label_hash':sha256_array(y),'F_hash':sha256_array(F),'A_hash':filehash(folder/'A.npz'),'W_hash':filehash(folder/'W.npz'),'source_commit':commit(),'source_hash':source_fingerprint(),'environment':environment_record(),'gamma0':t['gamma0'],'scale':t['scale'],'eigenvalues':info.get('eigenvalues'),'historical_identity':'NEW_SEEDED_REPRESENTATION; baseline historical F/W not stored in scalar release'}
            dump(folder/'meta.json',meta)
            # Labels are used only for these explicitly marked diagnostic summaries.
            results.append({**meta,'graph_A':graph_diagnostics(F,A,y),'graph_W':graph_diagnostics(F,W,y)})
            print('PREPARED',dataset,prep,F.shape,flush=True)
    dump(OUT/'representations.json',results);return results


def make_manifest():
    p=protocol();tasks=[]
    for gamma in [1.,1e3,1e-6,1e-3,1e6]:
        for dataset in PRIMARY:tasks.append({'phase':'A','dataset':dataset,'prep':'Y0','kind':'original','gamma':gamma})
    for gamma in [1.,1e3,1e-6,1e-3,1e6]:tasks.append({'phase':'A','dataset':'YaleB_dengcai32','prep':'Y0','kind':'original','gamma':gamma})
    # Historical display choices are already frozen; never use them for extension parameters.
    selections=[json.loads(line) for line in (ROOT/'results/final/generated/selection_manifest.jsonl').read_text().splitlines()]
    for selected in selections:
        if selected['track']!='closest_to_paper' or selected['method']!='ssc' or selected['config_id'] is None:continue
        task={'phase':'N0_selected','dataset':selected['dataset_version'],'prep':selected['prep'],'kind':'original','gamma':selected['gamma_effective'],'gamma_nominal':selected['gamma_nominal'],'legacy_variant':selected['variant'],'legacy_config_id':selected['config_id']}
        tasks.append(task)
    for gamma in [1.,1e3,1e-6,1e-3,1e6]:
        for dataset in PRIMARY:
            for kind,seed,tau in [('oracle_delete',None,None),('uniform_mass',None,None)]+[('random_delete',seed,None) for seed in [300,301,302]]+[('static',None,t) for t in p['tau_over_sF']]:
                task={'phase':'B','dataset':dataset,'prep':'Y0','kind':kind,'gamma':gamma}
                if seed is not None:task['delete_seed']=seed
                if tau is not None:task['tau_multiplier']=tau
                tasks.append(task)
    for dataset in PRIMARY:
        for fidelity in ['radial','squared']:
            for gamma in p['gamma15']:
                if fidelity=='radial' and gamma in p['gamma5']:continue
                tasks.append({'phase':'C','dataset':dataset,'prep':'Y0','kind':'original','gamma':gamma,'fidelity':fidelity})
            for gamma in p['gamma5']:
                for tau in p['tau_over_sF']:tasks.append({'phase':'C','dataset':dataset,'prep':'Y0','kind':'capped','gamma':gamma,'tau_multiplier':tau,'fidelity':fidelity})
    # Fixed operating points first within C; the whole search remains frozen.
    c=[t for t in tasks if t['phase']=='C'];other=[t for t in tasks if t['phase']!='C'];c.sort(key=lambda t:(t['gamma']!=1,t.get('tau_multiplier',1)!=1,PRIMARY.index(t['dataset']),t.get('fidelity','radial'),t['kind'],t['gamma']))
    tasks=other+c
    for t in tasks:t['task_id']=ident(t)
    dump(ROOT/'configs/next_round/job_manifest.json',{'protocol_version':p['version'],'tasks':tasks,'counts':dict(__import__('collections').Counter(t['phase'] for t in tasks)),'notes':'Task identities are immutable; execution run ids additionally include source/protocol/data hashes. SC is evaluated once per representation.'})
    return tasks


def _graph_for(task,F,W,y):
    kind=task['kind'];B,i,j,w=graph_arrays(W)
    if kind in ['original','capped']:return W
    keep=y[i]==y[j];target_mass=float(w[keep].sum())
    if kind=='oracle_delete':weights=w*keep
    elif kind=='uniform_mass':weights=w*(target_mass/w.sum() if w.sum() else 0)
    elif kind=='random_delete':
        ids=np.random.default_rng(task['delete_seed']).choice(len(w),int((~keep).sum()),replace=False);weights=w.copy();weights[ids]=0
    elif kind=='static':weights=w*(np.linalg.norm(B@F,axis=1)<=task['tau_multiplier']*threshold(F,W)['scale'])
    else:raise ValueError(kind)
    result=sparse.coo_matrix((np.r_[weights,weights],(np.r_[i,j],np.r_[j,i])),shape=W.shape).tocsr();result.eliminate_zeros();return result


def _worker(task,signature):
    os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
    started=time.perf_counter();cpu=time.process_time();task_id=task['task_id'];run_id=task_id+'-'+signature[:12];path=JOBS/(run_id+'.json')
    try:
        with threadpool_limits(limits=1):
            folder,meta,F,W,y=load_track(task['dataset'],task['prep']);Wfit=_graph_for(task,F,W,y);scale=meta['scale'];fidelity=task.get('fidelity','radial');limit=600. if len(F)<=800 else 1800.
            if task['kind']=='capped':
                # The second start must be the same-objective certified original.
                original=solve(F,W,task['gamma'],time_limit=limit,max_iter=30000)
                starts=[('F',F)]
                if original['certified']:starts.append(('original_SSC',original['G']))
                outputs=[]
                for name,start in starts:
                    r=capped_fit(F,W,task['gamma'],task['tau_multiplier']*scale,fidelity=fidelity,scale=scale,G_init=start,time_limit=limit)
                    outputs.append((name,r))
                name,r=min(outputs,key=lambda pair:pair[1]['objective']);G=r['G'];solver={k:v for k,v in r.items() if k!='G'};solver['selected_start']=name;solver['starts']=[{'start':name,**{k:v for k,v in out.items() if k!='G'}} for name,out in outputs];solver['second_start_available']=original['certified'];qualified=bool(r['local_qualified'] and original['certified']);bound_q=None
            else:
                r=solve(F,Wfit,task['gamma'],delta=scale if fidelity=='squared' else 0.,fidelity=fidelity,time_limit=limit,max_iter=30000,warm_start_irls=True)
                G=r['G'];bound_q=r['q'];solver={k:v for k,v in r.items() if k not in ['G','q']};qualified=r['certified']
            trials,pred,dist=evaluate(F,G,y,meta['K']);ARRAYS.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(ARRAYS/(run_id+'.npz'),G=G,predictions=pred,**({'q':bound_q} if bound_q is not None else {}))
            scores={metric+'_mean':float(np.mean([v[metric] for v in trials])*100) for metric in ['acc','nmi','false_merge_rate','false_split_rate']};scores.update({metric+'_sd':float(np.std([v[metric] for v in trials],ddof=1)*100) for metric in ['acc','nmi']})
            result={'run_id':run_id,'task':task,'status':'COMPLETED','qualified_for_method_contrast':qualified,'source_commit':commit(),'solver_protocol':'IRLS-upper-bound-plus-PDHG-v2','supersedes_run_ids':[f.stem for f in JOBS.glob(task_id+'-*.json') if f!=path],'source_hash':source_fingerprint(),'execution_signature':signature,'protocol_hash':filehash(ROOT/'configs/next_round/protocol.yaml'),'representation':meta,'fitted_graph_hash':hashlib.sha256(np.ascontiguousarray(Wfit.data).tobytes()+np.ascontiguousarray(Wfit.indices).tobytes()+np.ascontiguousarray(Wfit.indptr).tobytes()).hexdigest(),'diagnostic_uses_labels':task['kind'] in ['oracle_delete','uniform_mass','random_delete'],'solver':solver,'graph':graph_diagnostics(F,Wfit,y),'distance':dist,'trials':trials,'scores':scores,'wall_seconds':time.perf_counter()-started,'cpu_seconds':time.process_time()-cpu,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'G_hash':sha256_array(G),'array_path':str((ARRAYS/(run_id+'.npz')).relative_to(ROOT)),'array_redistribution':'Local-only arrays; scalar trials and certificates are published.'}
            dump(path,result)
            print('DONE',task['dataset'],task['kind'],task['gamma'],solver['status'],f"ACC={scores['acc_mean']:.3f}",f"cpu={result['cpu_seconds']:.1f}s",flush=True)
    except BaseException as exc:
        dump(path,{'run_id':run_id,'task':task,'status':'FAILED','error':repr(exc),'traceback':traceback.format_exc(),'source_commit':commit(),'source_hash':signature,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-started});print('FAILED',task,repr(exc),flush=True)


def sc_endpoints():
    for folder in sorted(CACHE.glob('*')):
        if not (folder/'meta.json').is_file():continue
        path=OUT/'sc'/ (folder.name+'.json')
        if path.exists():continue
        meta=json.loads((folder/'meta.json').read_text());F=np.load(folder/'F.npy');y=np.load(folder/'y.npy')
        with threadpool_limits(limits=1):trials,pred,dist=evaluate(F,F,y,meta['K'])
        dump(path,{'dataset':meta['dataset'],'prep':meta['prep'],'representation':meta,'trials':trials,'scores':{metric+'_mean':float(np.mean([v[metric] for v in trials])*100) for metric in ['acc','nmi']},'distance':dist})
        np.save(folder/'sc_predictions.npy',pred)


def run(phases,workers=2,budget_hours=36):
    tasks=json.loads((ROOT/'configs/next_round/job_manifest.json').read_text())['tasks'];p=protocol();JOBS.mkdir(parents=True,exist_ok=True)
    representations={str(f.relative_to(CACHE)):filehash(f) for f in sorted(CACHE.glob('*/meta.json'))}
    signature=hashlib.sha256(json.dumps({'source_hash':source_fingerprint(),'protocol_hash':filehash(ROOT/'configs/next_round/protocol.yaml'),'representations':representations},sort_keys=True).encode()).hexdigest()
    used=sum(json.loads(f.read_text()).get('cpu_seconds',0) for f in JOBS.glob('*.json'));queue=[]
    for task in tasks:
        if task['phase'] not in phases:continue
        if not (CACHE/(task['dataset']+'__'+task['prep'])/'meta.json').is_file():
            dump(JOBS/(task['task_id']+'-'+signature[:12]+'.json'),{'task':task,'status':'NOT_RUN_DATA_BLOCKED','cpu_seconds':0});continue
        path=JOBS/(task['task_id']+'-'+signature[:12]+'.json')
        if path.exists():continue
        queue.append(task)
    context=mp.get_context('spawn');active=[];spent=0.;begin=time.perf_counter();baseline=resource.getrusage(resource.RUSAGE_CHILDREN);remaining=max(0,budget_hours*3600-used)
    while queue or active:
        now=time.perf_counter();r=resource.getrusage(resource.RUSAGE_CHILDREN);spent=(r.ru_utime+r.ru_stime-baseline.ru_utime-baseline.ru_stime)
        estimated=spent+sum(now-start for _,_,start in active)
        slots_file=ROOT/'local/max_workers.txt'
        slots=min(workers,2,int(slots_file.read_text()) if slots_file.exists() else 2)
        while queue and len(active)<max(1,slots) and estimated<remaining:
            task=queue.pop(0);proc=context.Process(target=_worker,args=(task,signature));proc.start();active.append((proc,task,time.perf_counter()))
        for item in active[:]:
            proc,task,start=item;limit=(600 if task['dataset'] in ['ORL_att92','JAFFE'] else 1800)*(3 if task['kind']=='capped' else 1)+180
            if not proc.is_alive():proc.join();active.remove(item)
            elif now-start>limit or estimated>=remaining:
                proc.terminate();proc.join(5)
                if proc.is_alive():proc.kill();proc.join()
                active.remove(item);path=JOBS/(task['task_id']+'-'+signature[:12]+'.json')
                if not path.exists():dump(path,{'task':task,'run_id':path.stem,'status':'TIMEOUT' if now-start>limit else 'NOT_RUN_BUDGET','cpu_seconds':now-start,'wall_seconds':now-start,'source_hash':signature,'source_commit':commit()})
        if not active and queue and estimated>=remaining:
            for task in queue:dump(JOBS/(task['task_id']+'-'+signature[:12]+'.json'),{'task':task,'status':'NOT_RUN_BUDGET','cpu_seconds':0})
            queue=[]
        if active:time.sleep(1)
    dump(OUT/'resource_usage.json',{'max_cpu_core_hours':budget_hours,'charged_cpu_seconds':used+spent,'workers':min(workers,2),'rss_limit_target_gib':8,'wall_seconds_this_invocation':time.perf_counter()-begin})


def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='command',required=True);preparep=sub.add_parser('prepare');preparep.add_argument('--data-root',required=True);sub.add_parser('manifest');runp=sub.add_parser('run');runp.add_argument('--phases',nargs='+',default=['A','N0_selected']);runp.add_argument('--workers',type=int,default=2);runp.add_argument('--budget-hours',type=float,default=36);sub.add_parser('sc')
    args=ap.parse_args()
    if args.command=='manifest':make_manifest()
    elif args.command=='prepare':prepare(args.data_root)
    elif args.command=='sc':sc_endpoints()
    elif args.command=='run':run(args.phases,args.workers,args.budget_hours)
if __name__=='__main__':main()
