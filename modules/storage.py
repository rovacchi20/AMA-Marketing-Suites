import sqlite3, json
from pathlib import Path
DB_PATH = Path("output/app.db")
def _ensure_table(cur, create_sql: str):
    cur.execute(create_sql)
def _ensure_column(cur, table: str, col: str, ddl_type: str):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl_type}")
def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        _ensure_table(cur, "CREATE TABLE IF NOT EXISTS editorial_posts (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, channel TEXT, title TEXT, status TEXT, owner TEXT, copy TEXT, tags TEXT, assets TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        _ensure_column(cur, "editorial_posts", "copy", "TEXT")
        _ensure_column(cur, "editorial_posts", "tags", "TEXT")
        _ensure_column(cur, "editorial_posts", "assets", "TEXT")
        _ensure_column(cur, "editorial_posts", "updated_at", "TEXT DEFAULT CURRENT_TIMESTAMP")
        _ensure_table(cur, "CREATE TABLE IF NOT EXISTS newsletter_drafts (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, subject TEXT, sections TEXT, html TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        _ensure_table(cur, "CREATE TABLE IF NOT EXISTS wp_drafts (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, slug TEXT, html TEXT, status TEXT, tags TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        _ensure_table(cur, "CREATE TABLE IF NOT EXISTS social_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, datetime TEXT, channel TEXT, text TEXT, link TEXT, status TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        _ensure_table(cur, "CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, source TEXT, message TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        con.commit()
def add_post(date, channel, title, status="bozza", owner="", tags="", copy_text="", assets=None):
    assets = assets or []
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute("INSERT INTO editorial_posts (date, channel, title, status, owner, copy, tags, assets) VALUES (?,?,?,?,?,?,?,?)",(date, channel, title, status, owner, copy_text, tags, json.dumps(assets)))
        con.commit(); return cur.lastrowid
def list_posts(from_date=None, to_date=None, channels=None, statuses=None, search=""):
    q = "SELECT id, date, channel, title, status, owner, copy, tags, assets FROM editorial_posts WHERE 1=1"; params = []
    if from_date and to_date: q += " AND date BETWEEN ? AND ?"; params += [from_date, to_date]
    if channels: q += " AND channel IN (%s)" % ",".join("?"*len(channels)); params += channels
    if statuses: q += " AND status IN (%s)" % ",".join("?"*len(statuses)); params += statuses
    if search: q += " AND (title LIKE ? OR copy LIKE ? OR tags LIKE ?)"; params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    q += " ORDER BY date ASC, channel ASC"
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor(); cur.execute(q, params); rows = cur.fetchall(); cols = [d[0] for d in cur.description]
        out = [dict(zip(cols, r)) for r in rows]
        for r in out:
            try: r["assets"] = json.loads(r.get("assets") or "[]")
            except Exception: r["assets"] = []
        return out
def update_post(post_id: int, **fields):
    if not fields: return
    keys = list(fields.keys())
    q = "UPDATE editorial_posts SET " + ", ".join([f"{k}=?" for k in keys]) + ", updated_at=CURRENT_TIMESTAMP WHERE id=?"
    params = [fields[k] for k in keys] + [post_id]
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor(); cur.execute(q, params); con.commit()
def delete_post(post_id: int):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor(); cur.execute("DELETE FROM editorial_posts WHERE id=?", (post_id,)); con.commit()
def save_newsletter(title, subject, sections_json, html):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor(); cur.execute("INSERT INTO newsletter_drafts (title, subject, sections, html) VALUES (?,?,?,?)",(title, subject, sections_json, html)); con.commit(); return cur.lastrowid
def list_newsletters(limit=200):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor(); cur.execute("SELECT id, title, subject, sections, html, created_at FROM newsletter_drafts ORDER BY id DESC LIMIT ?", (limit,)); rows = cur.fetchall(); cols = [d[0] for d in cur.description]; return [dict(zip(cols, r)) for r in rows]
def save_wp_draft(title, slug, html, status="draft", tags=""):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor(); cur.execute("INSERT INTO wp_drafts (title, slug, html, status, tags) VALUES (?,?,?,?,?)",(title, slug, html, status, tags)); con.commit(); return cur.lastrowid
def list_wp_drafts(limit=200):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor(); cur.execute("SELECT id, title, slug, html, status, tags, created_at FROM wp_drafts ORDER BY id DESC LIMIT ?", (limit,)); rows = cur.fetchall(); cols = [d[0] for d in cur.description]; return [dict(zip(cols, r)) for r in rows]
def delete_wp_draft(draft_id: int):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor(); cur.execute("DELETE FROM wp_drafts WHERE id=?", (draft_id,)); con.commit()
def enqueue_post(datetime_iso, channel, text, link="", status="planned"):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor(); cur.execute("INSERT INTO social_queue (datetime, channel, text, link, status) VALUES (?,?,?,?,?)",(datetime_iso, channel, text, link, status)); con.commit(); return cur.lastrowid
def list_social_queue(limit=500):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor(); cur.execute("SELECT id, datetime, channel, text, link, status, created_at FROM social_queue ORDER BY datetime ASC LIMIT ?", (limit,)); rows = cur.fetchall(); cols = [d[0] for d in cur.description]; return [dict(zip(cols, r)) for r in rows]
def update_social_status(item_id: int, status: str):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor(); cur.execute("UPDATE social_queue SET status=? WHERE id=?", (status, item_id)); con.commit()
def insert_lead(rec: dict) -> int:
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor(); cur.execute("INSERT INTO leads (name, email, source, message) VALUES (?,?,?,?)",(rec.get("name"), rec.get("email"), rec.get("source"), rec.get("message"))); con.commit(); return cur.lastrowid
def list_leads(limit=200):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor(); cur.execute("SELECT id, name, email, source, message, created_at FROM leads ORDER BY id DESC LIMIT ?", (limit,)); rows = cur.fetchall(); cols = [d[0] for d in cur.description]; return [dict(zip(cols, r)) for r in rows]
