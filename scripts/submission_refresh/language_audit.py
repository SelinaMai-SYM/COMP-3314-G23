"""Inventory current publication text, decoded records and extracted PDFs.

Script detection is review evidence, not a language certificate. Known JSON
serialization layers are parsed once; literal backslash escapes inside decoded
strings are preserved. No publication text, legal notice or identity is edited.
"""
from __future__ import annotations
import argparse
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import re
import resource
import subprocess
import time
import zlib

SCRIPT = re.compile('[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\U00020000-\U0002fa1f]')
BINARY = {'.png','.jpg','.jpeg','.gif','.ico','.npz','.npy','.mat','.woff','.woff2',
    '.ttf','.otf','.zip','.bundle','.tar','.tgz','.bz2','.xz','.7z','.rar','.tif','.tiff'}


def _sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def _git_inventory(root):
    def git(*args):return subprocess.check_output(['git',*args],cwd=root).decode()
    tracked=set(filter(None,git('ls-files','-z').split('\0')))
    pending=set(filter(None,git('ls-files','--others','--exclude-standard','-z').split('\0')))
    return {'tracked':tracked,'pending':pending,'head':git('rev-parse','HEAD').strip(),
        'status':git('status','--porcelain=v1','-z')}


def _contexts(text):
    count=0;examples=[]
    for number,line in enumerate(text.splitlines(),1):
        matches=list(SCRIPT.finditer(line));count+=len(matches)
        if matches and len(examples)<5:
            index=matches[0].start()
            examples.append({'line':number,'context':line[max(0,index-60):index+100].strip()})
    return count,examples


def _decoded_strings(node,path='$'):
    if isinstance(node,str):yield path,node
    elif isinstance(node,dict):
        for key,value in node.items():
            if isinstance(key,str):yield path+'[object key]',key
            yield from _decoded_strings(value,path+'['+json.dumps(str(key),ensure_ascii=True)+']')
    elif isinstance(node,list):
        for index,value in enumerate(node):yield from _decoded_strings(value,path+f'[{index}]')


def _structured_scan(name,text):
    base=name.lower()[:-3] if name.lower().endswith('.gz') else name.lower()
    suffix=Path(base).suffix
    if suffix not in {'.json','.jsonl','.ndjson','.ipynb'}:
        return {'format':None,'CJK_characters':0,'contexts':[]}
    count=0;examples=[];documents=0
    entries=((number,line) for number,line in enumerate(text.splitlines(),1) if line.strip()) if suffix in {'.jsonl','.ndjson'} else [(None,text)]
    for number,serialized in entries:
        document=json.loads(serialized.lstrip('\ufeff'));documents+=1
        for location,value in _decoded_strings(document):
            matches=list(SCRIPT.finditer(value));count+=len(matches)
            if matches and len(examples)<5:
                index=matches[0].start()
                examples.append({'record_line':number,'value_path':location,
                    'context':value[max(0,index-60):index+100]})
    return {'format':suffix.lstrip('.'),'documents':documents,'CJK_characters':count,'contexts':examples}


def audit(root,output,*,pdf_timeout=30):
    root=Path(root).resolve();output=Path(output).resolve()
    started=time.process_time();wall_started=time.perf_counter()
    child_before=resource.getrusage(resource.RUSAGE_CHILDREN)
    before=_git_inventory(root)
    excluded=lambda name:(root/name).resolve()==output
    names={name for name in before['tracked']|before['pending'] if not excluded(name)}
    flags=[];filename_flags=[];pdfs=[];compressed=[];notebooks=[];records=[];errors=[];manual=[];decoded=0
    for name in sorted(names):
        path=root/name
        item={'path':name,'tracked':name in before['tracked'],'pending_untracked':name in before['pending']}
        records.append(item)
        if SCRIPT.search(name):filename_flags.append(name)
        if not path.is_file():
            item['classification']='NOT_A_REGULAR_FILE'
            errors.append({'path':name,'kind':'UNAVAILABLE_INPUT','error':'Publication inventory entry is not a regular file'})
            continue
        try:raw=path.read_bytes()
        except OSError as exc:
            item['classification']='UNREADABLE_INPUT';errors.append({'path':name,'kind':'UNREADABLE_INPUT','error':str(exc)});continue
        item.update(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
        if path.suffix.lower() in BINARY or name.lower().endswith('.tar.gz'):
            item['classification']='EXCLUDED_KNOWN_BINARY';continue
        if path.suffix.lower()=='.pdf':
            item['classification']='PDF'
            pdf={'path':name,'sha256':item['sha256'],'extraction_status':'FAILED','CJK_characters':0,'extracted_characters':0}
            pdfs.append(pdf)
            try:
                result=subprocess.run(['pdftotext','-enc','UTF-8',str(path),'-'],capture_output=True,timeout=pdf_timeout)
                text=result.stdout.decode('utf-8')
                if result.returncode:
                    errors.append({'path':name,'kind':'PDF_EXTRACTION_FAILED','error':result.stderr.decode(errors='replace'),'exit_code':result.returncode})
                else:
                    count,contexts=_contexts(text)
                    pdf.update(extraction_status='OK' if text.strip() else 'NO_TEXT_MANUAL_REVIEW_REQUIRED',
                        CJK_characters=count,extracted_characters=len(text),extracted_text_sha256=hashlib.sha256(result.stdout).hexdigest())
                    if count:flags.append({'path':name,'kind':'PDF','count':count,'contexts':contexts})
                    if not text.strip():manual.append({'path':name,'sha256':item['sha256'],'reason':'PDF_NO_EXTRACTABLE_TEXT','required_review':'Rendered pages or an explicitly reviewed OCR transcript'})
            except (OSError,subprocess.TimeoutExpired,UnicodeError) as exc:
                errors.append({'path':name,'kind':'PDF_EXTRACTION_FAILED','error':str(exc)})
            item.update(pdf)
            continue
        try:
            uncompressed=gzip.decompress(raw) if path.suffix.lower()=='.gz' else raw
            text=uncompressed.decode('utf-8')
            if '\x00' in text:raise UnicodeError('binary NUL in unclassified text input')
            count,contexts=_contexts(text)
            structured=_structured_scan(name,text)
            decoded+=1
            item.update(classification='STRUCTURED_TEXT' if structured['format'] else 'TEXT',
                uncompressed_bytes=len(uncompressed),uncompressed_sha256=hashlib.sha256(uncompressed).hexdigest(),
                raw_CJK_characters=count,decoded_value_CJK_characters=structured['CJK_characters'],
                decoded_format=structured['format'],decoded_documents=structured.get('documents',0))
            # Counts are separate raw/decoded views and can overlap.
            if count:flags.append({'path':name,'kind':'RAW_TEXT','count':count,'contexts':contexts})
            if structured['CJK_characters']:
                flags.append({'path':name,'kind':'DECODED_STRUCTURED_VALUES','count':structured['CJK_characters'],'contexts':structured['contexts']})
            if path.suffix.lower()=='.gz':compressed.append({**item,'compressed_sha256':item['sha256']})
            if path.suffix.lower()=='.ipynb':notebooks.append(name)
        except (UnicodeError,EOFError,OSError,ValueError,zlib.error,RecursionError) as exc:
            item['classification']='UNDECODABLE_OR_INVALID_TEXT'
            item['error']=str(exc)
            errors.append({'path':name,'kind':'UNDECODABLE_OR_INVALID_TEXT','error':str(exc)})
    after=_git_inventory(root)
    after_names={name for name in after['tracked']|after['pending'] if not excluded(name)}
    changed=[]
    for item in records:
        if 'sha256' not in item:continue
        try:unchanged=_sha(root/item['path'])==item['sha256']
        except OSError:unchanged=False
        item['unchanged_during_audit']=unchanged
        if not unchanged:changed.append(item['path'])
    inventory_changed=names!=after_names or before['head']!=after['head'] or before['status']!=after['status']
    if changed or inventory_changed:
        errors.append({'kind':'INPUTS_CHANGED_DURING_AUDIT','paths':changed,
            'added_paths':sorted(after_names-names),'removed_paths':sorted(names-after_names),
            'git_inventory_or_head_changed':inventory_changed})
    own_cpu=time.process_time()-started
    child_after=resource.getrusage(resource.RUSAGE_CHILDREN)
    child_cpu=child_after.ru_utime+child_after.ru_stime-child_before.ru_utime-child_before.ru_stime
    inventory_hash=hashlib.sha256(json.dumps({item['path']:item.get('sha256') for item in records},sort_keys=True).encode()).hexdigest()
    passed=not(flags or filename_flags or errors or manual)
    result={'schema':'current-language-inventory-v3','timestamp_UTC':dt.datetime.now(dt.timezone.utc).isoformat(),
        'source_commit':before['head'],'source_commit_after':after['head'],
        'working_tree_dirty':bool(before['status']),'git_status_before':before['status'],'git_status_after':after['status'],
        'scope':'Tracked and nonignored pending publication files; output itself excluded',
        'input_inventory_sha256':inventory_hash,'inputs_unchanged':not(changed or inventory_changed),
        'file_inventory':records,'decoded_text_files':decoded,'remaining_flags':flags,'filename_flags':filename_flags,
        'notebooks':notebooks,'compressed_records':compressed,
        'tracked_PDFs':[p['path'] for p in pdfs if p['path'] in before['tracked']],
        'pending_PDFs':[p['path'] for p in pdfs if p['path'] not in before['tracked']],
        'pdf_extraction':pdfs,'manual_review_required':manual,'errors':errors,
        'own_cpu_seconds':own_cpu,'child_cpu_seconds':child_cpu,'cpu_seconds':own_cpu+child_cpu,
        'cpu_definition':'This process plus waited child processes, including Git and PDF extraction.',
        'wall_seconds':time.perf_counter()-wall_started,'machine_audit_passed':passed,'language_certified':False,
        'interpretation':'Raw text and decoded structured values are separate views; matches can overlap. Only known JSON serialization layers are decoded, never arbitrary backslash escapes. Script detection is a review inventory; English prose, legal notices, author identities and rendered layout require human review.'}
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_name(output.name+'.tmp')
    temporary.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');temporary.replace(output)
    print(json.dumps({key:value for key,value in result.items() if key not in
        ['file_inventory','pdf_extraction','compressed_records','tracked_PDFs','pending_PDFs']},sort_keys=True))
    return passed


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    raise SystemExit(0 if audit(args.root,args.output or args.root/'results/submission_refresh/language_inventory.json') else 1)
