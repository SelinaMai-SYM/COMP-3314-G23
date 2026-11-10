"""No-data current release replay and fail-before-write integrity checks."""
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil

import pytest
import yaml
from experiments.submission_refresh import current_release as release
from experiments.submission_refresh.core import digest
from experiments.submission_refresh.selection import summarize,distances,rank


def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


@pytest.fixture
def scalar_fixture(tmp_path,monkeypatch):
    root=tmp_path/'checkout with spaces';root.mkdir()
    output=root/'results/subset_search';output.mkdir(parents=True)
    configs=root/'configs/subset_search';configs.mkdir(parents=True)
    (configs/'protocol.yaml').write_text('version: fixed\n')
    selection=root/'configs/submission_refresh/selection.yaml';selection.parent.mkdir(parents=True);selection.write_text('version: joint\n')
    paper={'acc':{'ssc':{'ORL':{'mean':50.,'sd':1.}}},'nmi':{'ssc':{'ORL':{'mean':50.,'sd':2.}}}}
    pp=root/'configs/v3/paper_reference.yaml';pp.parent.mkdir(parents=True);pp.write_text(yaml.safe_dump(paper))
    rows=[];trials=[];candidates=[];source_root=tmp_path/'external scientific objects'
    for i,(cid,gamma,acc,nmi) in enumerate([('A',1.,.50,.10),('B',1000.,.55,.55)]):
        config_id=f'{cid}|E8|{gamma}|RANDOM'
        base={'candidate_id':cid,'config_id':config_id,'benchmark':'ORL','family':'fixed',
              'pool':'specification_compatible','n_samples':10,'n_classes':2,'prep':'Y0','variant':'E8',
              'gamma_nominal':gamma,'gamma_effective':gamma,'initialization':'RANDOM',
              'solver_status':'ITERATE_CONVERGED_UNCERTIFIED','endpoint':'mean_sample_sd_50',
              'paper_deviations':0,'preparation_assumptions':1,'alias_of':None,
              'record_directory':f'subset/{cid}','record_file':f'E8__{gamma:g}__RANDOM.json'}
        current=[{'seed':seed,'acc':acc,'nmi':nmi,'inertia':float(seed+1)} for seed in range(50)]
        stats=summarize(current)
        row=distances({**base,**{k:v for k,v in stats.items() if k!='native_best'}},{'acc':50.,'nmi':50.})
        row.update(paper_acc=50.,paper_nmi=50.,paper_acc_sd=1.,paper_nmi_sd=2.)
        rows.append(row)
        for t in current:trials.append({**{k:base[k] for k in ['candidate_id','config_id','variant','gamma_nominal','initialization']},**t})
        m=output/'sample_manifests'/f'{cid}.json';m.parent.mkdir(exist_ok=True);m.write_text(json.dumps({'candidate_id':cid,'selected_indices':list(range(10))}))
        candidates.append({'candidate_id':cid,'benchmark':'ORL','pool':'specification_compatible','n':10,'manifest_path':str(m.relative_to(root)),'manifest_sha256':digest(m)})
        source=source_root/f'subset/{cid}/source.json';source.parent.mkdir(parents=True)
        source.write_text(json.dumps({'source_commit':'frozen-source','implementation_hash':'behavior-hash','cache_identity':'cache','environment':{'python':'test'}}))
    # B has the smaller joint discrepancy; ACC-only would choose A.
    native=[]
    for row in rows:
        native.append({**row,**summarize([{'seed':s,'acc':row['acc_mean']/100,'nmi':row['nmi_mean']/100,'inertia':float(s+1)} for s in range(50)])['native_best'],'endpoint':'native_best_of_50','n':1})
    closest=[rank(rows)[0],rank(native)[0]]
    write_csv(output/'joint_search_summary.csv',rows);write_csv(output/'closest_matches.csv',closest)
    buffer=io.StringIO(newline='');writer=csv.DictWriter(buffer,fieldnames=list(trials[0]));writer.writeheader();writer.writerows(trials)
    (output/'trials.csv.gz').write_bytes(gzip.compress(buffer.getvalue().encode(),mtime=0))
    (output/'candidate_catalogue.json').write_text(json.dumps({'candidates':candidates}))
    monkeypatch.setattr(release,'ROOT',root)
    manifest=configs/'release_manifest.json'
    release.freeze(output,manifest,source_root)
    return root,output,manifest


def test_current_release_fresh_copy_needs_no_data_artifacts_or_git(scalar_fixture,tmp_path):
    root,output,manifest=scalar_fixture
    fresh=tmp_path/'fresh shallow checkout with spaces';shutil.copytree(root,fresh)
    rebuilt=tmp_path/'rebuilt current'
    result=release.rebuild(fresh/'configs/subset_search/release_manifest.json',rebuilt)
    assert result['ok'] and result['trials']==100
    assert not result['external_data_read'] and not result['external_artifact_read'] and not result['git_history_read']
    rows=list(csv.DictReader((rebuilt/'closest_matches.csv').open()))
    assert all(r['candidate_id']=='B' for r in rows)
    native=next(r for r in rows if r['endpoint']=='native_best_of_50')
    assert native['acc_sd']==native['nmi_sd']==native['delta_acc_sd_pp']==native['delta_nmi_sd_pp']==''
    assert int(native['n'])==1
    # A verified previous output can be replaced without leaving a stale backup.
    assert release.rebuild(fresh/'configs/subset_search/release_manifest.json',rebuilt)['ok']
    assert not rebuilt.with_name(rebuilt.name+'.previous').exists()


def test_hash_mismatch_fails_before_output_write(scalar_fixture,tmp_path):
    root,output,manifest=scalar_fixture
    (output/'trials.csv.gz').write_bytes(b'not the frozen input')
    destination=tmp_path/'must remain absent'
    with pytest.raises(ValueError,match='hash mismatch'):
        release.rebuild(manifest,destination)
    assert not destination.exists()


@pytest.mark.parametrize('change',['missing','duplicate','empty'])
def test_invalid_raw_trial_set_fails_before_output_write(scalar_fixture,tmp_path,change):
    root,output,manifest=scalar_fixture
    p=output/'trials.csv.gz'
    with gzip.open(p,'rt',newline='') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    if change=='missing':rows=rows[:-1]
    elif change=='duplicate':rows.append(rows[0])
    else:rows=[]
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    raw=stream.getvalue().encode();p.write_bytes(gzip.compress(raw,mtime=0))
    data=json.loads(manifest.read_text());data['inputs']['trials'].update(sha256=digest(p),bytes=p.stat().st_size,uncompressed_sha256=hashlib.sha256(raw).hexdigest());manifest.write_text(json.dumps(data))
    destination=tmp_path/'must remain absent'
    with pytest.raises(ValueError,match='missing trials|duplicate trial|empty trial'):
        release.rebuild(manifest,destination)
    assert not destination.exists()
