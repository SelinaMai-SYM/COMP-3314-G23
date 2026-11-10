"""Markdown views retain endpoint qualifications and stable configuration IDs."""
import csv
import json
from pathlib import Path
import shutil
import pytest
from experiments.submission_refresh import tables


def test_markdown_pipe_ids_SD_and_zero_distance(tmp_path):
    root=tmp_path/'checkout';source=Path(__file__).resolve().parents[2]
    paper=root/'configs/v3/paper_reference.yaml';paper.parent.mkdir(parents=True);shutil.copy2(source/'configs/v3/paper_reference.yaml',paper)
    path=root/'results/submission_refresh/endpoint_comparison.csv';path.parent.mkdir(parents=True)
    rows=[{'benchmark':'ORL','method':'ssc','endpoint':'native_best_of_50','acc_mean':76.,'nmi_mean':88.6,'acc_sd':999.,'nmi_sd':999.,'D_max':0.,'D_mean':0.,'config_id':'run|E8|gamma1','status':'COMPLETED'}]
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    tables.build(root);view=(path.parent/'per_benchmark/ORL.md').read_text()
    assert 'run\\|E8\\|gamma1' in view and '999.000' not in view
    assert '0.000 / 0.000' in view and '76.000 (single assignment)' in view
    assert 'paper_reference.yaml' in json.loads((path.parent/'per_benchmark/table_inputs.json').read_text()).keys().__str__()
    previous=(path.parent/'per_benchmark/ORL.md').read_bytes()
    path.write_text('benchmark,method,endpoint,acc_mean\nORL,ssc,native_best_of_50,invalid\n')
    with pytest.raises(ValueError):tables.build(root)
    assert (path.parent/'per_benchmark/ORL.md').read_bytes()==previous
