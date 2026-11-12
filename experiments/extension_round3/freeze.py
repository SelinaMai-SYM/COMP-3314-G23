"""Byte-verify and retain exact round-two inputs without loading label arrays."""
from .common import *
from .rounding import anchor_indices


def freeze(config,data_root,artifact_root,input_artifact_root):
    store=ArtifactStore(artifact_root);expected=read(ROOT/'configs/extension_round3/cohort_lock.json');source=ArtifactStore(input_artifact_root)
    if digest(ROOT/'configs/extension_round2/cohort_lock.json')!=expected['round2_lock_sha256']:raise ValueError('round-two lock changed')
    if (store.root/'cohort_lock.json').exists():return locked(artifact_root,config)[1]
    assert_fitting_open(artifact_root);cohorts={}
    for name in ORDER:
        row=expected['cohorts'][name]
        for f in row['source_files']:
            p=Path(data_root)/f['path_relative_to_data_root']
            if digest(p)!=f['sha256']:raise ValueError('raw provider byte hash differs: '+name)
        for ref in row['objects'].values():link_ref(source,store,ref)
        H=store.get(row['objects']['H']);W=store.get(row['objects']['W0']);ids=store.get(row['objects']['original_ids'])
        if H.shape!=(row['n'],row['K']) or W.shape!=(row['n'],row['n']) or len(ids)!=row['n']:raise ValueError('locked dimensions differ')
        initial=store.put(anchor_indices(H,row['K']));cohorts[name]={**row,'anchor_initial_indices':initial};print('INPUT_VERIFIED',name,flush=True)
    files=numerical_files();lock=dict(schema='ssc-round3-runtime-lock-v1',base_commit=expected['base_commit'],registration_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),protocol_sha256=digest(config),input_lock_sha256=digest(ROOT/'configs/extension_round3/cohort_lock.json'),registry_sha256=digest(ROOT/'configs/extension_round3/method_registry.json'),queue_sha256=digest(ROOT/'configs/extension_round3/experiment_queue.json'),source_files=files,environment=environment(),source_fingerprint=identity({'files':files,'environment':environment()}),source_snapshot=store.put({n:(ROOT/n).read_text() for n in files}),cohorts=cohorts,selection_qualification=expected['selection_qualification'],labels_loaded=False)
    atomic_json(store.root/'cohort_lock.json',lock);return lock
