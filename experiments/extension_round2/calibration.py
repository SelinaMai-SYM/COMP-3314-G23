"""Label-blind interval bracketing on a fixed convex movement path."""
from __future__ import annotations
import time
import numpy as np
from scipy import linalg
from method_extension.extension_round2.models import QuadraticProblem,solve,norms
from .common import *


class MovementPath:
    def __init__(self,H,W,method,parameters,store,key,budget,context):
        self.H=H;self.W=W;self.method=method;self.parameters=parameters;self.store=store;self.key=key;self.budget=budget;self.context=context;self.start=time.process_time()
        self.path=store.root/'paths'/f'{key}.json';self.state=load_record(self.path) or {'distinct':[],'attempts':{},'fits':{},'targets':{}}
        self.scale=float(linalg.norm(H-H.mean(axis=0)));base=QuadraticProblem(H,W,0.,method,**parameters);d=base.B@H;r=norms(d);directions=np.divide(d,r[:,None],out=np.zeros_like(d),where=r[:,None]>0);force=float(linalg.norm(base.B.T@(base.w[:,None]*directions)));self.tv=float(base.w@r)
        self.lambda0=.02*self.scale/force if force>0 and self.scale>0 else None

    def remaining(self):return max(0.,self.budget-(time.process_time()-self.start)-20.)
    def save(self):atomic_json(self.path,self.state)
    def result(self,ref):return get_arrays(self.store,self.store.get(ref))
    def fitted(self,lam,rho):
        token=float(lam).hex();old=self.state['fits'].get(token);previous=self.result(old) if old else None
        if self.certified(previous,rho):return previous,old
        if token not in self.state['distinct']:
            if len(self.state['distinct'])>=32:return None,None
            self.state['distinct'].append(token)
        while self.remaining()>3:
            problem=QuadraticProblem(self.H,self.W,lam,self.method,**self.parameters);warm=previous['checkpoint'] if previous else None
            if warm is None and self.state['fits']:
                nearest=min(self.state['fits'],key=lambda k:abs(np.log(max(float.fromhex(k),1e-300)/max(lam,1e-300))));warm=self.result(self.state['fits'][nearest])['checkpoint']
            # Use the same-cohort QSSC path only as a label-blind computational
            # warm start. Its outputs never select variants by ACC/NMI.
            if warm is None and self.method=='E6':
                qpath=load_record(self.store.root/'paths'/f"{self.context['benchmark']}--QSSC--default.json")
                if qpath and qpath['fits']:
                    nearest=min(qpath['fits'],key=lambda k:abs(np.log(max(float.fromhex(k),1e-300)/max(lam,1e-300))));r=self.result(qpath['fits'][nearest]);warm={'Z':(r['G']-problem.mean)@problem.V,'q':r['q']@problem.V,'p':np.zeros((len(problem.w),len(problem.s))),'S':np.zeros((len(problem.s),len(problem.s)))}
            attempt=self.state['attempts'].get(token,0)+1;self.state['attempts'][token]=attempt;started=time.process_time();fitid=identity({**self.context,'method':self.method,'parameters':self.parameters,'lambda':lam,'attempt':attempt});folder=self.store.root/'fits'/fitid;folder.mkdir(parents=True,exist_ok=True)
            atomic_json(folder/'definition.json',{**self.context,'method':self.method,'parameters':self.parameters,'lambda':lam,'attempt':attempt})
            self.save()
            def checkpoint(value):
                save_continuation(folder/'continuation',{'state':value,'context':self.context,'lambda':lam,'parameters':self.parameters})
            result=solve(problem,rho=rho,cpu_limit=min(570.,self.remaining()-2),checkpoint=warm,callback=checkpoint);result.update(lam=lam,fit_id=fitid,attempt=attempt,method=self.method,parameters=self.parameters,context=self.context,fit_certification_rho=rho,fit_total_CPU_seconds=time.process_time()-started)
            ref=self.store.put(put_arrays(self.store,result));atomic_json(folder/'result.json',{'object':ref});self.state['fits'][token]=ref;self.save();previous=result
            if (folder/'continuation').exists():shutil.rmtree(folder/'continuation')
            if self.certified(result,rho) or result['stopping_reason'] in ['NUMERICAL_FAILURE','NUMERICAL_CONDITIONING'] or self.remaining()<5:return result,ref
        return (previous,self.state['fits'].get(token)) if previous else (None,None)

    @staticmethod
    def certified(result,rho):
        """A cached fit's certification belongs to the requested target."""
        return bool(result and result.get('valid_bound') and 0<=result['relative_gap']<=1e-6 and 0<=result['stable_relative_gap']<=1e-6 and result.get('movement_error') is not None and 0<=result['movement_error']<=.02*rho)

    @staticmethod
    def matched(result,rho):return MovementPath.certified(result,rho) and abs(result['movement']-rho)+result['movement_error']<=.05*rho

    def target(self,rho):
        key=str(rho)
        if key in self.state['targets']:return self.state['targets'][key]
        last=None;last_ref=None;reason='SEARCH_LIMIT';bracket_steps=0;refinements=0
        if self.scale==0 or self.tv==0 or self.lambda0 is None:
            result,ref=self.fitted(0.,rho);reason='TARGET_UNREACHABLE_DEGENERATE';last,last_ref=result,ref
        else:
            lam=self.lambda0
            while self.remaining()>4:
                known=[]
                for token,ref in self.state['fits'].items():
                    value=self.result(ref)
                    if self.matched(value,rho):last,last_ref=value,ref;reason='MATCHED';break
                    if value['valid_bound']:known.append((float.fromhex(token),value,ref))
                if reason=='MATCHED':break
                low=[v for v in known if v[1]['movement']+v[1]['movement_error']<rho];high=[v for v in known if v[1]['movement']-v[1]['movement_error']>rho]
                if low and high:
                    lo=max(low,key=lambda v:v[0]);hi=min(high,key=lambda v:v[0])
                    if lo[0]>=hi[0]:reason='NUMERICAL_NONMONOTONE_INTERVALS';break
                    if refinements>=6:break
                    lam=float(np.sqrt(lo[0]*hi[0]));refinements+=1
                elif known:
                    if bracket_steps>=8:break
                    if low:lam=max(v[0] for v in low)*2
                    elif high:lam=min(v[0] for v in high)*.5
                    else:
                        closest=min(known,key=lambda v:abs(v[1]['movement']-rho));lam=closest[0]
                    bracket_steps+=1
                value,ref=self.fitted(lam,rho)
                if value is None:break
                last,last_ref=value,ref
                if self.matched(value,rho):reason='MATCHED';break
                if not self.certified(value,rho):
                    reason=value['stopping_reason'] if value['stopping_reason'] in ['NUMERICAL_FAILURE','NUMERICAL_CONDITIONING'] else 'UNCERTIFIED';break
            if self.remaining()<=4 and reason!='MATCHED':reason='TIMEOUT'
        outcome={'status':reason,'rho':rho,'fit':last_ref,'fit_id':last.get('fit_id') if last else None,'lambda':last.get('lam') if last else None,'actual_movement':last.get('movement') if last else None,'movement_error':last.get('movement_error') if last else None,'matched':reason=='MATCHED','certified':self.certified(last,rho),'refinements':refinements,'bracketing_steps':bracket_steps,'distinct_lambda_count':len(self.state['distinct'])}
        self.state['targets'][key]=outcome;self.save();return outcome
