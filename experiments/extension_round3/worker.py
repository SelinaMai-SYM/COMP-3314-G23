"""Single label-free task; all heavy workers run under the shared native guard."""
from __future__ import annotations
import argparse
from .common import *
from .calibration import parameters,calibrate
from method_extension.extension_round3.evidence import edge_deletion_evidence
from method_extension.extension_round3.convex import FusionProblem,matched,eligible


def evidence_task(root,config,benchmark,tau_multiplier):
    assert_fitting_open(root);spec,lock,store=locked(root,config);c=lock['cohorts'][benchmark];key=f'{benchmark}__t{tau_multiplier:g}';p=store.root/'evidence'/(key+'.json')
    if p.exists():return
    H=store.get(c['objects']['H']);W=store.get(c['objects']['W0']);folder=store.root/'evidence_checkpoints'/key;checkpoint=recover_continuation(folder) if (folder/'CURRENT.json').exists() else None
    def callback(state):
        if state['completed']%256==0 or state['completed']==len(H):save_continuation(folder,state)
    result=edge_deletion_evidence(H,W,tau_multiplier=tau_multiplier,cpu_limit=3500.,checkpoint=checkpoint,callback=callback)
    refs=put_arrays(store,result);atomic_json(p,dict(benchmark=benchmark,tau_multiplier=tau_multiplier,result=refs,source_fingerprint=lock['source_fingerprint'],H_sha256=c['objects']['H']['sha256'],W_sha256=c['objects']['W0']['sha256'],labels_loaded=False));print('EVIDENCE_COMPLETE',key,flush=True)


def prior_record(source,benchmark,method,rho=None):
    records=[read(p) for p in (source.root/'endpoints').glob('*.json')]
    rows=[r for r in records if r['benchmark']==benchmark and r['method']==method and (rho is None or r['rho']==rho) and r.get('result')]
    if len(rows)!=1:return None
    return rows[0]


def verified_prior(source,store,c,record):
    if record['H_sha256']!=c['objects']['H']['sha256'] or record['W_sha256']!=c['objects']['W0']['sha256']:raise ValueError('reference input identity differs')
    result=get_arrays(source,source.get(record['result']))
    # get_arrays accepts recursive references, including the top-level JSON.
    for ref in collect_refs(record['result']):link_ref(source,store,ref)
    return result


def reference_task(root,config,profile,input_root):
    spec,lock,store=locked(root,config);c=lock['cohorts'][profile['benchmark']];H=store.get(c['objects']['H']);W=store.get(c['objects']['W0']);method=profile['method'];source=ArtifactStore(input_root)
    record=dict(profile,source_fingerprint=lock['source_fingerprint'],labels_loaded=False)
    if method=='SC':
        result={'G':H};record.update(status='EXACT_SC',qualified=True,certified=True)
    elif method=='UNIFORM_GRAPH_ALIAS':
        qid=f"{profile['benchmark']}__QSSC__r0.10__t1";qp=profile_path(store,qid)
        if not qp.exists():record.update(status='UNRUN_QSSC_MISSING',qualified=False,certified=False);result=None
        else:
            qrec=read(qp)
            if not qrec.get('result'):record.update(status='UNRUN_QSSC_MISSING',qualified=False,certified=False);result=None
            else:
                result=get_arrays(store,qrec['result']);lam=qrec['lambda']/.9;P=FusionProblem(H,W,lam,weights=.9*FusionProblem(H,W,1).w);cert=P.certificate(result['G'],result['q'],result.get('p'))
                result={**result,**cert};record.update(status='QUALIFIED_MATCHED' if matched(cert,.1) else 'ALIAS_UNQUALIFIED',qualified=matched(cert,.1),certified=eligible(cert,.1),lambda_value=lam,alias_of=qid,certificate=scalar(cert))
    else:
        prior=prior_record(source,profile['benchmark'],'historical' if method=='HISTORICAL_IRLS' else 'SSC_reference')
        if prior is None:record.update(status='MISSING_REFERENCE',qualified=False,certified=False);result=None
        else:
            result=verified_prior(source,store,c,prior);record['prior_endpoint_sha256']=identity(prior)
            if method=='HISTORICAL_IRLS':record.update(status='HISTORICAL_FINITE_IRLS',qualified=False,certified=False)
            else:
                from method_extension.extension_verification.convex import Problem
                P=Problem(H,W,c['gamma_effective'],kind='ssc');dual=P.dual(result['q'],result.get('p'));primal=P.primal(result['G']);signed=primal-dual['dual'];relative=signed/max(1.,abs(primal),abs(dual['dual']));capacity=max(v for k,v in dual.items() if k.endswith('violation'))
                certified=bool(signed>=0 and relative<=1e-5 and capacity<=1e-8)
                record.update(status='REFERENCE_CERTIFIED' if certified else 'REFERENCE_UNCERTIFIED',qualified=certified,certified=certified,certificate={'primal':primal,'dual':dual['dual'],'signed_gap':signed,'relative_gap':relative,'capacity_residual':capacity,'movement':float(np.linalg.norm(result['G']-H)/max(np.linalg.norm(H-H.mean(axis=0)),1e-300))})
                result.update(q=dual['q'],p=dual['p'])
    if result is not None:record['result']=put_arrays(store,result)
    atomic_json(profile_path(store,profile['id']),record);print('REFERENCE',profile['benchmark'],method,record['status'],flush=True)


def fit_task(root,config,profile,input_root):
    assert_fitting_open(root);spec,lock,store=locked(root,config);output=profile_path(store,profile['id'])
    if output.exists():return
    if profile['method'] in ['SC','SSC_REFERENCE','HISTORICAL_IRLS','UNIFORM_GRAPH_ALIAS']:return reference_task(root,config,profile,input_root)
    c=lock['cohorts'][profile['benchmark']];H=store.get(c['objects']['H']);W=store.get(c['objects']['W0']);ep=store.root/'evidence'/f"{profile['benchmark']}__t{profile['tau_multiplier']:g}.json"
    if not ep.exists():
        atomic_json(output,dict(profile,status='UNRUN_EVIDENCE_UNAVAILABLE',qualified=False,certified=False));return
    evidence=get_arrays(store,read(ep)['result']);method=registry()[profile['method']];kw,meta=parameters(H,W,evidence,method)
    key=f"{profile['benchmark']}__{profile['method']}__t{profile['tau_multiplier']:g}";folder=store.root/'paths'/key
    warm=None
    if not (folder/'path.json').exists():
        source=ArtifactStore(input_root);old_method={'quadratic':'QSSC','graph':'QSSC','tube':'E1_v2','guard':'E5'}[method['family']]
        prior=prior_record(source,profile['benchmark'],old_method,.1)
        if prior:
            old=verified_prior(source,store,c,prior)
            if old.get('q') is not None:warm={'Z':old['G'],'q':old['q'],'p':old.get('p',np.zeros_like(old['q'])),'bar':old['G'],'same_lambda':False}
    point,outcome=calibrate(H,W,kw,profile['rho'],folder,cpu_limit=1740.,warm=warm)
    record=dict(profile,**outcome,source_fingerprint=lock['source_fingerprint'],labels_loaded=False,evidence_sha256=digest(ep),parameters=put_arrays(store,kw),intervention_metadata=put_arrays(store,meta))
    if point:record.update(result=point['result'],certificate=point['certificate'],lambda_value=point['lambda'],**{'lambda':point['lambda']})
    atomic_json(output,record);print('PROFILE',profile['id'],record['status'],flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('task',choices=['evidence','fit']);p.add_argument('--config',default=str(CONFIG));p.add_argument('--artifact-root',required=True);p.add_argument('--input-artifact-root',required=True);p.add_argument('--benchmark');p.add_argument('--tau-multiplier',type=float,default=1.);p.add_argument('--profile-id');a=p.parse_args()
    if a.task=='evidence':evidence_task(a.artifact_root,a.config,a.benchmark,a.tau_multiplier)
    else:fit_task(a.artifact_root,a.config,next(r for r in queue() if r['id']==a.profile_id),a.input_artifact_root)
if __name__=='__main__':main()
