"""Builtin tool handoff and opt-in synchronous provider execution."""
import argparse, hashlib, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from task_store import read_json, write_json, job_lock
from delivery import save_image, inspect_image, export_images

SKILLS=['nanyin-ecommerce-'+s for s in ['image','photography','detail','marketing','edit','consistency']]
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',value):raise ValueError('Invalid identifier')
    return value

def validate_plan(plan,base,skip_inputs=()):
    if plan.get('schema_version')!=2:raise ValueError('schema_version must be 2')
    identifier(plan['job_id'])
    if plan.get('provider','codex_builtin') not in ['codex_builtin','qwen','volcengine']:raise ValueError('Unknown provider')
    if plan.get('coordinator') not in SKILLS:raise ValueError('Unknown coordinator')
    assets=plan.get('assets')
    if not isinstance(assets,list) or not assets:raise ValueError('Nonempty assets required')
    seen=set()
    for a in assets:
        aid=identifier(a['asset_id']);identifier(a['sku_id'])
        if aid in seen:raise ValueError('Duplicate asset_id')
        if a.get('owner_skill') not in SKILLS[1:]:raise ValueError('A specialist must own each asset')
        if not isinstance(a.get('prompt'),str) or not a['prompt'].strip():raise ValueError('Prompt required')
        if not isinstance(a.get('params',{}),dict):raise ValueError('params must be an object')
        size=a.get('size')
        if size is not None and (not isinstance(size,list) or len(size)!=2 or any(type(x)!=int or x<1 for x in size)):raise ValueError('Expected size must be [width,height] or null')
        if any(dep not in seen for dep in a.get('depends_on',[])):raise ValueError('Dependencies must precede the asset (no cycles)')
        refs=a.get('references',[])
        for ref in refs:
            if ref.get('role') not in ['product','person','composition','style','base','mask','logo']:raise ValueError('Reference role required')
            if 'from_asset' in ref:
                if ref['from_asset'] not in a.get('depends_on',[]):raise ValueError('Generated reference must be a dependency')
            elif aid not in skip_inputs:
                p=(Path(base)/ref['path']).resolve()
                if not p.is_file():raise ValueError('Reference file missing')
                actual=hashlib.sha256(p.read_bytes()).hexdigest()
                if ref.get('sha256')!=actual:raise ValueError('Reference SHA-256 required and must match')
            if ref['role']=='mask':raise ValueError('Dedicated mask parameter unsupported; do not treat a mask as an ordinary reference')
        if any(r['role']=='base' for r in refs) and refs[0]['role']!='base':raise ValueError('Base reference must be first')
        if a['owner_skill'].endswith('-edit') and sum(r['role']=='base' for r in refs)!=1:raise ValueError('Editing requires exactly one base reference')
        seen.add(aid)
    return plan

def freeze(plan,root):
    previous=[read_json(p) for p in (root/'tasks').glob('*.json')]
    skip={r['asset_id'] for r in previous if r.get('submitted_intent')}
    validate_plan(plan,root,skip)
    lock=root/'plan.lock.json'
    if lock.exists() and digest(read_json(lock))!=digest(plan):raise ValueError('Plan changed; use a new version')
    write_json(lock,plan)
    if not (root/'plan.json').exists():write_json(root/'plan.json',plan)

def state_for(a,root):
    path=root/'tasks'/f"{a['asset_id']}.json"
    return read_json(path) if path.exists() else {'asset_id':a['asset_id'],'sku_id':a['sku_id'],'state':'planned'}

def save(root,s):
    s['updated_at']=datetime.now(timezone.utc).isoformat();s.setdefault('created_at',s['updated_at'])
    write_json(root/'tasks'/f"{s['asset_id']}.json",s)

def intact(root,s):
    try:return bool(s.get('files')) and all(inspect_image(root/f['path'])['sha256']==f['sha256'] for f in s['files'])
    except (OSError,ValueError):return False

def references(a,root):
    paths=[]
    for ref in a.get('references',[]):
        if 'from_asset' in ref:
            dep=read_json(root/'tasks'/f"{ref['from_asset']}.json")
            paths.append(str(root/dep['files'][0]['path']))
        else:paths.append(str((root/ref['path']).resolve()))
    return paths

def ready(a,root):
    for dep in a.get('depends_on',[]):
        p=root/'tasks'/f'{dep}.json'
        if not p.exists():return False
        s=read_json(p)
        if s['state']!='downloaded' or not intact(root,s):return False
    return True

def manifest(plan,root):
    states=[state_for(a,root) for a in plan['assets']]
    result={'schema_version':2,'provider':plan.get('provider','codex_builtin'),'job_id':plan['job_id'],'status':'downloaded' if all(s['state']=='downloaded' and intact(root,s) for s in states) else 'partial','visual_check':'not_checked','assets':states}
    write_json(root/'manifest.json',result);return result

def persist_image(a,root,s,data,evidence):
    info=save_image(data,root/'images'/a['asset_id']/'result')
    info['path']=str(Path(info['path']).relative_to(root))
    s.update(files=[info],evidence=evidence,state='needs_revision' if a.get('size') and info['size']!=a['size'] else 'downloaded',visual_check='not_checked')
    save(root,s)

def prepare_builtin(plan,root):
    if plan.get('provider','codex_builtin')!='codex_builtin':raise ValueError('Not a built-in job')
    root=Path(root).resolve()
    with job_lock(root):
        freeze(plan,root);work=[]
        for a in plan['assets']:
            s=state_for(a,root)
            if s['state']=='downloaded' and intact(root,s):continue
            if not ready(a,root):s['state']='blocked_dependency';save(root,s);continue
            previous=s['state'] in ['awaiting_tool','submission_unknown','downloaded','needs_revision']
            if s['state']=='needs_revision':action='review_existing_result'
            else:action='recover_or_inspect_previous_tool_call' if previous else 'call_image_gen_once'
            if not previous:s.update(state='awaiting_tool',submitted_intent=True);save(root,s)
            work.append({'asset_id':a['asset_id'],'state':s['state'],'action':action,'prompt':a['prompt'],'reference_paths':references(a,root) if not previous else [],'transparent_background':a.get('transparent_background',False)})
        manifest(plan,root)
        return {'provider':'codex_builtin','assets':work,'instruction':'Agent must call real image_gen; Python does not invoke or emulate that tool. Inspect local references first.'}

def record_builtin(plan,root,asset_id,source,evidence):
    if plan.get('provider','codex_builtin')!='codex_builtin':raise ValueError('Not a built-in job')
    if not evidence.strip():raise ValueError('Actual tool output reference required')
    root=Path(root).resolve()
    with job_lock(root):
        freeze(plan,root);a=next(a for a in plan['assets'] if a['asset_id']==asset_id);s=state_for(a,root)
        if not ready(a,root):raise ValueError('Dependency not ready')
        if s['state']=='downloaded' and intact(root,s):raise ValueError('Existing result preserved; use a new asset/job for revision')
        if s['state'] not in ['awaiting_tool','submission_unknown','downloaded']:raise ValueError('Prepare before recording')
        persist_image(a,root,s,Path(source).read_bytes(),evidence);return manifest(plan,root)

def run_external(plan,root,client,allow_submit=False):
    if plan.get('provider','codex_builtin')!=client.provider:raise ValueError('External provider must be explicitly selected in plan')
    root=Path(root).resolve()
    with job_lock(root):
        freeze(plan,root)
        for a in plan['assets']:
            s=state_for(a,root)
            if s.get('scope',client.scope)!=client.scope:raise ValueError('Provider configuration/account changed')
            if s['state']=='downloaded' and intact(root,s):continue
            if s['state']=='needs_revision':continue
            response_path=root/'responses'/f"{a['asset_id']}.json"
            if not ready(a,root):s['state']='blocked_dependency';save(root,s);continue
            if not response_path.exists():
                if s.get('submitted_intent'):s['state']='submission_unknown';save(root,s);continue
                if not allow_submit:save(root,s);continue
                auth=plan.get('authorization',{})
                if auth.get('provider')!=client.provider or auth.get('config_fingerprint')!=getattr(client,'fingerprint',client.scope):raise ValueError('Review external provider configuration and cost scope before submitting')
                used=sum(bool(read_json(p).get('submitted_intent')) for p in (root/'tasks').glob('*.json'))
                if type(auth.get('max_submissions'))!=int or used>=auth['max_submissions']:raise ValueError('Authorized submission count exceeded')
                refs=references(a,root)
                # Validate payload before marking submission intent, avoiding unknown state for local configuration errors.
                if hasattr(client,'payload'):client.payload(a,refs)
                s.update(state='submitting',submitted_intent=True,scope=client.scope);save(root,s)
                try:
                    response=client.submit(a,refs);write_json(response_path,response)
                except Exception as e:s.update(state='submission_unknown',error=type(e).__name__);save(root,s);continue
            try:
                response=read_json(response_path)
                if len(response.get('results',[]))!=1:raise ValueError('Exactly one saved result required')
                persist_image(a,root,s,client.download(response['results'][0]),response.get('request_id') or 'saved-sync-response')
            except Exception as e:s.update(state='download_failed',error=type(e).__name__);save(root,s)
        return manifest(plan,root)

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for name in ['validate-plan','prepare','record','run','resume','status','check']:
        c=sub.add_parser(name);c.add_argument('--job',required=True)
        if name in ['run','resume']:c.add_argument('--config');c.add_argument('--allow-submit',action='store_true')
        if name=='record':c.add_argument('--asset',required=True);c.add_argument('--source',required=True);c.add_argument('--evidence',required=True)
    c=sub.add_parser('provider-info');c.add_argument('--provider',choices=['qwen','volcengine'],required=True);c.add_argument('--config',required=True)
    c=sub.add_parser('export');c.add_argument('--images',nargs='+',required=True);c.add_argument('--output',required=True);c.add_argument('--slice-height',type=int,default=1600)
    args=p.parse_args()
    if args.command=='export':result=export_images(args.images,args.output,args.slice_height)
    elif args.command=='provider-info':
        from providers import fingerprint
        config=read_json(args.config)['providers'][args.provider]
        result={'provider':args.provider,'endpoint':config['endpoint'],'model':config['model'],'config_fingerprint':fingerprint(config),'live_connectivity':'not_checked'}
    else:
        root=Path(args.job).resolve();plan=read_json(root/'plan.json');provider=plan.get('provider','codex_builtin')
        if args.command=='validate-plan':validate_plan(plan,root);result={'valid':True,'provider':provider}
        elif args.command=='record':result=record_builtin(plan,root,args.asset,args.source,args.evidence)
        elif args.command=='status':result=manifest(plan,root)
        elif args.command=='check':
            result={'files':[inspect_image(x) for x in (root/'images').rglob('*') if x.is_file() and not x.name.endswith('.part')],'visual_check':'not_checked'};write_json(root/'file-checks.json',result)
        elif provider=='codex_builtin':result=prepare_builtin(plan,root)
        else:
            if args.command=='prepare':raise ValueError('prepare is built-in only')
            if not args.config:raise ValueError('External provider requires --config')
            from providers import load_provider
            result=run_external(plan,root,load_provider(provider,args.config),args.command=='run' and args.allow_submit)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,KeyError,OSError,StopIteration) as e:raise SystemExit(str(e)) from None
