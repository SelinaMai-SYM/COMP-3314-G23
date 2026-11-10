"""Final confirmation predictions and seed namespace survive actual recovery."""
import json
import shutil
import numpy as np
from experiments.submission_refresh import aggregate,export_artifacts
from experiments.submission_refresh.core import ArtifactStore,atomic_json,identity


def test_registered_confirmation_recovers_without_the_original_store(tmp_path,monkeypatch):
    checkout=tmp_path/'fresh checkout';store=ArtifactStore(tmp_path/'original external store')
    first=1000000;seeds=list(range(first,first+50))
    inventory={'sources':[],'scope':'test fixture, no historical source inputs'}
    namespace={'version':2,'first':first,'count':50,'seeds':seeds,
        'winner_lock_sha256':'fixture-winner-lock','historical_inventory':inventory,
        'historical_inventory_sha256':identity(inventory),'overlap':False,'no_reselection':True,
        'historical_inventory_frozen_at_namespace_lock':True,
        'resume_rule':'reuse this exact block; own confirmation files never influence a new choice'}
    predictions=np.tile(np.array([0,0,1,1]),(50,1))
    sc_predictions=np.tile(np.array([0,1,1,0]),(50,1))
    record={'config_id':'fixture|locked-SSC','candidate_id':'fixture','endpoint':'mean_sample_sd_50',
        'status':'COMPLETED','first_seed':first,'namespace_sha256':identity(namespace),
        'winner_lock_sha256':namespace['winner_lock_sha256'],
        'trials':[{'seed':seed,'acc':.5,'nmi':.6} for seed in seeds],
        'objects':{'predictions':store.put(predictions),'matched_sc_predictions':store.put(sc_predictions)}}
    atomic_json(store.root/'confirmation/seed_namespace.json',namespace)
    atomic_json(store.root/'confirmation/confirm-fixture.json',record)
    records,extras=aggregate._register_scientific_tree(store,[])
    assert {item['record'] for item in records}=={'confirmation/seed_namespace.json','confirmation/confirm-fixture.json'}
    atomic_json(checkout/'results/submission_refresh/artifact_manifest.json',{'records':records,'extra_files':extras})
    monkeypatch.setattr(export_artifacts,'ROOT',checkout)
    archive=tmp_path/'confirmation.tar.gz';exported=export_artifacts.export(store.root,archive)
    assert exported['verified'] is True
    shutil.rmtree(store.root)  # The archive is now the only available object source.
    recovered=tmp_path/'independent recovered store';export_artifacts.recover(archive,recovered)
    actual=json.loads((recovered/'confirmation/confirm-fixture.json').read_text())
    recovered_namespace=json.loads((recovered/'confirmation/seed_namespace.json').read_text())
    assert actual==record and recovered_namespace==namespace
    assert actual['namespace_sha256']==identity(recovered_namespace)
    assert [row['seed'] for row in actual['trials']]==recovered_namespace['seeds']
    recovered_store=ArtifactStore(recovered)
    np.testing.assert_array_equal(recovered_store.get(actual['objects']['predictions']),predictions)
    np.testing.assert_array_equal(recovered_store.get(actual['objects']['matched_sc_predictions']),sc_predictions)
    proof=json.loads((recovered/'RECOVERED_EXPORT.json').read_text())
    assert proof['archive_sha256']==exported['sha256']
