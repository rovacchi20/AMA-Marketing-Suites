import os
from typing import List
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY","")
try:
    from slugify import slugify as _slugify
except Exception:
    import re as _re
    def _slugify(text: str) -> str:
        text=(text or "titolo").lower(); text=_re.sub(r"[^a-z0-9\s-]","",text); text=_re.sub(r"[\s-]+","-",text).strip("-"); return text
def apply_glossary(text: str, glossary_pairs: List[List[str]]) -> str:
    out=text
    for pair in glossary_pairs:
        if len(pair)==2:
            src,dst=pair; out=out.replace(src.strip(), dst.strip())
    return out
def ai_generate_copy(prompt: str, n: int = 3) -> List[str]:
    if not OPENAI_API_KEY:
        base=prompt[:200].strip(); return [f"[DRAFT {i+1}] {base}… CTA inclusa. #brand #promo" for i in range(n)]
    try:
        from openai import OpenAI
        client=OpenAI(api_key=OPENAI_API_KEY)
        sys='Sei un copywriter. Scrivi copy brevi e diversi tra loro; max 5 hashtag.'
        res=client.chat.completions.create(model='gpt-4o-mini',messages=[{'role':'system','content':sys},{'role':'user','content':prompt}],n=n,temperature=0.7)
        return [c.message.content.strip() for c in res.choices]
    except Exception as e:
        return [f"[ERRORE AI] {e}\n[FALLBACK] {prompt[:160]}… #brand"]
def to_slug(text: str) -> str:
    return _slugify(text or "titolo")
