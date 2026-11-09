"""Prepare licensed ORL/YaleB archives explicitly, without network or old caches."""
from pathlib import Path
import argparse,hashlib,io,json,re,zipfile
import numpy as np
from PIL import Image
from benchmarks.data_paths import resolve_data_root

EXPECTED={'ORL_att92':'509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec','YaleB_cropped2414':'8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573'}
def prepare(dataset,archive,data_root):
    root=resolve_data_root(data_root);archive=Path(archive);digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest!=EXPECTED[dataset]:raise ValueError('archive hash differs from the documented release; do not silently change samples')
    if dataset=='ORL_att92':
        out=root/'orl/data/att92/processed';prefix='orl_att92';names=[f's{s}/{i}.pgm' for s in range(1,41) for i in range(1,11)];labels=np.repeat(np.arange(40,dtype=np.int64),10)
    else:
        out=root/'yaleb/data/cropped_wayback/processed';prefix='yaleb_cropped2414'
        with zipfile.ZipFile(archive) as z:names=sorted(n for n in z.namelist() if n.lower().endswith('.pgm') and 'ambient' not in n.lower())
        subjects=[re.search(r'yaleB(\d+)',n).group(1) for n in names];ids=sorted(set(subjects));labels=np.array([ids.index(s) for s in subjects],dtype=np.int64)
        if len(names)!=2414 or len(ids)!=38:raise ValueError('unexpected YaleB sample identity/count')
    arrays={key:[] for key in ['nearest','bilinear','bicubic']}
    with zipfile.ZipFile(archive) as z:
        for name in names:
            image=Image.open(io.BytesIO(z.read(name)));image.load();image=image.convert('L')
            for method in arrays:arrays[method].append(np.asarray(image.resize((32,32),getattr(Image.Resampling,method.upper())),dtype=np.uint8))
    out.mkdir(parents=True,exist_ok=True)
    for method,values in arrays.items():np.save(out/(prefix+'_32x32_'+method+'_uint8.npy'),np.stack(values))
    np.save(out/(prefix+'_labels_int64.npy'),labels)
    result={'dataset':dataset,'source_archive_sha256':digest,'sample_names':names,'array_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.npy'))}}
    (out/'preparation_manifest.json').write_text(json.dumps(result,indent=2)+'\n');return {'dataset':dataset,'n_samples':len(names),'n_classes':len(np.unique(labels)),'array_hashes':result['array_hashes']}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',choices=list(EXPECTED),required=True);ap.add_argument('--archive',required=True);ap.add_argument('--data-root',required=True);a=ap.parse_args();print(json.dumps(prepare(a.dataset,a.archive,a.data_root),indent=2))
if __name__=='__main__':main()
