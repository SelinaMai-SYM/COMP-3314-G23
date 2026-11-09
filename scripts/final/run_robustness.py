"""Corrected full SC/SSC pipeline under four fixed held-out image conditions."""
from pathlib import Path
import json,csv,time
import numpy as np
from scipy import sparse
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits
from SSC_method.spectral_embedding import spectral_embedding
from SSC_method.graph_construction import knn_affinity
from method_extension.next_round.certified_solver import solve
from method_extension.v3_theory.x2_stability_graph.weights import perturb_images,HELD_OUT_PERTURBATIONS
from experiments.next_round.campaign import CACHE,OUT,PRIMARY,dump
from experiments.next_round.evaluate import evaluate
from scripts.final.analyze_next_round import load

def main():
    start=time.process_time();results=[];old=load();folder=OUT/'full_pipeline_robustness';folder.mkdir(exist_ok=True)
    with threadpool_limits(limits=1):
        for dataset in PRIMARY:
            base=CACHE/(dataset+'__Y0');meta=json.loads((base/'meta.json').read_text());X=np.load(base/'X.npy');y=np.load(base/'y.npy');sc0=np.load(base/'sc_predictions.npy');ssc=next(j for j in old if j.get('status')=='COMPLETED' and j['task']['phase']=='A' and j['task']['dataset']==dataset and j['task']['gamma']==1.);sscpred=np.load(Path(__file__).resolve().parents[2]/ssc['array_path'])['predictions'];scmeta=json.loads((OUT/'sc'/(dataset+'__Y0.json')).read_text());domain=(-1.,1.) if dataset=='USPS' else (0.,1.)
            for index,(kind,brightness,contrast) in enumerate(HELD_OUT_PERTURBATIONS):
                path=folder/(dataset+'_'+str(index)+'.json')
                if path.exists():results.append(json.loads(path.read_text()));continue
                cpu=time.process_time();changed=perturb_images(X,brightness,contrast,domain=domain);F,_=spectral_embedding(changed,meta['K']);W,_=knn_affinity(F,k=5);fit=solve(F,W,1.,time_limit=600 if len(F)<=800 else 1800,warm_start_irls=True)
                record={'dataset':dataset,'condition_index':index,'kind':kind,'brightness_steps':brightness,'contrast':contrast,'domain':domain,'gamma':1.,'fixed_clean_parameters':True,'solver':{k:v for k,v in fit.items() if k not in ['G','q','history']},'endpoints':[],'scope':'four fixed deterministic image conditions; not independent random perturbation seeds or an X2 beta=1 evaluation'}
                for method,G,baseline,unperturbed in [('SC',F,scmeta['scores']['acc_mean'],sc0),('SSC',fit['G'],ssc['scores']['acc_mean'],sscpred)]:
                    trials,pred,_=evaluate(F,G,y,meta['K']);acc=float(np.mean([t['acc'] for t in trials])*100);nmi=float(np.mean([t['nmi'] for t in trials])*100);ari=float(np.mean([adjusted_rand_score(unperturbed[s],pred[s]) for s in range(50)]));record['endpoints'].append({'method':method,'ACC':acc,'NMI':nmi,'ACC_change_pp':acc-baseline,'partition_ARI_vs_same_clean_method_mean':ari,'trials':trials})
                record['cpu_seconds']=time.process_time()-cpu;dump(path,record);results.append(record);print('ROBUSTNESS',dataset,index,fit['status'],flush=True)
    rows=[]
    for r in results:
        for e in r['endpoints']:rows.append({k:v for k,v in e.items() if k!='trials'}|{k:r[k] for k in ['dataset','condition_index','brightness_steps','contrast','domain']}|{'SSC_solver_status':r['solver']['status'],'SSC_gap':r['solver']['gap']})
    with (OUT/'full_pipeline_robustness.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    dump(OUT/'robustness_resource_usage.json',{'cpu_seconds':sum(r['cpu_seconds'] for r in results),'endpoints':len(rows),'fixed_conditions':4,'inference_limit':'Conditions are descriptive; K-means seeds are conditional rounding variation, not independent image perturbations.'})
if __name__=='__main__':main()
