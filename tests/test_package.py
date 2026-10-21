import unittest, tempfile, sys, importlib.util, re, json
from pathlib import Path
from urllib.parse import unquote
B=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('installer',B/'install.py');installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)
class Package(unittest.TestCase):
    def test_install_and_links(self):
        with tempfile.TemporaryDirectory() as d:
            result=installer.install(B,d)
            self.assertEqual(len(result),7)
            for p in Path(d).glob('*/SKILL.md'):
                for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):self.assertTrue((p.parent/unquote(target)).exists(),target)
            with self.assertRaises(ValueError):installer.install(B,d)
    def test_subset(self):
        with tempfile.TemporaryDirectory() as d:
            installer.install(B,d,['edit'])
            self.assertEqual(len(list(Path(d).glob('*/SKILL.md'))),1)
            self.assertTrue((Path(d)/'nanyin-ecommerce-shared/scripts/ecommerce.py').exists())
    def test_all_package_links(self):
        for p in B.rglob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
                if not target.startswith(('https:','http:','#')):self.assertTrue((p.parent/unquote(target)).exists(),str(p)+':'+target)
if __name__=='__main__':unittest.main()
