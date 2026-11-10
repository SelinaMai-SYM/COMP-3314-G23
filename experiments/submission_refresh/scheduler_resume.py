"""Validate graph/EnSC scheduler skips without invoking scientific builders.

The scheduler's saved controller record is terminal evidence, not permission to
ignore changed inputs, source behavior, task allocations or G4 authorization.
"""
from __future__ import annotations
import json
from pathlib import Path
import resource
import time
import numpy as np
from experiments.v3_reproduction.provenance import fingerprint_matrix
from .core import ArtifactStore,digest,identity

SCHEMA='scheduler-fixed-input-resume-v1'


def _input_path(root,value,dataset,kind):
    if not isinstance(value,str) or not value:raise ValueError('saved fixed input record is unavailable')
    candidate=Path(value);candidate=candidate if candidate.is_absolute() else root/candidate
    if candidate.is_symlink():raise ValueError('saved fixed input record must not be a symlink')
    path=candidate.resolve()
    if root not in path.parents:raise ValueError('saved fixed input record is outside its artifact root')
    parts=path.relative_to(root).parts
    allowed={'graph_inputs'} if kind=='graph' else {'graph_inputs','ensc_inputs'}
    if len(parts)!=4 or parts[0] not in allowed or parts[1]!=dataset or parts[-1]!='representation.json':
        raise ValueError('saved fixed input path does not match its task dataset/kind')
    if not path.is_file():raise ValueError('saved fixed input record is missing')
    return path


def _source_identity(source):
    if not isinstance(source,dict) or not source.get('implementation_hash') or not isinstance(source.get('environment'),dict):
        raise ValueError('saved scientific source/environment is unavailable')
    return {'implementation_hash':source['implementation_hash'],'environment':source['environment']}


def _authorization_identity(value):
    keys=['gate_sha256','backend_validation_sha256','source_revision']
    if not isinstance(value,dict) or any(not value.get(key) for key in keys):
        raise ValueError('saved EnSC authorization identity is unavailable')
    return {key:value[key] for key in keys}


def capture_execution(task,result,artifact_root):
    """Attach immutable metadata identity to a returned controller record.

    A failure before source/input availability stays a genuine failed attempt,
    with an explicit unavailable identity. It cannot later be silently skipped.
    This function reads metadata only and never computes or replaces arrays.
    """
    base={'schema':SCHEMA,'task_sha256':identity(task),'available':False}
    try:
        if task['kind'] not in ['graph','ensc']:raise ValueError('unsupported fixed-input task kind')
        authorization=_authorization_identity(result.get('authorization')) if task['kind']=='ensc' else None
        root=Path(artifact_root).resolve();path=_input_path(root,result.get('input_record'),task['dataset'],task['kind'])
        source=_source_identity(result.get('source'))
        return {**base,'available':True,'source':source,'authorization':authorization,
            'input_record':str(path.relative_to(root)),'input_record_sha256':digest(path),
            'profile':bool(task.get('profile',False))}
    except (KeyError,TypeError,ValueError,OSError) as exc:
        return {**base,'unavailable_reason':str(exc)}


class ResumeValidator:
    """Reuse one current data/source snapshot per dataset in this controller.

    Only X/y are decoded to compare the current loader output with the saved
    input. Every fixed object is verified by content hash, without graph,
    spectral, coefficient, solver or rounding calls. The data root must remain
    frozen throughout this scheduler invocation, as during scientific fitting.
    """
    def __init__(self,data_root,artifact_root):
        self.data_root=Path(data_root).resolve();self.root=Path(artifact_root).resolve()
        self.sources={};self.data={};self.inputs={};self.verified_objects={}
        self.cpu_seconds=0.;self.child_cpu_seconds=0.;self.validated=0

    def _sources(self,kind):
        if kind not in self.sources:
            if kind=='graph':
                from .graph_repair import scientific_source_record
                shared=scientific_source_record();source=shared
            else:
                from . import ensc_campaign as ensc
                source=ensc._construction_source();shared=ensc.scientific_source_record()
            self.sources[kind]=(source,shared)
        return self.sources[kind]

    def _current_data(self,dataset):
        if dataset not in self.data:
            from .baselines import load
            X,y,_=load(dataset,self.data_root)
            self.data[dataset]=fingerprint_matrix(np.asarray(X,dtype=float),np.asarray(y))
        return self.data[dataset]

    def _verify_objects(self,objects):
        from .export_artifacts import _object_reference
        for ref in objects.values():
            relative=_object_reference(ref);path=(self.root/relative).resolve()
            if self.root not in path.parents or not path.is_file():raise ValueError('saved fixed input object is unavailable')
            stat=path.stat();key=(relative,ref['sha256']);stamp=(stat.st_size,stat.st_mtime_ns,stat.st_ino)
            if self.verified_objects.get(key)==stamp:continue
            if (ref.get('bytes') is not None and stat.st_size!=ref['bytes']) or digest(path)!=ref['sha256']:
                raise ValueError('saved fixed input object hash mismatch')
            self.verified_objects[key]=stamp

    def validate(self,task,saved):
        start=time.process_time();children=resource.getrusage(resource.RUSAGE_CHILDREN)
        try:return self._validate(task,saved)
        except Exception as exc:
            raise ValueError('Existing '+str(task.get('kind'))+' task cannot be reused: '+str(exc)+
                '; preserve the original evidence and use a new run ID') from exc
        finally:
            after=resource.getrusage(resource.RUSAGE_CHILDREN)
            self.cpu_seconds+=time.process_time()-start
            self.child_cpu_seconds+=max(0.,after.ru_utime+after.ru_stime-children.ru_utime-children.ru_stime)

    def _validate(self,task,saved):
        kind=task['kind'];dataset=task['dataset'];locked=saved.get('scheduler_resume_identity',{})
        if kind not in ['graph','ensc']:raise ValueError('unsupported fixed-input task kind')
        if identity(saved.get('task'))!=identity(task) or locked.get('task_sha256')!=identity(task):
            raise ValueError('task parameters or CPU/fit allocations changed')
        if locked.get('schema')!=SCHEMA or locked.get('available') is not True:
            raise ValueError('locked source/input metadata identity is unavailable')
        status=saved.get('status');profile=bool(task.get('profile',False))
        if status not in ['COMPLETED','PROFILE_ONLY_INELIGIBLE','FAILED','TIMEOUT','INTERRUPTED','KILLED_OR_CRASHED']:
            raise ValueError('saved controller record is not terminal')
        if locked.get('profile')!=profile or (status=='PROFILE_ONLY_INELIGIBLE' and not profile) or (status=='COMPLETED' and profile):
            raise ValueError('saved profile/formal execution status differs')
        # Authorization precedes all EnSC input-file and object-store access.
        if kind=='ensc':
            from . import ensc_campaign as ensc
            authorization=_authorization_identity(ensc._authorization(task))
            if authorization!=locked.get('authorization') or authorization!=_authorization_identity(saved.get('authorization')):
                raise ValueError('current G3 gate/backend authorization differs from the saved execution')
        current,shared=self._sources(kind);current_id=_source_identity(current)
        if current_id!=locked.get('source') or current_id!=_source_identity(saved.get('source')):
            raise ValueError('current scientific source/helper behavior or environment differs')
        path=_input_path(self.root,locked.get('input_record'),dataset,kind)
        if path!=_input_path(self.root,saved.get('input_record'),dataset,kind) or digest(path)!=locked.get('input_record_sha256'):
            raise ValueError('saved fixed input metadata changed')
        metadata=json.loads(path.read_text());objects=metadata.get('objects',{})
        from .ensc_campaign import K_VALUES
        if metadata.get('dataset')!=dataset or metadata.get('input_preparation')!='Y0' or metadata.get('K')!=K_VALUES[dataset]:
            raise ValueError('fixed input membership/preparation/K differs')
        if _source_identity(metadata.get('source'))!=_source_identity(shared):
            raise ValueError('fixed input scientific source/environment differs')
        if not {'X','y','F0','U','A','W0','Wa_raw'}<=objects.keys():raise ValueError('fixed input objects are incomplete')
        self._verify_objects(objects)
        if not (self.root/'objects').is_dir():raise ValueError('saved object store is unavailable')
        store=ArtifactStore(self.root)
        input_key=(str(path),locked['input_record_sha256'])
        if input_key not in self.inputs:
            self.inputs[input_key]=fingerprint_matrix(store.get(objects['X']),store.get(objects['y']))
        if self.inputs[input_key]!=self._current_data(dataset):raise ValueError('current source data/row order differs from saved X/y')
        if kind=='ensc':
            behavior=ensc._adapter_behavior('input')
            if path.relative_to(self.root).parts[0]=='graph_inputs':
                ensc._g3_input_compatibility(metadata,store,behavior)
            elif metadata.get('ensc_input_adapter_fingerprint')!=behavior['fingerprint']:
                raise ValueError('saved EnSC input-loader/helper fingerprint differs')
        self.validated+=1
        return {'validated':True,'kind':kind,'dataset':dataset,'input_record':locked['input_record'],
            'input_record_sha256':locked['input_record_sha256'],'source':current_id,
            'current_data_fingerprint':self.data[dataset],'fit_or_builder_called':False}
