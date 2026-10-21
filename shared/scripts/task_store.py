"""Atomic local records and OS-released advisory locks (POSIX hosts)."""
import json, os, tempfile, fcntl
from pathlib import Path
from contextlib import contextmanager

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write_json(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

@contextmanager
def job_lock(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    with (root/'.lock').open('a+') as f:
        try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Job is locked by another process') from None
        try:yield
        finally:fcntl.flock(f,fcntl.LOCK_UN)
