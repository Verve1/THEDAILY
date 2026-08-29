#!/usr/bin/env python3
"""
THE DAILY — static site generator.
Reads /data/<date>.json editions and produces:
  site/index.html              (latest edition, i.e. homepage)
  site/archive/<date>.html     (permanent edition page, never overwritten in content)
  site/archive/index.html      (archive listing grouped by month)

Run: python3 generate.py
"""
import json, os, glob
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
SITE_DIR = os.path.join(ROOT, "site")
ARCHIVE_DIR = os.path.join(SITE_DIR, "archive")

os.makedirs(ARCHIVE_DIR, exist_ok=True)

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" href="{assets_prefix}assets/logo.png">
<link rel="stylesheet" href="{assets_prefix}styles.css">
</head>
<body>
"""

FOOT = """
<footer>
  <div class="wrap">
    <div>
      <div class="fbrand">THE DAILY — THISWEEK.FIN</div>
      <div class="disclaimer">Business and finance news, edited daily. Figures verified against primary and wire sources at time of publication; market data is a point-in-time snapshot, not investment advice. Corrections: contact via thisweek.fin.</div>
    </div>
    <div>
      <a href="{archive_prefix}archive/index.html">Full Archive →</a>
    </div>
  </div>
</footer>
</body>
</html>
"""

def esc(s):
    return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def source_html(src, secondary=None):
    if not src: return ""
    out = f'<span class="srcline">Source: <a class="src-link" href="{esc(src["url"])}" target="_blank" rel="noopener">{esc(src["name"])}</a>'
    if secondary:
        out += f' &middot; <a class="src-link" href="{esc(secondary["url"])}" target="_blank" rel="noopener">{esc(secondary["name"])}</a>'
    out += "</span>"
    return out

def top3_block(item):
    pos = item["position"]
    cls = "center" if pos == "center" else "side"
    hcls = "headline big" if pos == "center" else "headline"
    eyebrow = "TOP STORY" if pos == "center" else ("#2" if item["rank"] == 2 else "#3")
    why = f'<div class="why">Why it matters</div><p class="why-text">{esc(item["whyItMatters"])}</p>' if pos == "center" or item.get("whyItMatters") else ""
    keynum = ""
    if item.get("keyNumber"):
        keynum = f'''<div class="keynum"><span class="num">{esc(item["keyNumber"])}</span><span class="lbl">{esc(item.get("keyNumberLabel",""))}</span></div>'''
    return f'''
  <div class="{cls}">
    <div class="eyebrow">{eyebrow}</div>
    <h1 class="{hcls}">{esc(item["headline"])}</h1>
    <p class="dek">{esc(item["summary"])}</p>
    {why}
    {keynum}
    {source_html(item.get("source"), item.get("secondarySource"))}
  </div>'''

def story_html(s):
    kn = f'<div class="kn">{esc(s["keyNumber"])}</div>' if s.get("keyNumber") else ""
    return f'''
    <div class="story">
      <h3>{esc(s["headline"])}</h3>
      <p>{esc(s["text"])}</p>
      {kn}
      <div class="src">{source_html(s.get("source"))}</div>
    </div>'''

def market_cell(m):
    return f'''
    <div class="mkt-cell">
      <div class="lbl">{esc(m["label"])}</div>
      <div class="val">{esc(m["value"])}</div>
      <div class="chg {m["direction"]}">{esc(m["change"])}</div>
    </div>'''

def render_edition(data, assets_prefix, archive_prefix, is_latest):
    top3_sorted = sorted(data["top3"], key=lambda x: {"left":0,"center":1,"right":2}[x["position"]])
    top3_html = "".join(top3_block(i) for i in top3_sorted)

    biz = data["sections"]["business"]
    mkt = data["sections"]["markets"]
    tech = data["sections"]["technology"]
    comp = data["sections"]["companies"]
    watch = data["sections"]["whatToWatch"]

    biz_html = "".join(story_html(s) for s in biz["stories"])
    tech_html = "".join(story_html(s) for s in tech["stories"])
    comp_html = "".join(story_html(s) for s in comp["stories"])
    watch_html = "".join(story_html(s) for s in watch["stories"])
    mkt_cells = "".join(market_cell(m) for m in mkt["data"])
    mkt_stories = "".join(story_html(s) for s in mkt.get("stories", []))

    nav_home_active = "active" if is_latest else ""

    body = f'''
<div class="masthead">
  <div class="wrap">
    <div class="masthead-row">
      <div class="brand">
        <img src="{assets_prefix}assets/logo.png" alt="logo">
        <div class="brand-text">
          <div class="brand-title">{esc(data["edition"])}</div>
          <div class="brand-sub">THISWEEK.FIN</div>
        </div>
      </div>
      <div class="masthead-meta">BUSINESS &amp; FINANCE, DAILY<br><span class="date">{esc(data["displayDate"])}</span></div>
    </div>
    <div class="nav">
      <a href="{archive_prefix}index.html" class="{nav_home_active}">LATEST</a>
      <a href="{archive_prefix}archive/index.html">ARCHIVE</a>
    </div>
  </div>
</div>
<div class="rule-green"></div>

<div class="wrap">
  <div class="top3">{top3_html}
  </div>

  <section class="sec">
    <div class="sec-title">{biz["title"]}</div>
    <div class="story-grid">{biz_html}</div>
  </section>

  <section class="sec">
    <div class="sec-title">{mkt["title"]} <span class="tag">SNAPSHOT</span></div>
    <div class="mkt-note">{esc(mkt.get("note",""))}</div>
    <div class="mkt-grid">{mkt_cells}</div>
    <div class="story-grid">{mkt_stories}</div>
  </section>

  <section class="sec">
    <div class="sec-title">{tech["title"]}</div>
    <div class="story-grid">{tech_html}</div>
  </section>

  <section class="sec">
    <div class="sec-title">{comp["title"]}</div>
    <div class="story-grid">{comp_html}</div>
  </section>

  <section class="sec watch">
    <div class="sec-title">{watch["title"]} <span class="tag">DEVELOPING, NOT CONFIRMED</span></div>
    <div class="story-grid">{watch_html}</div>
  </section>
</div>
'''
    title = f'{data["edition"]} — {data["displayDate"]} | thisweek.fin'
    desc = data["top3"][1]["headline"] if len(data["top3"]) > 1 else "Daily business and finance news."
    html = HEAD.format(title=esc(title), desc=esc(desc), assets_prefix=assets_prefix) + body + FOOT.format(archive_prefix=archive_prefix)
    return html

def render_archive_index(editions):
    # editions: list of data dicts, sorted desc by date
    months = {}
    for d in editions:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        key = dt.strftime("%B %Y").upper()
        months.setdefault(key, []).append(d)

    blocks = []
    for month, eds in months.items():
        items = ""
        for d in eds:
            dt = datetime.strptime(d["date"], "%Y-%m-%d")
            top_headline = next((t["headline"] for t in d["top3"] if t["position"]=="center"), "")
            items += f'''
        <li>
          <a href="{d["date"]}.html">{dt.strftime("%d %b").upper()} — {dt.strftime("%A").upper()}</a>
          <span class="top-headline">{esc(top_headline)}</span>
        </li>'''
        blocks.append(f'''
      <div class="archive-month">
        <h2>{month}</h2>
        <ul class="archive-list">{items}
        </ul>
      </div>''')

    body = f'''
<div class="masthead">
  <div class="wrap">
    <div class="masthead-row">
      <div class="brand">
        <img src="../assets/logo.png" alt="logo">
        <div class="brand-text">
          <div class="brand-title">THE DAILY</div>
          <div class="brand-sub">THISWEEK.FIN</div>
        </div>
      </div>
      <div class="masthead-meta">ARCHIVE</div>
    </div>
    <div class="nav">
      <a href="../index.html">LATEST</a>
      <a href="index.html" class="active">ARCHIVE</a>
    </div>
  </div>
</div>
<div class="rule-green"></div>
<div class="wrap" style="padding-top:30px;">
  {"".join(blocks)}
</div>
'''
    title = "Archive | THE DAILY — thisweek.fin"
    html = HEAD.format(title=esc(title), desc="Past editions of THE DAILY.", assets_prefix="../") + body + FOOT.format(archive_prefix="../")
    return html

def main():
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.json")), reverse=True)
    editions = []
    for f in files:
        with open(f) as fh:
            editions.append(json.load(fh))

    if not editions:
        print("No editions found in /data.")
        return

    latest = editions[0]

    # Homepage = latest edition
    with open(os.path.join(SITE_DIR, "index.html"), "w") as fh:
        fh.write(render_edition(latest, assets_prefix="", archive_prefix="", is_latest=True))

    # Permanent archive pages — one per edition, never overwritten in content once written
    for d in editions:
        out_path = os.path.join(ARCHIVE_DIR, f'{d["date"]}.html')
        with open(out_path, "w") as fh:
            fh.write(render_edition(d, assets_prefix="../", archive_prefix="../", is_latest=(d["date"]==latest["date"])))

    # Archive index
    with open(os.path.join(ARCHIVE_DIR, "index.html"), "w") as fh:
        fh.write(render_archive_index(editions))

    print(f"Built {len(editions)} edition(s). Homepage = {latest['date']}.")

if __name__ == "__main__":
    main()
