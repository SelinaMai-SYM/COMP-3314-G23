"""Resumable fixed-design orchestration, with promotion separate from fitting."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
import json
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
from experiments.submission_refresh.core import ResourceLedger,atomic_json,identity,ROOT
from method_extension.extension_verification.convex import rowunit,row_norm
from .inputs import load_locked
from .gates import radial_geometry,radial_gate,semantic_gate
from .statistics import transitions


class BudgetExhausted(RuntimeError):pass


class Campaign:
    def __init__(self,config,artifact_root):
        self.config=str(Path(config).resolve());self.spec,self.lock,self.store=load_locked(config,artifact_root);self.root=self.store.root;self.ledger=ResourceLedger(self.root)
        self.state_path=self.root/'campaign_state.json';self.state=json.loads(self.state_path.read_text()) if self.state_path.exists() else {'source_fingerprint':self.lock['source_fingerprint'],'stages':{},'gates':{},'point_ids':[]}
        if self.state['source_fingerprint']!=self.lock['source_fingerprint']:raise ValueError('campaign source context changed')
        self.start_cpu=time.process_time();self._bookkeeping()

    def _bookkeeping(self):
        state=self.ledger.state()
        if not any(e['run_id']=='controller-bookkeeping-0001' for e in state['entries']):
            if not self.ledger.reserve('controller-bookkeeping-0001',600,'aggregation'):raise BudgetExhausted('No controller allowance')
            self.ledger.finish('controller-bookkeeping-0001',None,'CONSERVATIVE_ACCOUNTING',note='600-second conservative bucket for controller transforms, gates, reporting setup and resume metadata; worker commands are metered separately')
        self.accounting=self.root/'controller_accounting.json'
        old=json.loads(self.accounting.read_text()) if self.accounting.exists() else {'CPU_seconds':0.}
        self.previous_controller_cpu=old['CPU_seconds']

    def save(self):
        atomic_json(self.state_path,self.state)
        actual=self.previous_controller_cpu+time.process_time()-self.start_cpu
        atomic_json(self.accounting,{'CPU_seconds':actual,'conservative_bucket_seconds':600,'excludes_already_charged_worker_children':True})
        if actual>580:raise BudgetExhausted('Controller accounting bucket requires an explicit new bounded allocation')

    def _command(self,run_id,argv,cpu_limit,phase):
        status=self.root/'command_jobs'/run_id/'status.json'
        if status.exists():
            value=json.loads(status.read_text())
            if value['status']=='COMPLETED':return value
            raise RuntimeError('A failed immutable command needs its recorded continuation identity: '+run_id)
        command=[sys.executable,'-m','experiments.extension_verification.resources','--artifact-root',str(self.root),'--run-id',run_id,'--cpu-limit',str(cpu_limit),'--wall-limit',str(2*cpu_limit+120),'--phase',phase,'--cwd',str(ROOT),'--',*argv]
        while True:
            result=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            if status.exists():
                record=json.loads(status.read_text())
                if record['status']=='COMPLETED':return record
                raise RuntimeError('Bounded worker failed: '+str(status.parent/'command.log'))
            state=self.ledger.state()
            if result.returncode and state['active']:time.sleep(.5);continue
            if result.returncode:raise BudgetExhausted('Shared allowance cannot reserve '+run_id)
            raise RuntimeError('Worker ended without a command receipt')

    def definition(self,benchmark,panel,method,kind,gamma,parameters=None,*,purpose='primary',primary=False):
        entry=self.lock['datasets'][benchmark];base={'benchmark':benchmark,'panel':panel,'kind':kind,'gamma':float(gamma),'parameters':parameters or {},'source_fingerprint':self.lock['source_fingerprint'],'protocol_sha256':self.lock['protocol_sha256'],'anchor_sha256':entry['objects']['F0' if panel=='original' else 'U']['sha256'],'W0_sha256':entry['objects']['W0']['sha256']}
        fit_id=identity(base);return {**base,'fit_id':fit_id,'point_id':identity({'fit_id':fit_id,'method':method}),'method':method,'purposes':[purpose],'primary':primary}

    def point_path(self,point_id):return self.root/'points'/f'{point_id}.json'

    def register(self,record):
        path=self.point_path(record['point_id'])
        if path.exists():
            old=json.loads(path.read_text());record['purposes']=sorted(set(old.get('purposes',[])+record.get('purposes',[])));record['primary']=bool(old.get('primary') or record.get('primary'))
        atomic_json(path,record)
        return record

    def fitted(self,definition):
        folder=self.root/'fits'/definition['fit_id'];latest=folder/'result.json';record=json.loads(latest.read_text()) if latest.exists() else None
        ceilings=list(zip([30000,60000,120000],[1800,3600,7200]))
        if not definition['primary']:ceilings=ceilings[:1]
        charged=0.;previous_checkpoint=None
        for stage,(iterations,cpu_ceiling) in enumerate(ceilings,1):
            run_id='fit-'+definition['fit_id']+'-'+str(stage);receipt=self.root/'command_jobs'/run_id/'status.json'
            if receipt.exists():
                status=json.loads(receipt.read_text());charged+=status['charged_CPU_seconds']
                result=folder/'attempts'/run_id/'result.json'
                if result.exists():record=json.loads(result.read_text());previous_checkpoint=record['checkpoint']
                elif status['status']!='COMPLETED':raise RuntimeError('Numerical worker failed before a saved feasible endpoint; inspect '+str(receipt.parent/'command.log'))
                if record is not None and record['solver']['certified']:break
                continue
            if record is not None:
                if record['source_fingerprint']!=definition['source_fingerprint']:raise ValueError('cached fit source differs')
                if record['solver']['certified']:break
                previous_checkpoint=record['checkpoint']
            allowance=cpu_ceiling-charged
            if allowance<30:break
            task={**definition,'attempt_id':run_id,'iteration_ceiling':iterations,'cumulative_cpu_ceiling':cpu_ceiling,'prior_charged_CPU_seconds':charged,'cpu_allowance':allowance,'checkpoint':previous_checkpoint}
            task_path=self.root/'fit_tasks'/f'{run_id}.json';atomic_json(task_path,task)
            status=self._command(run_id,[sys.executable,'-m','experiments.extension_verification.worker','--task',str(task_path),'--config',self.config,'--artifact-root',str(self.root)],allowance,definition['method'])
            charged+=status['charged_CPU_seconds'];record=json.loads(latest.read_text());record['cumulative_charged_fit_CPU_seconds']=charged;atomic_json(latest,record)
            previous_checkpoint=record['checkpoint']
            if record['solver']['certified']:break
        if record is None:raise RuntimeError('No finite fit output')
        for ref in record['objects'].values():self.store.get(ref)
        record.update(point_id=definition['point_id'],method=definition['method'],purposes=definition['purposes'],primary=definition['primary'],cumulative_charged_fit_CPU_seconds=charged)
        return self.register(record)

    def parallel(self,definitions):
        pending=iter(definitions);results=[]
        with ThreadPoolExecutor(max_workers=2) as pool:
            active={}
            for _ in range(2):
                value=next(pending,None)
                if value is not None:active[pool.submit(self.fitted,value)]=value
            while active:
                done,_=wait(active,return_when=FIRST_COMPLETED)
                for future in done:
                    definition=active.pop(future);record=future.result();results.append(record)
                    print('FIT',record['benchmark'],record['panel'],record['method'],record['gamma'],record['solver']['certified'],record['solver']['relative_gap'],flush=True)
                    value=next(pending,None)
                    if value is not None:active[pool.submit(self.fitted,value)]=value
        return results

    def transform(self,benchmark,panel,method,G,*,gamma=0.,parameters=None,purpose='primary_control',source_point=None,primary=False):
        entry=self.lock['datasets'][benchmark];G=np.asarray(G,dtype=float);Q=G.copy() if panel=='original' else rowunit(G);objects={'G':self.store.put(G),'Q':self.store.put(Q)}
        H=self.store.get(entry['objects']['F0' if panel=='original' else 'U']);movement=float(row_norm(G-H).sum()/max(float(row_norm(H).sum()),1e-12))
        base={'benchmark':benchmark,'panel':panel,'method':method,'kind':'deterministic_control','gamma':float(gamma),'parameters':parameters or {},'G_sha256':objects['G']['sha256'],'source_point':source_point,'source_fingerprint':self.lock['source_fingerprint'],'protocol_sha256':self.lock['protocol_sha256']};record={**base,'point_id':identity(base),'candidate_id':entry['candidate_id'],'n':entry['n'],'K':entry['K'],'role':entry['role'],'qualification':entry['qualification'],'objects':objects,'solver':{'status':'DETERMINISTIC_REFERENCE','certified':None,'numerically_active':movement>1e-6,'normalized_L21_movement':movement},'output_normalization':'none' if panel=='original' else 'rowunit','purposes':[purpose],'primary':primary,'labels_loaded_for_fitting':False}
        return self.register(record)

    def round(self,record):
        target=self.root/'evaluations'/f"{record['point_id']}.json"
        if target.exists():
            value=json.loads(target.read_text())
            if value['Q_object']!=record['objects']['Q']:raise ValueError('a changed saved Q requires a new qualified point identity')
            return value
        status=self._command('round-'+record['point_id'],[sys.executable,'-m','experiments.extension_verification.evaluation','--record',str(self.point_path(record['point_id'])),'--config',self.config,'--artifact-root',str(self.root)],600,record['method'])
        return json.loads(target.read_text())

    def gamma(self,benchmark,panel,factor=2.):
        reference=self.lock['datasets'][benchmark]['gamma_references'][panel]['gamma_ref'];return factor*reference if reference is not None else 1.

    def ordinary(self,b,p,*,gamma=None,purpose='primary',primary=True):return self.definition(b,p,'SSC','ssc',self.gamma(b,p) if gamma is None else gamma,purpose=purpose,primary=primary)
    def relative(self,b,p,*,gamma=None,eta=.25,purpose='primary',primary=True):return self.definition(b,p,'E1','relative',self.gamma(b,p) if gamma is None else gamma,{'eta':eta},purpose=purpose,primary=primary)

    def e1(self):
        if self.state['stages'].get('E1')=='COMPLETED':return
        for benchmark in self.spec['inputs']['dataset_order']:
            definitions=[item for panel in ['original','angular'] for item in [self.ordinary(benchmark,panel),self.relative(benchmark,panel)]];records=self.parallel(definitions)
            for panel in ['original','angular']:
                H=self.store.get(self.lock['datasets'][benchmark]['objects']['F0' if panel=='original' else 'U']);self.round(self.transform(benchmark,panel,'SC',H,purpose='primary',primary=True))
            for record in records:self.round(record)
            self.state['stages']['E1_'+benchmark]='COMPLETED';self.save()
        self.state['stages']['E1']='COMPLETED';self.save()

    def require(self,name):
        if self.state['stages'].get(name)!='COMPLETED':raise ValueError('Complete prerequisite stage '+name+' before selecting this phase')

    def e2_gate(self):
        self.require('E1')
        if self.state['stages'].get('E2_gate')=='COMPLETED':return
        outcomes={}
        for benchmark in ['ORL','YaleB']:
            entry=self.lock['datasets'][benchmark];selected=None;attempts=[]
            if entry['gamma_references']['angular']['gamma_ref'] is not None:
                for factor in [2,8,32]:
                    definition=self.ordinary(benchmark,'angular',gamma=self.gamma(benchmark,'angular',factor),purpose='E2_gate_reference',primary=factor==2);record=self.fitted(definition);attempts.append({'point_id':record['point_id'],'factor':factor,'certified':record['solver']['certified'],'active':record['solver']['numerically_active']})
                    if record['solver']['certified'] and record['solver']['numerically_active']:selected=record;break
            if selected is None:
                outcomes[benchmark]={'passed':False,'decision':'NOT_EVALUABLE_INACTIVE_OR_UNCERTIFIED','attempts':attempts};continue
            U=self.store.get(entry['objects']['U']);G=self.store.get(selected['objects']['G']);R,geometry,arrays=radial_geometry(U,G)
            neutral=self.transform(benchmark,'angular','radial_neutralization',R,gamma=selected['gamma'],purpose='E2_gate_diagnostic',source_point=selected['point_id'])
            geometry_refs={name:self.store.put(value) for name,value in arrays.items()};ordinary_trials=self.round(selected);neutral_trials=self.round(neutral);gate=radial_gate(selected['solver'],geometry,ordinary_trials['trials'],neutral_trials['trials'])
            labels=self.store.get(entry['objects']['labels']);ids=self.store.get(entry['objects']['original_ids']);gate.update(selected_reference=selected['point_id'],neutralization_point=neutral['point_id'],attempts=attempts,geometry_objects=geometry_refs,correctness_transitions=transitions(labels,self.store.get(ordinary_trials['predictions']),self.store.get(neutral_trials['predictions']),ids))
            sc=self.transform(benchmark,'angular','SC',U,purpose='primary',primary=True);sc_trials=self.round(sc)
            gate['SC_to_SSC_correctness_transitions']=transitions(labels,self.store.get(sc_trials['predictions']),self.store.get(ordinary_trials['predictions']),ids)
            outcomes[benchmark]=gate
        result={'method':'E2','development_outcomes':outcomes,'promoted':any(row['passed'] for row in outcomes.values()),'both_development_outcomes_retained':True,'protocol_sha256':self.lock['protocol_sha256']};atomic_json(self.root/'gates/E2.json',result);self.state['gates']['E2']=result;self.state['stages']['E2_gate']='COMPLETED';self.save()

    def e2(self):
        self.require('E2_gate')
        if self.state['stages'].get('E2')=='COMPLETED':return
        if self.state['gates']['E2']['promoted']:
            definitions=[]
            for b in self.spec['inputs']['dataset_order']:
                for method,kind in [('E2','tangent'),('isotropic','ball')]:definitions.append(self.definition(b,'angular',method,kind,self.gamma(b,'angular'),{'angle_degrees':15.},purpose='primary' if method=='E2' else 'primary_control',primary=True))
            for record in self.parallel(definitions):self.round(record)
        self.state['stages']['E2']='COMPLETED';self.save()

    def e3_gate(self):
        self.require('E2')
        if self.state['stages'].get('E3_gate')=='COMPLETED':return
        outcomes={}
        for b in ['ORL','YaleB']:
            entry=self.lock['datasets'][b];triplets=self.store.get(entry['objects']['triplets']);labels=self.store.get(entry['objects']['labels']);gate=semantic_gate(triplets,labels);gate.update(triplets_object=entry['objects']['triplets'],construction_diagnostics=entry['label_free_diagnostics']);outcomes[b]=gate
        result={'method':'E3','development_outcomes':outcomes,'promoted':any(row['passed'] for row in outcomes.values()),'triplets_frozen_before_label_audit':True,'protocol_sha256':self.lock['protocol_sha256']};atomic_json(self.root/'gates/E3.json',result);self.state['gates']['E3']=result;self.state['stages']['E3_gate']='COMPLETED';self.save()

    def e3(self):
        self.require('E3_gate')
        if self.state['stages'].get('E3')=='COMPLETED':return
        if self.state['gates']['E3']['promoted']:
            definitions=[]
            for b in self.spec['inputs']['dataset_order']:
                definitions.append(self.definition(b,'angular','E3','relative_neighbor',self.gamma(b,'angular'),{'mu':2.},purpose='primary',primary=True))
                definitions.append(self.definition(b,'angular','triplet_only','relative_neighbor',0,{'mu':2.},purpose='primary_control',primary=True))
                for seed in [400,401,402]:definitions.append(self.definition(b,'angular','random_hinge_'+str(seed),'relative_neighbor',self.gamma(b,'angular'),{'mu':2.,'random_seed':seed},purpose='primary_control',primary=True))
            for record in self.parallel(definitions):self.round(record)
        self.state['stages']['E3']='COMPLETED';self.save()

    def controls(self):
        self.require('E3')
        if self.state['stages'].get('controls')=='COMPLETED':return
        for b in self.spec['inputs']['dataset_order']:
            for panel in ['original','angular']:
                ordinary=self.fitted(self.ordinary(b,panel));relative=self.fitted(self.relative(b,panel));entry=self.lock['datasets'][b];H=self.store.get(entry['objects']['F0' if panel=='original' else 'U']);base=self.store.get(ordinary['objects']['G'])
                self.round(self.transform(b,panel,'interpolation',.25*H+.75*base,gamma=ordinary['gamma'],parameters={'eta':.25},source_point=ordinary['point_id']))
                self.round(self.transform(b,panel,'uniform_scaling',.25*H,parameters={'eta':.25}))
                reference=entry['gamma_references'][panel]['gamma_ref']
                if reference is not None and ordinary['solver']['certified'] and relative['solver']['certified'] and not ordinary['solver']['numerically_active'] and not relative['solver']['numerically_active']:
                    for factor in [8,32]:
                        a=self.fitted(self.ordinary(b,panel,gamma=factor*reference,purpose='activity_probe',primary=False));z=self.fitted(self.relative(b,panel,gamma=factor*reference,purpose='activity_probe',primary=False));self.round(a);self.round(z)
                        if not (a['solver']['certified'] and z['solver']['certified'] and not a['solver']['numerically_active'] and not z['solver']['numerically_active']):break
        for b in ['ORL','YaleB']:
            for panel in ['original','angular']:
                ref=self.lock['datasets'][b]['gamma_references'][panel]['gamma_ref'];values=[factor*ref for factor in [0,.5,1,2,8]] if ref is not None else []
                values+= [1.]
                for gamma in dict.fromkeys(values):
                    for definition in [self.ordinary(b,panel,gamma=gamma,purpose='development_path',primary=gamma==self.gamma(b,panel)),self.relative(b,panel,gamma=gamma,purpose='development_path',primary=gamma==self.gamma(b,panel))]:self.round(self.fitted(definition))
                eta=self.fitted(self.relative(b,panel,eta=.5,purpose='development_eta_sensitivity',primary=False));self.round(eta)
                ordinary=self.fitted(self.ordinary(b,panel));H=self.store.get(self.lock['datasets'][b]['objects']['F0' if panel=='original' else 'U']);self.round(self.transform(b,panel,'interpolation',.5*H+.5*self.store.get(ordinary['objects']['G']),gamma=ordinary['gamma'],parameters={'eta':.5},purpose='development_eta_control',source_point=ordinary['point_id']))
        if self.state['gates']['E2']['promoted']:
            for b in self.spec['inputs']['dataset_order']:
                reference=self.lock['datasets'][b]['gamma_references']['angular']['gamma_tan_ref']
                if reference is not None:
                    for factor in [2,8]:
                        gamma=factor*reference;records=[]
                        for method,kind in [('E2','tangent'),('isotropic','ball'),('SSC','ssc')]:
                            parameters={'angle_degrees':15.} if kind!='ssc' else {};row=self.fitted(self.definition(b,'angular',method,kind,gamma,parameters,purpose='projected_force_secondary',primary=False));self.round(row);records.append(row)
                        tangent=records[0]
                        if not (tangent['solver']['certified'] and not tangent['solver']['numerically_active']):break
            for b in ['ORL','YaleB']:
                for method,kind in [('E2','tangent'),('isotropic','ball')]:self.round(self.fitted(self.definition(b,'angular',method,kind,self.gamma(b,'angular'),{'angle_degrees':30.},purpose='development_angle_sensitivity',primary=False)))
        if self.state['gates']['E3']['promoted']:
            for b in ['ORL','YaleB']:self.round(self.fitted(self.definition(b,'angular','E3','relative_neighbor',self.gamma(b,'angular'),{'mu':.5},purpose='development_mu_sensitivity',primary=False)))
        self.state['stages']['controls']='COMPLETED';self.save()


def run(config,artifact_root,phase='all'):
    campaign=Campaign(config,artifact_root)
    verification=campaign.root/'verification.json'
    if not verification.is_file() or not json.loads(verification.read_text()).get('passed') or json.loads(verification.read_text())['source_fingerprint']!=campaign.lock['source_fingerprint']:raise ValueError('Run the fixed small-objective verification before benchmark fitting')
    methods={'e1':campaign.e1,'e2_gate':campaign.e2_gate,'e2':campaign.e2,'e3_gate':campaign.e3_gate,'e3':campaign.e3,'controls':campaign.controls}
    try:
        if phase=='all':
            for method in methods.values():method()
        else:methods[phase]()
        campaign.state['run_status']='COMPLETED'
    except BudgetExhausted as exc:campaign.state.update(run_status='STOPPED_SHARED_BUDGET',stop_reason=str(exc))
    except BaseException as exc:
        campaign.state.update(run_status='FAILED_REQUIRES_INVESTIGATION',stop_reason=repr(exc));campaign.save();raise
    campaign.save();return campaign.state
