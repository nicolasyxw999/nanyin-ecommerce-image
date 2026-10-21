"""Explicit opt-in synchronous Qwen / Volcengine adapters."""
import base64,hashlib,json,os
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
from task_store import read_json

def fingerprint(config):return hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
def https(url):
    p=urlparse(url)
    if p.scheme!='https' or not p.hostname or p.username or p.password:raise ValueError('Explicit HTTPS endpoint required')
    return url

def data_uri(path):
    p=Path(path)
    if p.stat().st_size>20*1024*1024:raise ValueError('Reference exceeds local 20 MiB limit; check model limits too')
    with Image.open(p) as im:im.verify();fmt=im.format
    mime={'PNG':'image/png','JPEG':'image/jpeg','WEBP':'image/webp'}.get(fmt)
    if not mime:raise ValueError('Reference must be PNG/JPEG/WebP')
    return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()

class Provider:
    def __init__(self,name,config):
        if name not in ['qwen','volcengine']:raise ValueError('Unsupported external provider')
        self.provider=name;self.config=config;self.endpoint=https(config['endpoint'])
        self.model=config['model']
        if not self.model or '<' in self.model:raise ValueError('Configure actual model or endpoint ID')
        self.key=os.environ.get(config['api_key_env'])
        if not self.key:raise ValueError('Missing provider credential environment variable: '+config['api_key_env'])
        self.fingerprint=fingerprint(config)
        self.scope=fingerprint({'provider':name,'config':config,'key_hash':hashlib.sha256(self.key.encode()).hexdigest()})
    def payload(self,asset,refs):
        if len(refs)>self.config.get('max_reference_images',0):raise ValueError('Reference count exceeds configured model capability')
        params=dict(self.config.get('parameters',{}));params.update(asset.get('params',{}))
        if self.provider=='qwen':
            if params.get('n',1)!=1:raise ValueError('One output per asset required')
            params['n']=1
            if asset.get('size'):params.setdefault('size','*'.join(map(str,asset['size'])))
            content=[{'image':data_uri(p)} for p in refs]+[{'text':asset['prompt']}]
            return {'model':self.model,'input':{'messages':[{'role':'user','content':content}]},'parameters':params}
        forbidden={'model','prompt','image','stream','sequential_image_generation','sequential_image_generation_options','layer_decomposition'}
        if forbidden.intersection(params):raise ValueError('Reserved Volcengine parameter; configure model separately; single image only')
        if asset.get('size'):params.setdefault('size','x'.join(map(str,asset['size'])))
        body=dict(params,model=self.model,prompt=asset['prompt'],stream=False,sequential_image_generation='disabled')
        if refs:body['image']=[data_uri(p) for p in refs]
        return body
    def submit(self,asset,refs):
        import requests
        body=self.payload(asset,refs)
        try:
            r=requests.post(self.endpoint,headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'},json=body,timeout=(15,self.config.get('timeout_seconds',300)),allow_redirects=False)
            if not 200<=r.status_code<300:raise RuntimeError('Provider HTTP '+str(r.status_code))
            raw=r.json()
        except requests.RequestException:raise RuntimeError('Provider transport failure; submission outcome unknown') from None
        if raw.get('error') or raw.get('code'):raise RuntimeError('Provider returned error; inspect provider console')
        if self.provider=='qwen':
            images=[{'url':v['image']} for c in raw.get('output',{}).get('choices',[]) for v in c.get('message',{}).get('content',[]) if v.get('image')]
        else:images=[{'url':v['url']} if v.get('url') else {'b64':v['b64_json']} for v in raw.get('data',[]) if v.get('url') or v.get('b64_json')]
        if len(images)!=1:raise ValueError('Expected one image result; reconcile before any resubmission')
        return {'request_id':raw.get('request_id') or raw.get('id'),'results':images}
    def download(self,item):
        if item.get('b64'):return base64.b64decode(item['b64'],validate=True)
        import requests
        try:
            with requests.get(https(item['url']),stream=True,timeout=(15,120)) as r:
                r.raise_for_status();parts=[];size=0
                for chunk in r.iter_content(65536):
                    size+=len(chunk)
                    if size>100*1024*1024:raise ValueError('Result exceeds 100 MiB')
                    parts.append(chunk)
                return b''.join(parts)
        except requests.RequestException:raise RuntimeError('Download failed; retry saved result, not generation') from None

def load_provider(name,path):
    config=read_json(path)
    return Provider(name,config['providers'][name])
