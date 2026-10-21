import unittest,tempfile,sys,os,io,base64
from pathlib import Path
from unittest.mock import patch,Mock
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'shared/scripts'))
from providers import Provider,fingerprint
class Adapter(unittest.TestCase):
    def client(self,name):
        config={'endpoint':'https://example.com/generate','model':'test-model','api_key_env':'ECOM_TEST_KEY','max_reference_images':2,'parameters':{}}
        with patch.dict(os.environ,{'ECOM_TEST_KEY':'test-secret'}):return Provider(name,config)
    def test_qwen_generation_contract(self):
        c=self.client('qwen');body=c.payload({'prompt':'cup','size':[1024,1024]},[])
        self.assertEqual(body['parameters']['size'],'1024*1024');self.assertEqual(body['input']['messages'][0]['content'],[{'text':'cup'}])
    def test_qwen_edit_contract(self):
        c=self.client('qwen')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ref.png';Image.new('RGB',(32,32)).save(p)
            body=c.payload({'prompt':'edit'},[p]);self.assertTrue(body['input']['messages'][0]['content'][0]['image'].startswith('data:image/png;base64,'))
    def test_volc_contract(self):
        c=self.client('volcengine');body=c.payload({'prompt':'cup','size':[1024,1024]},[])
        self.assertEqual(body['size'],'1024x1024');self.assertFalse(body['stream']);self.assertEqual(body['sequential_image_generation'],'disabled')
    def test_qwen_response(self):
        c=self.client('qwen');r=Mock(status_code=200);r.json.return_value={'request_id':'r','output':{'choices':[{'message':{'content':[{'image':'https://example.com/r.png'}]}}]}}
        with patch('requests.post',return_value=r):self.assertEqual(c.submit({'prompt':'x'},[])['results'][0]['url'],'https://example.com/r.png')
    def test_volc_base64(self):
        c=self.client('volcengine');r=Mock(status_code=200);r.json.return_value={'data':[{'b64_json':base64.b64encode(b'image').decode()}]}
        with patch('requests.post',return_value=r):result=c.submit({'prompt':'x'},[])
        self.assertEqual(c.download(result['results'][0]),b'image')
    def test_reserved_override(self):
        with self.assertRaises(ValueError):self.client('volcengine').payload({'prompt':'x','params':{'model':'other'}},[])
    def test_no_redirect_auth(self):
        c=self.client('qwen');r=Mock(status_code=302)
        with patch('requests.post',return_value=r) as req:
            with self.assertRaises(RuntimeError) as e:c.submit({'prompt':'x'},[])
            self.assertFalse(req.call_args.kwargs['allow_redirects']);self.assertNotIn('test-secret',str(e.exception))
    def test_missing_key(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ValueError):Provider('qwen',{'endpoint':'https://example.com','model':'x','api_key_env':'NO_KEY'})
if __name__=='__main__':unittest.main()
