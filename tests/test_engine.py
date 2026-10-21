import unittest,tempfile,sys,io,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'shared/scripts'))
from ecommerce import prepare_builtin,record_builtin,run_external,validate_plan
from task_store import read_json,write_json,job_lock
from PIL import Image
class Fake:
    scope='test';provider='qwen'
    def __init__(self):self.posts=0;self.unknown=False;self.bad=False
    def submit(self,a,refs):
        self.posts+=1
        if self.unknown:raise TimeoutError()
        return {'request_id':'r1','results':[{'url':'https://example.com/a.png'}]}
    def download(self,item):
        if self.bad:return b'bad'
        b=io.BytesIO();Image.new('RGB',(32,32),'white').save(b,format='PNG');return b.getvalue()
class Engine(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.plan={'schema_version':2,'job_id':'demo','coordinator':'nanyin-ecommerce-image','assets':[{'asset_id':'hero','sku_id':'sku1','owner_skill':'nanyin-ecommerce-photography','prompt':'white cup','size':[32,32],'references':[],'depends_on':[]}]}
        write_json(self.root/'plan.json',self.plan);self.client=Fake()
    def tearDown(self):self.tmp.cleanup()
    def external(self):
        self.plan.update(provider='qwen',authorization={'provider':'qwen','max_submissions':1,'config_fingerprint':'test'})
    def test_builtin_default_no_key(self):
        r=prepare_builtin(self.plan,self.root);self.assertEqual(r['provider'],'codex_builtin');self.assertEqual(r['assets'][0]['state'],'awaiting_tool')
    def test_record_builtin(self):
        prepare_builtin(self.plan,self.root);p=self.root/'result.png';p.write_bytes(self.client.download({}))
        record_builtin(self.plan,self.root,'hero',p,'tool-result-1');self.assertEqual(read_json(self.root/'manifest.json')['status'],'downloaded')
    def test_builtin_repeat_requires_recovery(self):
        prepare_builtin(self.plan,self.root);r=prepare_builtin(self.plan,self.root);self.assertEqual(r['assets'][0]['action'],'recover_or_inspect_previous_tool_call')
    def test_external_unknown(self):
        self.external();self.client.unknown=True;run_external(self.plan,self.root,self.client,True);self.client.unknown=False;run_external(self.plan,self.root,self.client,True);self.assertEqual(self.client.posts,1)
    def test_download_recovery(self):
        self.external();self.client.bad=True;run_external(self.plan,self.root,self.client,True);self.client.bad=False;run_external(self.plan,self.root,self.client,False);self.assertEqual(self.client.posts,1);self.assertEqual(read_json(self.root/'tasks/hero.json')['state'],'downloaded')
    def test_changed_plan_rejected(self):
        prepare_builtin(self.plan,self.root);self.plan['assets'][0]['prompt']='changed'
        with self.assertRaises(ValueError):prepare_builtin(self.plan,self.root)
    def test_traversal(self):
        self.plan['assets'][0]['asset_id']='../bad'
        with self.assertRaises(ValueError):validate_plan(self.plan,self.root)
    def test_external_requires_selection(self):
        with self.assertRaises(ValueError):run_external(self.plan,self.root,self.client,True)
    def test_base_first(self):
        a=self.plan['assets'][0];a['owner_skill']='nanyin-ecommerce-edit';p=self.root/'r.png';p.write_bytes(self.client.download({}));r={'path':'r.png','sha256':hashlib.sha256(p.read_bytes()).hexdigest()};a['references']=[dict(r,role='style'),dict(r,role='base')]
        with self.assertRaises(ValueError):validate_plan(self.plan,self.root)
    def test_external_limit_blocks_before_submit(self):
        self.external();self.plan['authorization']['max_submissions']=0
        with self.assertRaises(ValueError):run_external(self.plan,self.root,self.client,True)
        self.assertEqual(self.client.posts,0)
    def test_external_repeat_and_missing_file_recover(self):
        self.external();run_external(self.plan,self.root,self.client,True)
        run_external(self.plan,self.root,self.client,True)
        task=read_json(self.root/'tasks/hero.json');(self.root/task['files'][0]['path']).unlink()
        run_external(self.plan,self.root,self.client,False)
        self.assertEqual(self.client.posts,1)
        self.assertEqual(read_json(self.root/'manifest.json')['status'],'downloaded')
    def test_dependency_waits_for_recorded_image(self):
        import copy
        a=copy.deepcopy(self.plan['assets'][0]);a.update(asset_id='detail',depends_on=['hero'],references=[{'role':'product','from_asset':'hero'}])
        self.plan['assets'].append(a)
        self.assertEqual(len(prepare_builtin(self.plan,self.root)['assets']),1)
        p=self.root/'result.png';p.write_bytes(self.client.download({}));record_builtin(self.plan,self.root,'hero',p,'fixture')
        work=prepare_builtin(self.plan,self.root)['assets'];self.assertEqual(work[0]['asset_id'],'detail');self.assertTrue(Path(work[0]['reference_paths'][0]).is_file())
    def test_dimension_mismatch_needs_revision(self):
        self.plan['assets'][0]['size']=[64,64];prepare_builtin(self.plan,self.root)
        p=self.root/'result.png';p.write_bytes(self.client.download({}));record_builtin(self.plan,self.root,'hero',p,'fixture')
        self.assertEqual(read_json(self.root/'tasks/hero.json')['state'],'needs_revision')
        self.assertEqual(prepare_builtin(self.plan,self.root)['assets'][0]['action'],'review_existing_result')
    def test_lock(self):
        with job_lock(self.root):
            with self.assertRaises(RuntimeError):
                with job_lock(self.root):pass
if __name__=='__main__':unittest.main()
