"""Image integrity, manifest data, contact sheet and detail-page exports."""
import io, hashlib, os
from pathlib import Path
from PIL import Image, ImageOps

def inspect_image(path):
    path=Path(path)
    with Image.open(path) as im:im.verify()
    with Image.open(path) as im:
        im.load();size=list(im.size);fmt=im.format
    return {'path':str(path.resolve()),'size':size,'format':fmt,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def save_image(data,stem):
    with Image.open(io.BytesIO(data)) as im:im.verify()
    with Image.open(io.BytesIO(data)) as im:im.load();fmt=im.format
    ext={'PNG':'.png','JPEG':'.jpg','WEBP':'.webp'}.get(fmt)
    if not ext:raise ValueError('Unsupported image format')
    stem=Path(stem);stem.parent.mkdir(parents=True,exist_ok=True);path=stem.with_suffix(ext);tmp=path.with_suffix(ext+'.part')
    try:
        with tmp.open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        info=inspect_image(tmp);os.replace(tmp,path);info['path']=str(path.resolve());return info
    finally:tmp.unlink(missing_ok=True)

def export_images(paths,out,slice_height=1600):
    if not paths or slice_height<1:raise ValueError('Images and positive slice height required')
    out=Path(out);out.mkdir(parents=True,exist_ok=True);images=[]
    for p in paths:
        with Image.open(p) as im:images.append(im.convert('RGB'))
    width=images[0].width
    if any(i.width!=width for i in images):raise ValueError('Detail modules must share width; no implicit resizing')
    height=sum(i.height for i in images)
    if width*height>80_000_000:raise ValueError('Export exceeds 80 MP limit')
    canvas=Image.new('RGB',(width,height),'white');y=0
    for im in images:canvas.paste(im,(0,y));y+=im.height
    canvas.save(out/'detail-long.png');slices=[]
    for n,y in enumerate(range(0,height,slice_height),1):
        p=out/f'slice-{n:03d}.png';canvas.crop((0,y,width,min(y+slice_height,height))).save(p);slices.append(str(p))
    cols=min(4,len(images));rows=(len(images)+cols-1)//cols;sheet=Image.new('RGB',(cols*256,rows*256),'#eeeeee')
    for n,im in enumerate(images):sheet.paste(ImageOps.contain(im,(248,248)),((n%cols)*256,(n//cols)*256))
    sheet.save(out/'overview.jpg');return {'long':str(out/'detail-long.png'),'slices':slices,'overview':str(out/'overview.jpg')}
