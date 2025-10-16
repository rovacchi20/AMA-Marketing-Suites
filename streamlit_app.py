import os, json, datetime as dt, pandas as pd
from dotenv import load_dotenv
import streamlit as st
from modules import storage, content, newsletter, pr_pack
from modules import ics_export as icsq
load_dotenv(".env"); storage.init_db()
st.set_page_config(page_title="Marketing Ops — Local Suite", page_icon="🧩", layout="wide")
with st.sidebar:
    st.title("🧩 Marketing Ops (Local Suite)")
    page = st.radio("Navigazione", ["Dashboard","Copy Studio","Editorial Calendar","Newsletter Studio","WP Drafts (Local)","Social Queue (Local)","PR Pack","Leads","Impostazioni"], index=0)
    st.caption("Tutto locale. Solo OpenAI opzionale per il copy.")
if page == "Dashboard":
    st.header("Panoramica")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Post editoriali", len(storage.list_posts()))
    with c2: st.metric("Newsletter salvate", len(storage.list_newsletters()))
    with c3: st.metric("WP bozze locali", len(storage.list_wp_drafts()))
    with c4: st.metric("In coda social", len(storage.list_social_queue()))
elif page == "Copy Studio":
    st.header("Copy Studio")
    with st.expander("Brand & Glossario"):
        brand = st.text_area("Tono di voce", "Chiaro, concreto, utile.")
        gloss_raw = st.text_area("Glossario (termine→sostituzione per riga)", "AMA→AMA S.p.A.\nofficina→servizio officina")
    col1, col2 = st.columns(2)
    with col1:
        channel = st.selectbox("Canale", ["Instagram","Facebook","LinkedIn"])
        lang = st.selectbox("Lingua", ["Italiano","Inglese"])
        title = st.text_input("Titolo/Argomento")
    with col2:
        points = st.text_area("Punti chiave (uno per riga)", "Qualità\nAffidabilità\nAssistenza")
        cta = st.text_input("CTA", "Scopri di più")
        n = st.slider("Varianti", 1, 6, 3)
    if st.button("Genera copy"):
        pairs = []
        for row in gloss_raw.splitlines():
            if "→" in row:
                left, right = row.split("→", 1)
                pairs.append([left.strip(), right.strip()])
        brief = f"Canale: {channel}\nLingua: {lang}\nTono: {brand}\nTitolo: {title}\nPunti:\n{points}\nCTA: {cta}"
        outs = content.ai_generate_copy(content.apply_glossary(brief, pairs), n=n)
        for i, txt in enumerate(outs, 1):
            st.subheader(f"Variante {i}")
            st.write(txt)
elif page == "Editorial Calendar":
    st.header("Calendario editoriale (locale)")
    today = dt.date.today()
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Data", value=today)
        channel = st.selectbox("Canale", ["Instagram","Facebook","LinkedIn"])
        title = st.text_input("Titolo")
    with col2:
        status = st.selectbox("Stato", ["bozza","approvare","pronto","pubblicato"])
        owner = st.text_input("Owner", "")
        tags = st.text_input("Tags (csv)", "")
    copy_saved = st.text_area("Copy salvato (opzionale)")
    if st.button("Aggiungi al calendario"):
        storage.add_post(str(date), channel, title, status, owner, tags, copy_saved); st.success("Aggiunto")
    st.markdown("---")
    st.subheader("Post per mese")
    m = st.number_input("Mese", value=today.month, min_value=1, max_value=12)
    y = st.number_input("Anno", value=today.year, step=1)
    start = dt.date(int(y), int(m), 1)
    end = (start.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
    f1, f2, f3 = st.columns(3)
    with f1: chans = st.multiselect("Filtra canali", ["Instagram","Facebook","LinkedIn"], [])
    with f2: stats = st.multiselect("Filtra stati", ["bozza","approvare","pronto","pubblicato"], [])
    with f3: search = st.text_input("Cerca")
    posts = storage.list_posts(str(start), str(end), channels=chans or None, statuses=stats or None, search=search)
    st.dataframe(pd.DataFrame(posts), use_container_width=True) if posts else st.info("Nessun post per il periodo")
elif page == "Newsletter Studio":
    st.header("Newsletter — builder locale")
    title = st.text_input("Titolo newsletter")
    sections_raw = st.text_area("Sezioni (una per riga, formato: 'Header: testo')", "Hero: Offerta X\nProdotto 1: descrizione\nCTA finale: clicca qui")
    suggest = st.checkbox("Suggerisci 5 oggetti (AI)", value=False)
    subjects = []
    if suggest and title:
        subjects = newsletter.suggest_subjects(title, n=5)
        st.write("Suggerimenti:"); [st.write(f"- {s}") for s in subjects]
    chosen_subject = st.text_input("Oggetto scelto", subjects[0] if subjects else "")
    if st.button("Genera bozza e salva"):
        sections = [s for s in sections_raw.splitlines() if s.strip()]
        html = newsletter.build_html(title, sections)
        nid = storage.save_newsletter(title, chosen_subject or title, json.dumps(sections, ensure_ascii=False), html)
        st.success(f"Salvata bozza (ID {nid})")
        st.download_button("Scarica HTML", data=html, file_name=f"{title}.html", mime="text/html")
        eml_path = newsletter.export_eml(chosen_subject or title, html)
        with open(eml_path, "rb") as fh: st.download_button("Scarica EML", data=fh.read(), file_name=os.path.basename(eml_path), mime="message/rfc822")
    st.markdown("---")
    st.subheader("Archivio newsletter")
    nl = storage.list_newsletters()
    st.dataframe(pd.DataFrame(nl), use_container_width=True) if nl else st.info("Nessuna bozza salvata")
elif page == "WP Drafts (Local)":
    st.header("Bozze WordPress — solo locale")
    title = st.text_input("Titolo")
    slug = st.text_input("Slug", "")
    tags = st.text_input("Tag (csv)", "")
    status = st.selectbox("Stato", ["draft","publish"], index=0)
    html = st.text_area("Contenuto (HTML)", "<h2>Titolo</h2><p>Paragrafo...</p>", height=240)
    auto = st.checkbox("Genera slug automatico", value=not bool(slug))
    if auto:
        slug = content.to_slug(title); st.caption(f"Slug auto: {slug}")
    if st.button("Salva bozza locale"):
        did = storage.save_wp_draft(title, slug, html, status=status, tags=tags); st.success(f"Salvata (ID {did})")
        dl_name = (slug or "post") + ".html"
        st.download_button("Scarica HTML", data=html, file_name=dl_name, mime="text/html")
    st.markdown("---")
    drafts = storage.list_wp_drafts()
    st.dataframe(pd.DataFrame(drafts), use_container_width=True) if drafts else st.info("Nessuna bozza salvata")
elif page == "Social Queue (Local)":
    st.header("Coda social — locale")
    dt_str = st.text_input("Data/ora (YYYY-MM-DD HH:MM)", (dt.datetime.now()+dt.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"))
    channel = st.selectbox("Canale", ["Instagram","Facebook","LinkedIn"])
    text = st.text_area("Testo")
    link = st.text_input("Link (opzionale)", "")
    if st.button("Metti in coda"):
        storage.enqueue_post(dt_str, channel, text, link, "planned"); st.success("In coda")
    st.markdown("---")
    q = storage.list_social_queue()
    if q:
        df = pd.DataFrame(q); st.dataframe(df, use_container_width=True)
        ics_txt = icsq.export_ics_from_queue(q)
        st.download_button("Export ICS", data=ics_txt.encode("utf-8"), file_name="social_queue.ics", mime="text/calendar")
        st.download_button("Export CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="social_queue.csv", mime="text/csv")
    else:
        st.info("Coda vuota")
elif page == "PR Pack":
    st.header("Press kit — locale")
    t = st.text_input("Titolo comunicato")
    s = st.text_area("Sommario")
    up_files = st.file_uploader("Allega file/immagini", type=["jpg","jpeg","png","pdf","zip","docx"], accept_multiple_files=True)
    url_list = st.text_area("URL immagini (uno per riga)", "")
    if st.button("Crea ZIP"):
        os.makedirs("output/tmp_uploads", exist_ok=True)
        file_paths = []
        for f in up_files or []:
            path = os.path.join("output/tmp_uploads", f.name)
            with open(path, "wb") as fh: fh.write(f.read())
            file_paths.append(path)
        zip_path = pr_pack.build_press_kit(t or "Comunicato", s or "", file_paths, [u.strip() for u in url_list.splitlines() if u.strip()])
        st.success("Creato!")
        with open(zip_path, "rb") as fh: st.download_button("Scarica ZIP", fh, file_name=os.path.basename(zip_path))
elif page == "Leads":
    st.header("Leads — locale")
    name = st.text_input("Nome"); email = st.text_input("Email")
    source = st.text_input("Sorgente", "Sito/Evento/Campagna")
    msg = st.text_area("Messaggio")
    if st.button("Salva lead"):
        lid = storage.insert_lead({"name": name, "email": email, "source": source, "message": msg}); st.success(f"Lead salvato (ID {lid})")
    st.markdown("---")
    leads = storage.list_leads()
    st.dataframe(pd.DataFrame(leads), use_container_width=True) if leads else st.info("Nessun lead")
elif page == "Impostazioni":
    st.header("Impostazioni")
    st.write(f"OPENAI_API_KEY: {'✅' if os.getenv('OPENAI_API_KEY') else '— (fallback attivo)'}")
    st.write(f"TIMEZONE: {os.getenv('TIMEZONE','Europe/Rome')}")
