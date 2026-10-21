"""Build a source ZIP and SHA-256 inventory from explicit distributable paths."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('skills', 'shared', 'tests', 'docs', 'scripts')
FILES = ('README.md', 'AUTHOR.md', 'LICENSE', '.gitignore', 'install.py',
         'requirements.txt', '使用说明.md', '来源与实现说明.md')


def main():
    version = json.loads((ROOT / 'shared/registry.json').read_text())['bundle_version']
    files = [ROOT / name for name in FILES]
    for name in DIRECTORIES:
        files.extend(p for p in (ROOT / name).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts
                     and p.suffix not in ('.pyc', '.pyo')
                     and p.name != '.DS_Store')
    files = sorted(files)
    if any(p.is_symlink() for p in files):
        raise ValueError('Do not distribute symlinks')
    inventory = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in files}
    manifest = json.dumps(inventory, ensure_ascii=False, indent=2) + '\n'
    (ROOT / 'MANIFEST.json').write_text(manifest, encoding='utf-8')
    out = ROOT / 'dist'
    out.mkdir(exist_ok=True)
    archive = out / f'nanyin-ecommerce-image-v{version}.zip'
    prefix = f'nanyin-ecommerce-image-v{version}'
    with ZipFile(archive, 'w', ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, prefix + '/' + p.relative_to(ROOT).as_posix())
        z.writestr(prefix + '/MANIFEST.json', manifest.encode('utf-8'))
    with ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('ZIP integrity failed')
        for name, expected in inventory.items():
            if hashlib.sha256(z.read(prefix + '/' + name)).hexdigest() != expected:
                raise ValueError('Archive hash mismatch: ' + name)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(checksum + '  ' + archive.name + '\n')
    print(json.dumps({'archive': str(archive), 'files': len(inventory) + 1,
                      'sha256': checksum, 'zip_integrity': 'passed'}, indent=2))


if __name__ == '__main__':
    main()
