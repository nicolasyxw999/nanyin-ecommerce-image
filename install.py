"""Install discoverable sibling skills plus shared resources, without overwriting."""
import argparse, shutil, json, tempfile, os
from pathlib import Path

def install(source,dest,selected=None):
    source=Path(source).resolve();dest=Path(dest).resolve();registry=json.loads((source/'shared/registry.json').read_text())
    names=selected or list(registry['skills']);unknown=set(names)-set(registry['skills'])
    if unknown:raise ValueError('Unknown skills: '+str(unknown))
    shared_name='nanyin-ecommerce-shared'
    targets=[dest/('nanyin-ecommerce-'+n) for n in names]+[dest/shared_name]
    if any(p.exists() for p in targets):raise ValueError('Destination exists; choose a new directory or explicitly manage upgrade')
    dest.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.ecom-stage-',dir=dest) as staging:
        stage=Path(staging);shutil.copytree(source/'shared',stage/shared_name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for n in names:
            folder=stage/('nanyin-ecommerce-'+n);shutil.copytree(source/'skills'/folder.name,folder)
            for p in folder.rglob('*.md'):p.write_text(p.read_text().replace('../../shared/','../'+shared_name+'/'))
        reg=dict(registry);reg['skills']={n:'../nanyin-ecommerce-'+n for n in names};(stage/shared_name/'registry.json').write_text(json.dumps(reg,indent=2))
        moved=[]
        try:
            for p in list(stage.iterdir()):target=dest/p.name;os.rename(p,target);moved.append(target)
        except Exception:
            for p in moved:shutil.rmtree(p)
            raise
    return [str(x) for x in targets]
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dest',required=True);p.add_argument('--skills',nargs='+');a=p.parse_args()
    print(json.dumps(install(Path(__file__).parent,a.dest,a.skills),ensure_ascii=False,indent=2))
