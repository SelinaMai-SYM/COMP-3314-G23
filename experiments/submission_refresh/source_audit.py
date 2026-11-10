"""Read-only source-version audit, separate from unsupervised fitting.

Class labels diagnose duplicate conflicts; conflicts are recorded for all
parents. Only the separate UMIST deduplication consistency check is strict.
No official dataset is deduplicated or rewritten by this utility.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import io
import json
from pathlib import Path
import time
import tarfile
import zipfile
import numpy as np
from PIL import Image
from scipy.io import loadmat
from benchmarks.data_paths import resolve_data_root
from experiments.subset_search.catalogue import PARENTS, load_parent
from experiments.v3_reproduction.provenance import fingerprint_matrix, json_ready
from .core import ROOT, atomic_json, digest


def duplicate_audit(X,y):
    """Retain all exact-equality groups and first-occurrence inverse mapping.

    This intentionally does not call catalogue.exact_deduplicate: a conflicting
    BinAlpha group is diagnostic evidence, not a reason to reject the parent.
    """
    _,first,inverse,counts=np.unique(X,axis=0,return_index=True,return_inverse=True,return_counts=True)
    retained=np.sort(first);group_to_retained=np.empty(len(first),dtype=np.int64)
    group_to_retained[inverse[retained]]=np.arange(len(retained));mapping=group_to_retained[inverse]
    groups=[]
    for group in np.flatnonzero(counts>1):
        ids=np.flatnonzero(inverse==group);labels,numbers=np.unique(y[ids],return_counts=True)
        groups.append({'original_indices':ids.tolist(),'first_original_index':int(ids[0]),
            'class_counts':{str(k):int(n) for k,n in zip(labels,numbers)},'cross_class_conflict':len(labels)>1})
    groups.sort(key=lambda row:row['first_original_index'])
    return {'index_convention':'zero-based loader row index','input_rows':len(X),'unique_rows':len(retained),
        'duplicate_extra_rows':int(np.sum(counts-1)),
        'duplicate_pair_count':int(np.sum(counts*(counts-1)//2)),
        'duplicate_group_count':len(groups),'cross_class_duplicate_groups':sum(g['cross_class_conflict'] for g in groups),
        'first_occurrence_indices':retained.tolist(),'original_to_first_occurrence_row':mapping.tolist(),
        'duplicate_groups':groups,'official_input_modified':False,
        'equality_definition':'exact equality of the loaded pixel values; no tolerance or near-duplicate threshold'}


def _range(array):
    finite=np.asarray(array)[np.isfinite(array)]
    return [float(finite.min()),float(finite.max())] if finite.size else None


def _mat_details(path):
    mat=loadmat(path,mat_dtype=True);variables={};feature=None
    for name,value in mat.items():
        if name.startswith('__'):continue
        array=np.asarray(value);variables[name]={'shape':list(array.shape),'dtype':str(array.dtype)}
    for name in ['X','XX','fea','dat','facedat']:
        if name not in mat:continue
        array=np.asarray(mat[name]);feature={'variable':name,**variables[name]}
        if array.dtype==object:
            cells=[np.asarray(v) for v in array.ravel()]
            numeric=[v for v in cells if np.issubdtype(v.dtype,np.number)]
            ranges=[_range(v) for v in numeric]
            ranges=[r for r in ranges if r is not None]
            feature.update(cell_shapes=sorted({tuple(v.shape) for v in cells}),cell_dtypes=sorted({str(v.dtype) for v in cells}),
                pixel_range=[min(r[0] for r in ranges),max(r[1] for r in ranges)] if ranges else None,
                nonfinite_values=sum(int(np.count_nonzero(~np.isfinite(v))) for v in numeric))
        elif np.issubdtype(array.dtype,np.number):
            feature.update(pixel_range=_range(array),nonfinite_values=int(np.count_nonzero(~np.isfinite(array))))
        break
    geometry={name:int(np.asarray(mat[name]).item()) for name in ['im_height','im_width'] if name in mat and np.asarray(mat[name]).size==1}
    return {'reader':'scipy.io.loadmat(mat_dtype=True); declared MATLAB dtype convention',
            'variables':variables,'feature_storage':feature,'geometry_metadata':geometry}


def _image_archive_details(path):
    """Inspect native arrays without extracting image data into the checkout."""
    shapes=Counter();dtypes=Counter();pixel_min=None;pixel_max=None;nonfinite=0;seen=defaultdict(list);count=0
    def observe(name,raw):
        nonlocal count,pixel_min,pixel_max,nonfinite
        if '__MACOSX' in name or 'Ambient' in name:return
        suffix=Path(name).suffix.lower()
        if suffix not in ['.pgm','.tif','.tiff']:return
        with Image.open(io.BytesIO(raw)) as image:array=np.asarray(image.convert('L'))
        count+=1;shapes[str(tuple(array.shape))]+=1;dtypes[str(array.dtype)]+=1
        limits=_range(array);nonfinite+=int(np.count_nonzero(~np.isfinite(array)))
        if limits is not None:
            pixel_min=limits[0] if pixel_min is None else min(pixel_min,limits[0]);pixel_max=limits[1] if pixel_max is None else max(pixel_max,limits[1])
        payload=str(array.dtype).encode()+repr(array.shape).encode()+array.tobytes()
        seen[hashlib.sha256(payload).hexdigest()].append(name)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            for name in sorted(archive.namelist()):
                if Path(name).suffix.lower() in ['.pgm','.tif','.tiff']:observe(name,archive.read(name))
    elif tarfile.is_tarfile(path):
        with tarfile.open(path) as archive:
            for member in sorted(archive.getmembers(),key=lambda item:item.name):
                if member.isfile() and Path(member.name).suffix.lower()=='.pgm':
                    stream=archive.extractfile(member)
                    if stream is not None:observe(member.name,stream.read())
    else:return None
    return {'reader':'Pillow native image dimensions; grayscale L pixel interpretation',
        'non_ambient_image_count':count,'shape_counts':dict(shapes),'dtype_counts':dict(dtypes),
        'pixel_range':[pixel_min,pixel_max] if count else None,'nonfinite_values':nonfinite,
        'native_pixel_duplicate_groups':[{ 'pixel_sha256':sha,'source_member_names':members} for sha,members in sorted(seen.items()) if len(members)>1],
        'scope':'All PGM/TIFF archive members except Ambient and nonimage sidecars; no data written or removed.'}


def _resolution(parent_id,meta,feature_dimension,native_details):
    native=meta.get('original_spatial_size');processed=meta.get('processed_spatial_size')
    geometry=next((r['native_details'].get('geometry_metadata',{}) for r in native_details if r.get('native_details',{}).get('geometry_metadata')),None)
    if native is None and geometry and {'im_height','im_width'}<=geometry.keys():native=[geometry['im_height'],geometry['im_width']]
    evidence='loader-declared image geometry or actual source image/MAT geometry'
    if native is None and parent_id=='USPS':native=[16,16];evidence='LIBSVM release explicitly described as16x16 in loader; no resize'
    if native is None and parent_id=='YaleB_dengcai32':native=[32,32];evidence='loader documents the already32x32 source matrix; original pre-resize images unavailable'
    if processed is None and native is not None and int(np.prod(native))==feature_dimension:processed=list(native)
    return {'native_resolution':native,'processed_resolution':processed,
        'resolution_evidence':evidence if native is not None else 'No source image geometry metadata; feature count alone does not verify native resolution',
        'native_resolution_unverified':native is None}


def audit_sources(data_root,output):
    started=time.perf_counter();cpu=time.process_time();data_root=resolve_data_root(data_root);output=Path(output)
    output.mkdir(parents=True,exist_ok=True);mapping_dir=output/'source_duplicate_maps';mapping_dir.mkdir(exist_ok=True)
    frozen_path=ROOT/'results/subset_search/candidate_catalogue.json'
    frozen=json.loads(frozen_path.read_text()).get('parents',{}) if frozen_path.exists() else {}
    details_cache={};rows=[];matrix_aliases={};file_aliases={}
    for parent_id,(benchmark,folder,version) in PARENTS.items():
        row={'parent_id':parent_id,'benchmark':benchmark,'version':version,'status':'UNAVAILABLE',
             'historical_identity':'unverified','official_input_modified':False}
        try:
            X,y,meta=load_parent(parent_id,str(data_root));X=np.asarray(X);y=np.asarray(y)
            if X.ndim!=2 or y.shape!=(len(X),):raise ValueError('parent feature/label shape mismatch')
            duplicates=duplicate_audit(X,y)
            mapping_path=mapping_dir/(parent_id+'.json');atomic_json(mapping_path,duplicates)
            paths=meta.get('archive_paths',[meta.get('archive_path')]);source_files=[]
            for raw in paths:
                if not raw:continue
                source=Path(raw).resolve()
                if data_root not in source.parents:raise ValueError('source lies outside independent data root')
                relative=str(source.relative_to(data_root));sha=digest(source)
                expected=next((f['sha256'] for f in frozen.get(parent_id,{}).get('source_files',[]) if f['path_relative_to_data_root']==relative),None)
                if expected is not None and sha!=expected:raise ValueError('frozen source file hash mismatch')
                if sha not in details_cache:
                    if source.suffix.lower()=='.mat':details_cache[sha]=_mat_details(source)
                    elif source.suffix.lower() in ['.zip','.gz']:details_cache[sha]=_image_archive_details(source)
                    else:details_cache[sha]=None
                alias=file_aliases.get(sha);file_aliases.setdefault(sha,relative)
                source_files.append({'path_relative_to_data_root':relative,'sha256':sha,'bytes':source.stat().st_size,
                    'frozen_catalogue_hash_verified':expected is not None,'file_alias_of':alias,
                    'native_details':details_cache[sha]})
            fp=fingerprint_matrix(X,y);matrix_key=(fp['x_sha256'],fp['y_sha256'])
            alias=matrix_aliases.get(matrix_key);matrix_aliases.setdefault(matrix_key,parent_id)
            native_sources=[r for r in source_files if r.get('native_details')]
            row.update(status='AUDITED',shape=list(X.shape),dtype=str(X.dtype),labels_dtype=str(y.dtype),
                class_counts={str(k):int(n) for k,n in zip(*np.unique(y,return_counts=True))},
                classes=len(np.unique(y)),fingerprint=fp,nonfinite_values=int(np.count_nonzero(~np.isfinite(X))),
                processed_pixel_range=_range(X),source_files=source_files,source_url=meta.get('source_url'),
                source_order='Exact loader canonical order; indices zero-based; no score-based reorder',
                row_id_pattern=parent_id+':row:{zero_based_index}',
                source_selection=meta.get('sample_selection_method'),construction=meta.get('construction'),preprocessing_operations=meta.get('preprocessing_operations'),
                original_parent_id=meta.get('original_parent_id',parent_id),
                original_row_indices=meta.get('original_row_indices',list(range(len(X)))),
                physical_matrix_alias_of=alias,
                duplicate_map={'path':str(mapping_path.relative_to(output)),'sha256':digest(mapping_path),'bytes':mapping_path.stat().st_size},
                **{key:duplicates[key] for key in ['unique_rows','duplicate_extra_rows','duplicate_pair_count','duplicate_group_count','cross_class_duplicate_groups']},
                **_resolution(parent_id,meta,X.shape[1],native_sources))
            if parent_id.startswith('UMIST_'):
                row['strict_umist_duplicate_label_check_passed']=duplicates['cross_class_duplicate_groups']==0
                if not row['strict_umist_duplicate_label_check_passed']:row['status']='FAILED_UMIST_DUPLICATE_LABEL_CONSISTENCY'
            elif duplicates['cross_class_duplicate_groups']:
                row['status']='AUDITED_WITH_DUPLICATE_LABEL_CONFLICTS'
                row['conflict_interpretation']='Recorded as source evidence; parent not rejected or silently deduplicated.'
        except Exception as exc:row.update(status='UNAVAILABLE_OR_INVALID',error=repr(exc))
        rows.append(row)
    result={'schema':'parent-source-audit-v1','parents':rows,'parent_count':len(PARENTS),
        'available_audited_parents':sum(r['status'].startswith('AUDITED') for r in rows),
        'no_official_data_deduplicated':True,'labels_used_only_for_source_diagnostics':True,
        'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-started}
    atomic_json(output/'source_version_audit.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data-root',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();result=audit_sources(args.data_root,args.output)
    print(json.dumps({'parents':result['parent_count'],'audited':result['available_audited_parents'],
        'statuses':{r['parent_id']:r['status'] for r in result['parents']},'cpu_seconds':result['cpu_seconds']},indent=2))
    if any(r['status'] not in ['AUDITED','AUDITED_WITH_DUPLICATE_LABEL_CONFLICTS'] for r in result['parents']):raise SystemExit(1)


if __name__=='__main__':main()
