import os, zipfile, pathlib, requests
def build_press_kit(title: str, summary: str, file_paths: list[str], image_urls: list[str]) -> str:
    base=pathlib.Path("output/press_kits"); base.mkdir(parents=True, exist_ok=True)
    safe="".join(c for c in title if c.isalnum() or c in (" ","-","_")).strip().replace(" ","_") or "press_kit"
    kit=base/safe; kit.mkdir(parents=True, exist_ok=True)
    open(kit/"comunicato.txt","w",encoding="utf-8").write(f"{title}\n\n{summary}\n")
    for p in file_paths:
        try:
            data=open(p,"rb").read(); open(kit/os.path.basename(p),"wb").write(data)
        except Exception: pass
    for i,url in enumerate(image_urls,1):
        try:
            r=requests.get(url,timeout=30)
            if r.ok: open(kit/f"img_{i}.jpg","wb").write(r.content)
        except Exception: pass
    z=str(kit)+".zip"
    with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as zipf:
        for root,_,files in os.walk(kit):
            for f in files:
                fp=os.path.join(root,f); zipf.write(fp, arcname=os.path.relpath(fp, kit))
    return z
