"""Read-only link inventory with local future-main validation and bounded HTTP checks.

No repository setting is modified. --published enables HTTP checks of the future
main links after the separate branch rename has actually completed.
"""
from __future__ import annotations
import argparse,csv,gzip,json,re,ssl,subprocess,time,urllib.error,urllib.parse,urllib.request
from collections import Counter
from pathlib import Path

OWNER='SelinaMai-SYM';REPO='COMP-3314-G23'
BASE='https://github.com/'+OWNER+'/'+REPO
RAW='https://raw.githubusercontent.com/'+OWNER+'/'+REPO
URL=re.compile(r'https?://[^\s<>"\'`\\\]\}]+')
MARKDOWN=re.compile(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)')
PROJECT=re.compile(r'^https?://(?:github\.com|raw\.githubusercontent\.com)/'+re.escape(OWNER+'/'+REPO)+r'(?:/|$)',re.I)
SKIP_SUFFIX={'.pdf','.png','.jpg','.jpeg','.gif','.npy','.npz','.mat','.ttf','.woff','.ico'}
SELF_OUTPUTS={'docs/submission_refresh/link_audit.md','results/submission_refresh/link_audit.csv','results/submission_refresh/link_audit_summary.json','results/submission_refresh/external_link_checks.json'}
LIVE=['README.md','report/README.md','report/main.tex','docs/final/data_setup.md','docs/final/sources_and_licenses.md','docs/final/presentation_outline.md']


def git(root,*args):
    return subprocess.check_output(['git',*args],cwd=root,text=True).strip()


def file_inventory(root):
    tracked=set(filter(None,git(root,'ls-files','-z').split('\0')))
    untracked=set(filter(None,git(root,'ls-files','--others','--exclude-standard','-z').split('\0')))
    return tracked,untracked


def lines(path):
    opener=gzip.open if path.suffix=='.gz' else open
    with opener(path,'rt',encoding='utf-8') as handle:
        yield from enumerate(handle,1)


def trim(url):
    return url.rstrip('.,;:)')


def main_target(url):
    parsed=urllib.parse.urlsplit(url);path=urllib.parse.unquote(parsed.path).split('/')
    # /OWNER/REPO/{blob,tree,raw}/REF/TARGET or raw.githubusercontent/OWNER/REPO/REF/TARGET.
    if parsed.netloc.lower()=='raw.githubusercontent.com':
        ref=path[3] if len(path)>3 else '';target='/'.join(path[4:]);kind='blob'
    else:
        if len(path)<5 or path[3] not in ['blob','tree','raw']:return None
        kind=path[3];ref=path[4];target='/'.join(path[5:])
    return ref,target,kind


def local_status(root,target,tracked,untracked):
    target=urllib.parse.unquote(target).split('#',1)[0]
    path=(root/target).resolve()
    if not path.is_relative_to(root):return 'OUTSIDE_CHECKOUT',False
    relative=path.relative_to(root).as_posix()
    if not path.exists():return 'LOCAL_MISSING',False
    if path.is_dir():return 'LOCAL_DIRECTORY_PRESENT',True
    if relative in tracked:return 'LOCAL_TRACKED_FILE_PRESENT',True
    if relative in untracked:return 'LOCAL_FILE_PENDING_ADD',True
    return 'LOCAL_ONLY_NOT_PUBLISHED',False


def ordinary_head(url):
    """One ordinary HEAD with verified TLS; no 429 retry or access bypass."""
    import certifi
    chain=[]
    class Redirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,request,fp,code,message,headers,newurl):
            chain.append({'status':code,'url':newurl})
            return super().redirect_request(request,fp,code,message,headers,newurl)
    opener=urllib.request.build_opener(Redirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    try:
        request=urllib.request.Request(url,method='HEAD',headers={'User-Agent':'COMP3314-public-link-audit/1.0'})
        with opener.open(request,timeout=12) as response:
            return {'http_status':response.status,'http_result':'ACCESSIBLE','final_url':response.url,
                    'redirects':chain,'retry_after':response.headers.get('Retry-After','')}
    except urllib.error.HTTPError as exc:
        return {'http_status':exc.code,'http_result':'RATE_LIMITED' if exc.code==429 else 'HTTP_ERROR',
                'final_url':exc.url,'redirects':chain,'retry_after':exc.headers.get('Retry-After','')}
    except Exception as exc:
        return {'http_status':'','http_result':'REQUEST_FAILED','final_url':url,'redirects':chain,'retry_after':'','error':repr(exc)}


def audit(root,published=False,external_limit=16,project_limit=80):
    started_cpu=time.process_time();started_wall=time.perf_counter()
    root=root.resolve();tracked,untracked=file_inventory(root);files=sorted(tracked|untracked)
    cache_path=root/'results/submission_refresh/external_link_checks.json'
    cached=json.loads(cache_path.read_text()).get('checks',{}) if cache_path.exists() else {}
    rows=[];branch_links=[];text_files=compressed=0
    scopes=set(p for p in LIVE if (root/p).exists())
    scopes.update(p for p in files if p.startswith(('docs/submission_refresh/','docs/subset_search/','.github/workflows/')) and p.endswith(('.md','.yml','.yaml','.tex')))
    scopes.difference_update(SELF_OUTPUTS)
    for name in files:
        if name in SELF_OUTPUTS:continue
        path=root/name
        if not path.is_file() or path.suffix.lower() in SKIP_SUFFIX:continue
        try:
            for line,text in lines(path):
                for match in URL.finditer(text):
                    url=trim(match.group())
                    if not PROJECT.match(url):continue
                    info=main_target(url)
                    if not info:continue
                    ref,target,kind=info
                    row={'source_path':name,'line':line,'kind':'project_url','original_link':url,
                         'future_main_url':url if ref=='main' else '', 'target':target,'ref':ref,
                         'historical':name.startswith(('archive/','docs/v3','docs/final/'))}
                    if ref=='main':
                        row['local_status'],row['locally_valid']=local_status(root,target,tracked,untracked)
                        row['http_result']='PENDING_BRANCH_RENAME' if not published else 'NOT_CHECKED'
                    elif ref in ['v1','v2','v3']:
                        row.update(local_status='BRANCH_SENSITIVE_REVIEW_REQUIRED',locally_valid=False,http_result='NOT_CHECKED');branch_links.append(row)
                    else:
                        row.update(local_status='IMMUTABLE_OR_OTHER_REF_PRESERVED',locally_valid=None,http_result='NOT_CHECKED')
                    rows.append(row)
            text_files+=1;compressed+=path.suffix=='.gz'
        except (UnicodeError,OSError):pass
    # Published current navigation gets future-main URLs with a local target check.
    for name in sorted(scopes):
        if name in SELF_OUTPUTS:continue
        path=root/name
        for line,text in lines(path):
            for match in MARKDOWN.finditer(text):
                link=match.group(1)
                parsed=urllib.parse.urlsplit(link)
                if parsed.scheme or link.startswith(('#','//')):continue
                target=(path.parent/urllib.parse.unquote(parsed.path)).resolve()
                if not target.is_relative_to(root):
                    rows.append({'source_path':name,'line':line,'kind':'relative','original_link':link,
                                 'target':link,'local_status':'OUTSIDE_CHECKOUT','locally_valid':False,'http_result':'NOT_A_PUBLIC_LINK'});continue
                relative=target.relative_to(root).as_posix();status,valid=local_status(root,relative,tracked,untracked)
                mode='tree' if target.is_dir() else 'blob'
                url=BASE+'/'+mode+'/main/'+urllib.parse.quote(relative,safe='/')
                if parsed.fragment:url+='#'+parsed.fragment
                rows.append({'source_path':name,'line':line,'kind':'relative','original_link':link,
                             'future_main_url':url,'target':relative,'ref':'main',
                             'local_status':status,'locally_valid':valid,
                             'http_result':'PENDING_BRANCH_RENAME' if not published else 'NOT_CHECKED'})
            for match in URL.finditer(text):
                url=trim(match.group())
                if PROJECT.match(url):continue
                rows.append({'source_path':name,'line':line,'kind':'external','original_link':url,
                             'local_status':'EXTERNAL_PRIMARY_SOURCE','locally_valid':None,'http_result':'NOT_CHECKED_BOUNDED_AUDIT'})
    # Keep one result per source occurrence while sharing actual HTTP work by URL.
    unique={}
    for row in rows:unique[(row['source_path'],row['line'],row['kind'],row['original_link'])]=row
    rows=list(unique.values());external={};project={}
    priority=['github.com/collinleiber/ClustPy/blob/','github.com/ChongYou/subspace-clustering/tree/',
              'github.com/LZUFE-Machine-Learning/EBSA/blob/','github.com/moetayuko/Fast-CD/tree/',
              'arxiv.org/pdf/2311.15214','openaccess.thecvf.com','raw.githubusercontent.com/LZUFE-Machine-Learning/Datasets/']
    urls=sorted({r['original_link'] for r in rows if r['kind']=='external'},
                key=lambda u:(next((i for i,p in enumerate(priority) if p in u),len(priority)),u))
    # The source-recovery block already investigated the throttled SharePoint
    # endpoint. This audit neither restarts its allowance nor circumvents it.
    for url in urls:
        if 'sharepoint.com' in url:
            external[url]={'http_result':'SKIPPED_PRIOR_429_SOURCE_RECOVERY_RECORD','http_status':'','retry_after':'','final_url':url}
        elif url in cached:
            external[url]={**cached[url],'validation_reused':True}
        elif len([v for v in external.values() if v.get('http_result')!='SKIPPED_PRIOR_429_SOURCE_RECOVERY_RECORD'])<external_limit:
            external[url]={**ordinary_head(url),'checked_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'validation_reused':False}
            cached[url]={k:v for k,v in external[url].items() if k!='validation_reused'}
    if published:
        for url in sorted({r.get('future_main_url') for r in rows if r.get('future_main_url') and r.get('locally_valid')})[:project_limit]:
            project[url]=ordinary_head(url)
    for row in rows:
        result=external.get(row['original_link']) if row['kind']=='external' else project.get(row.get('future_main_url'))
        if result:row.update({k:json.dumps(v,sort_keys=True) if isinstance(v,(list,dict)) else v for k,v in result.items()})
    out=root/'results/submission_refresh';out.mkdir(parents=True,exist_ok=True)
    cache_path.write_text(json.dumps({'schema':'ordinary-public-head-checks-v1','checks':cached},sort_keys=True,indent=2)+'\n')
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with (out/'link_audit.csv').open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    summary={'schema':'public-link-audit-v1','utc_timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
             'source_commit':git(root,'rev-parse','HEAD'),'published_main_http_enabled':published,
             'cpu_seconds':time.process_time()-started_cpu,'wall_seconds':time.perf_counter()-started_wall,
             'scanned_text_files':text_files,'compressed_files_scanned':compressed,
             'legacy_project_branch_urls':len(branch_links),'workflow_files':sum(p.startswith('.github/workflows/') for p in files),
             'current_navigation_sources':len(scopes),'link_occurrences':len(rows),
             'local_status_counts':dict(Counter(r['local_status'] for r in rows)),
             'http_result_counts':dict(Counter(r.get('http_result','') for r in rows)),
             'external_unique_requests':sum(r.get('http_result')!='SKIPPED_PRIOR_429_SOURCE_RECOVERY_RECORD' and not r.get('validation_reused',False) for r in external.values()),
             'external_reused_checks':sum(r.get('validation_reused',False) for r in external.values()),
             'external_limit':external_limit,'project_unique_requests':len(project),'project_limit':project_limit,
             'missing_current_targets':sorted({r['target'] for r in rows if r.get('local_status')=='LOCAL_MISSING'}),
             'publication_followup':'Rerun with --published only after main rename; locally validated future URLs are not yet claimed HTTP-accessible.'}
    (out/'link_audit_summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    doc=root/'docs/submission_refresh/link_audit.md'
    if doc.exists():
        begin='<!-- BEGIN CURRENT LINK STATUS -->';end='<!-- END CURRENT LINK STATUS -->'
        mode='Published-main HTTP pass' if published else 'Prepublication local/future-main pass'
        project_responses=Counter(str(r.get('http_status','')) for r in project.values())
        block=(begin+'\n\n## Current machine-verified snapshot\n\n'
               +f"{mode} at {summary['utc_timestamp']}, local commit `{summary['source_commit']}`. "
               +f"Legacy project branch URLs: {summary['legacy_project_branch_urls']}. "
               +f"Missing current target paths: {len(summary['missing_current_targets'])}. "
               +f"Fresh project HTTP requests: {len(project)}; response counts: {dict(project_responses)}. "
               +('Default-branch/head identity is checked separately by the publication workflow.' if published else 'Public main availability is pending the separate rename verification.')
               +'\n\n'+end)
        text=doc.read_text()
        if begin in text and end in text:
            text=text[:text.index(begin)]+block+text[text.index(end)+len(end):]
        else:text=text.rstrip()+'\n\n'+block+'\n'
        doc.write_text(text)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--published',action='store_true')
    parser.add_argument('--external-limit',type=int,default=16)
    parser.add_argument('--project-limit',type=int,default=80)
    args=parser.parse_args()
    print(json.dumps(audit(args.root,args.published,args.external_limit,args.project_limit),sort_keys=True,indent=2))


if __name__=='__main__':main()
