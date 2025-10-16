import os, datetime as dt
from . import content
TPL="""<html><head><meta charset='utf-8'><title>{title}</title></head><body style='font-family:Arial,Helvetica,sans-serif;line-height:1.5;color:#111'><h1 style='margin:0 0 16px'>{title}</h1>{body}<hr><p style='font-size:12px;color:#666'>Bozza generata (locale)</p></body></html>"""
def build_html(title: str, sections: list[str]) -> str:
    parts=[]
    for s in sections:
        if ":" in s:
            h,p=s.split(":",1); parts.append(f"<h2 style='margin:24px 0 8px'>{h.strip()}</h2><p>{p.strip()}</p>")
        else:
            parts.append(f"<p>{s.strip()}</p>")
    return TPL.format(title=title, body="\n".join(parts))
def suggest_subjects(title: str, n: int = 5):
    prompt=f"Genera {n} oggetti email concisi e diversi per: {title}. Evita spam words."
    return content.ai_generate_copy(prompt, n=n)
def export_eml(subject: str, html: str, from_addr: str = "marketing@example.com", to_addr: str = "dest@example.com") -> str:
    eml=f"From: {from_addr}\nTo: {to_addr}\nDate: {dt.datetime.utcnow():%a, %d %b %Y %H:%M:%S} +0000\nSubject: {subject}\nMIME-Version: 1.0\nContent-Type: text/html; charset=utf-8\n\n{html}"
    os.makedirs("output/newsletters", exist_ok=True)
    path=os.path.join("output/newsletters", f"newsletter_{dt.datetime.now():%Y%m%d_%H%M%S}.eml")
    open(path,"w",encoding="utf-8").write(eml); return path
