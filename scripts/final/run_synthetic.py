"""Prespecified synthetic edge/anchor interventions, including the fidelity 2x2."""
from pathlib import Path
import json,csv,time,hashlib,subprocess
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_limits
from SSC_method.graph_construction import knn_affinity
from method_extension.next_round.certified_solver import solve,threshold,graph_arrays
from method_extension.next_round.capped_fusion import fit as capped
from experiments.next_round.evaluate import pair_errors,distance_diagnostics
from experiments.v2_kmeans_protocol.kmeans_trials import fit_lloyd,GREEDY
from benchmarks.metrics.accuracy import clustering_accuracy
from benchmarks.metrics.nmi import normalized_mutual_information
from experiments.v3_reproduction.provenance import source_fingerprint,environment_record,json_ready

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/next_round/synthetic'
SCENARIOS=[{'name':'clean','distance':3.,'sizes':[30,30,30],'outlier':0.,'bridge':0.}]
SCENARIOS += [{'name':f'anchor_{f:g}','distance':3.,'sizes':[30,30,30],'outlier':f,'bridge':0.} for f in [.05,.1,.2]]
SCENARIOS += [{'name':f'bridge_{f:g}','distance':3.,'sizes':[30,30,30],'outlier':0.,'bridge':f} for f in [.05,.1]]
SCENARIOS += [{'name':f'distance_{d:g}','distance':d,'sizes':[30,30,30],'outlier':0.,'bridge':0.} for d in [1.,6.]]
SCENARIOS += [{'name':'imbalanced_clean','distance':3.,'sizes':[10,30,50],'outlier':0.,'bridge':0.},{'name':'imbalanced_bridge','distance':3.,'sizes':[10,30,50],'outlier':0.,'bridge':.1}]
def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(json_ready(data),sort_keys=True,indent=2)+'\n');tmp.replace(path)
def dataset(seed,case):
    d=case['distance'];centers=np.array([[0,0],[d,0],[d/2,d*np.sqrt(3)/2]]);y=np.repeat(np.arange(3),case['sizes']);clean=centers[y]+np.random.default_rng(seed).normal(0,.1,(len(y),2));base=clean+np.random.default_rng(seed+10000).normal(0,.1,clean.shape);W,_=knn_affinity(base,k=5);t=threshold(base,W);F=base.copy();B,i,j,w=graph_arrays(W)
    # Scales are frozen from this scenario's unpolluted baseline, never recalibrated after pollution.
    if case['outlier']:
        rng=np.random.default_rng(seed+20000);ids=rng.permutation(len(F))[:int(round(len(F)*case['outlier']))];directions=rng.normal(size=(len(F),2));directions/=np.linalg.norm(directions,axis=1)[:,None];F[ids]+=5*t['scale']*directions[ids]
    if case['bridge']:
        a,b=np.triu_indices(len(F),1);keep=(y[a]!=y[b])&(np.asarray(W[a,b]).ravel()==0);a,b=a[keep],b[keep];n=int(round(len(w)*case['bridge']));ids=np.random.default_rng(seed+30000).choice(len(a),n,replace=False);value=float(np.median(w[w>0]));W=(W+sparse.coo_matrix((np.full(2*n,value),(np.r_[a[ids],b[ids]],np.r_[b[ids],a[ids]])),shape=W.shape)).tocsr()
    return clean,F,W,y,t

def evaluate(F,G,y,K):
    """Same metrics with an explicit floating-point boundary guard for perfect NMI.

    This local compatibility guard avoids changing an in-flight baseline campaign.
    Values farther than 1e-12 out of range are still implementation errors.
    """
    rows=[];predictions=[]
    for seed in range(50):
        fit=fit_lloyd(G,K,seed,GREEDY);pred=fit['labels'];acc=float(clustering_accuracy(y,pred));nmi=float(normalized_mutual_information(y,pred))
        if not np.isfinite(acc+nmi) or min(acc,nmi)<-1e-12 or max(acc,nmi)>1+1e-12:raise ArithmeticError('metric beyond floating-point bound tolerance')
        rows.append({'seed':seed,'acc':float(np.clip(acc,0,1)),'nmi':float(np.clip(nmi,0,1)),**pair_errors(y,pred),'inertia':fit['inertia'],'warning':fit['kmeans_warning'],'nmi_roundoff_guard_applied':nmi>1 or nmi<0});predictions.append(pred)
    return rows,np.asarray(predictions),distance_diagnostics(F,G,y)

def main():
    OUT.mkdir(parents=True,exist_ok=True);manifest={'seeds':list(range(100,110)),'scenarios':SCENARIOS,'methods':['SC','SSC','squared_linear','radial_capped','squared_capped','static_screen'],'gamma':1.,'tau':'baseline sF','N1_pilot':'original/Huber/squared at gamma=2*baseline_gamma0,delta=.2*baseline_sF; clean/anchor/bridge cases','numeric_metric_guard_tolerance':1e-12,'baseline_scales_frozen':True,'oracle_designed_bridges':True,'primary_claim_scope':'synthetic mechanism only; not a real-data performance claim','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'source_hash':source_fingerprint(),'script_hash':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'environment':environment_record()};dump(OUT/'protocol.json',manifest);dump(OUT/'protocols'/(hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()+'.json'),manifest)
    with threadpool_limits(limits=1):
        for seed in manifest['seeds']:
            for case in SCENARIOS:
                path=OUT/'jobs'/f"{seed}_{case['name']}.json"
                if path.exists():continue
                started=time.perf_counter();cpu=time.process_time();clean,F,W,y,t=dataset(seed,case);scale=t['scale'];outputs=[];linear={}
                for name,fidelity in [('SSC','radial'),('squared_linear','squared')]:
                    r=solve(F,W,1.,delta=scale if fidelity=='squared' else 0.,fidelity=fidelity,time_limit=600.);linear[name]=r
                    outputs.append((name,r['G'],{k:v for k,v in r.items() if k not in ['G','q','history']}))
                outputs.insert(0,('SC',F,{'certified':True,'status':'NO_OPTIMIZATION'}))
                for name,fidelity in [('radial_capped','radial'),('squared_capped','squared')]:
                    starts=[]
                    for init,G0 in [('F',F),('original_SSC',linear['SSC']['G'])]:
                        r=capped(F,W,1.,scale,fidelity=fidelity,scale=scale,G_init=G0,time_limit=600.);starts.append((init,r))
                    init,r=min(starts,key=lambda pair:pair[1]['objective']);meta={k:v for k,v in r.items() if k!='G'};meta.update(selected_start=init,original_start_certified=linear['SSC']['certified'],certified=False,local_qualified=r['local_qualified'] and linear['SSC']['certified'],starts=[{'name':n,**{k:v for k,v in s.items() if k!='G'}} for n,s in starts]);outputs.append((name,r['G'],meta))
                B,i,j,w=graph_arrays(W);active=np.linalg.norm(B@F,axis=1)<=scale;Ws=sparse.coo_matrix((np.r_[w[active],w[active]],(np.r_[i[active],j[active]],np.r_[j[active],i[active]])),shape=W.shape).tocsr();r=solve(F,Ws,1.,time_limit=600.);outputs.append(('static_screen',r['G'],{k:v for k,v in r.items() if k not in ['G','q','history']}))
                # The separately labelled N1 pilot uses its originally fixed primary settings.
                if case['name']=='clean' or case['name'].startswith(('anchor_','bridge_')):
                    for name,fidelity,delta in [('N1_original','radial',0.),('N1_Huber','radial',.2*scale),('N1_squared','squared',.2*scale)]:
                        r=solve(F,W,2*t['gamma0'],delta=delta,fidelity=fidelity,time_limit=600.);meta={k:v for k,v in r.items() if k not in ['G','q','history']}
                        residual=np.linalg.norm(r['G']-F,axis=1);meta['tail_fraction']=float(np.mean(residual>delta)) if delta else None;outputs.append((name,r['G'],meta))
                measured=[]
                for name,G,solver in outputs:
                    trials,_,dist=evaluate(F,G,y,3);measured.append({'method':name,'solver':solver,'trials':trials,'ACC':float(np.mean([r['acc'] for r in trials])*100),'NMI':float(np.mean([r['nmi'] for r in trials])*100),'clean_target_MSE_per_coordinate':float(np.mean((G-clean)**2)),'movement':float(np.linalg.norm(G-F)/np.linalg.norm(F)),'distance':dist})
                dump(path,{'seed':seed,'case':case,'baseline_scale':scale,'baseline_gamma0':t['gamma0'],'results':measured,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-started,'source_protocol_hash':hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()});print('SYNTHETIC',seed,case['name'],flush=True)
    summarize()
def summarize():
    configs=[];trials=[];jobs=[json.loads(p.read_text()) for p in sorted((OUT/'jobs').glob('*.json'))]
    for job in jobs:
        for r in job['results']:
            row={'seed':job['seed'],'scenario':job['case']['name'],'method':r['method'],'ACC':r['ACC'],'NMI':r['NMI'],'MSE':r['clean_target_MSE_per_coordinate'],'movement':r['movement'],'solver_status':r['solver']['status'],'gap':r['solver'].get('gap'),'qualified':r['solver'].get('certified') or r['solver'].get('local_qualified'),'tail_fraction':r['solver'].get('tail_fraction')};configs.append(row)
            for t in r['trials']:trials.append({'synthetic_seed':job['seed'],'scenario':job['case']['name'],'method':r['method'],**t})
    for name,rows in [('configuration_table.csv',configs),('raw_trials.csv',trials)]:
        keys=list(dict.fromkeys(k for r in rows for k in r))
        with (OUT/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    summary=[]
    for scenario in SCENARIOS:
        for method in sorted(set(r['method'] for r in configs)):
            rows=[r for r in configs if r['scenario']==scenario['name'] and r['method']==method]
            if rows:summary.append({'scenario':scenario['name'],'method':method,'independent_synthetic_seeds':len(rows),'ACC':float(np.mean([r['ACC'] for r in rows])),'NMI':float(np.mean([r['NMI'] for r in rows])),'MSE':float(np.mean([r['MSE'] for r in rows])),'qualified_seeds':sum(bool(r['qualified']) for r in rows)})
    dump(OUT/'summary.json',summary);dump(OUT/'resource_usage.json',{'cpu_seconds':sum(j['cpu_seconds'] for j in jobs),'jobs':len(jobs),'independent_seed_unit':True,'gpu_hours':0})
if __name__=='__main__':main()
