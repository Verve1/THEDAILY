#!/usr/bin/env python3
"""
Builds self-contained single-file HTML pages for Artifact publishing:
  artifact_home.html     -> the live homepage (latest edition)
  artifact_archive.html  -> all editions, stacked with anchors, newest first
No <html>/<head>/<body>/doctype tags (Artifact wraps the page).
CSS inlined, logo embedded as base64 data URI.
"""
import json, glob, os
from datetime import datetime
import generate as g  # reuse block builders

ROOT = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(ROOT, "site", "styles.css")) as f:
    CSS = f.read()

with open("/tmp/logo_b64.txt") as f:
    LOGO_B64 = f.read().strip()
LOGO_DATA_URI = f"data:image/png;base64,{LOGO_B64}"

ARCHIVE_URL_PLACEHOLDER = "__ARCHIVE_URL__"
HOME_URL_PLACEHOLDER = "__HOME_URL__"

def edition_body(data, home_href, archive_href, anchor_id=None, show_nav=True):
    top3_sorted = sorted(data["top3"], key=lambda x: {"left":0,"center":1,"right":2}[x["position"]])
    top3_html = "".join(g.top3_block(i) for i in top3_sorted)
    biz = data["sections"]["business"]; mkt = data["sections"]["markets"]
    tech = data["sections"]["technology"]; comp = data["sections"]["companies"]; watch = data["sections"]["whatToWatch"]
    biz_html = "".join(g.story_html(s) for s in biz["stories"])
    tech_html = "".join(g.story_html(s) for s in tech["stories"])
    comp_html = "".join(g.story_html(s) for s in comp["stories"])
    watch_html = "".join(g.story_html(s) for s in watch["stories"])
    mkt_cells = "".join(g.market_cell(m) for m in mkt["data"])
    mkt_stories = "".join(g.story_html(s) for s in mkt.get("stories", []))
    anchor = f'id="{anchor_id}"' if anchor_id else ""
    nav = f'''
    <div class="nav">
      <a href="{home_href}">LATEST</a>
      <a href="{archive_href}">ARCHIVE</a>
    </div>''' if show_nav else ""

    return f'''
<div class="masthead" {anchor}>
  <div class="wrap">
    <div class="masthead-row">
      <div class="brand">
        <img src="{LOGO_DATA_URI}" alt="logo">
        <div class="brand-text">
          <div class="brand-title">{g.esc(data["edition"])}</div>
          <div class="brand-sub">THISWEEK.FIN</div>
        </div>
      </div>
      <div class="masthead-meta">BUSINESS &amp; FINANCE, DAILY<br><span class="date">{g.esc(data["displayDate"])}</span></div>
    </div>{nav}
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
    <div class="mkt-note">{g.esc(mkt.get("note",""))}</div>
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
</div>'''

def build_home(latest, archive_href):
    body = edition_body(latest, home_href="#", archive_href=archive_href)
    footer = f'''
<footer>
  <div class="wrap">
    <div>
      <div class="fbrand">THE DAILY — THISWEEK.FIN</div>
      <div class="disclaimer">Business and finance news, edited daily. Figures verified against primary and wire sources at time of publication; market data is a point-in-time snapshot, not investment advice. Corrections: contact via thisweek.fin.</div>
    </div>
    <div><a href="{archive_href}">Full Archive &rarr;</a></div>
  </div>
</footer>'''
    return f'<title>THE DAILY — thisweek.fin</title>\n<style>{CSS}</style>\n' + body + footer

def build_archive(editions, home_href):
    # editions sorted desc by date already
    months = {}
    for d in editions:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        key = dt.strftime("%B %Y").upper()
        months.setdefault(key, []).append(d)
    index_blocks = []
    for month, eds in months.items():
        items = ""
        for d in eds:
            dt = datetime.strptime(d["date"], "%Y-%m-%d")
            top_headline = next((t["headline"] for t in d["top3"] if t["position"]=="center"), "")
            items += f'''
        <li><a href="#ed-{d["date"]}">{dt.strftime("%d %b").upper()} — {dt.strftime("%A").upper()}</a>
        <span class="top-headline">{g.esc(top_headline)}</span></li>'''
        index_blocks.append(f'<div class="archive-month"><h2>{month}</h2><ul class="archive-list">{items}</ul></div>')

    header = f'''
<div class="masthead">
  <div class="wrap">
    <div class="masthead-row">
      <div class="brand">
        <img src="{LOGO_DATA_URI}" alt="logo">
        <div class="brand-text">
          <div class="brand-title">THE DAILY</div>
          <div class="brand-sub">THISWEEK.FIN</div>
        </div>
      </div>
      <div class="masthead-meta">ARCHIVE</div>
    </div>
    <div class="nav"><a href="{home_href}">LATEST</a><a href="#" class="active">ARCHIVE</a></div>
  </div>
</div>
<div class="rule-green"></div>
<div class="wrap" style="padding-top:30px;">{"".join(index_blocks)}</div>
<div style="height:1px;background:#1f1f1f;margin:10px 0 0;"></div>'''

    editions_html = ""
    for d in editions:
        editions_html += edition_body(d, home_href=home_href, archive_href="#", anchor_id=f"ed-{d['date']}", show_nav=False)
        editions_html += '<div style="height:2px;background:#0a0a0a;margin:0 0 0;"></div>'

    footer = f'''
<footer>
  <div class="wrap">
    <div>
      <div class="fbrand">THE DAILY — THISWEEK.FIN</div>
      <div class="disclaimer">Every past edition, permanently archived. Nothing here is overwritten — new editions are appended.</div>
    </div>
    <div><a href="{home_href}">Latest Edition &rarr;</a></div>
  </div>
</footer>'''

    return f'<title>Archive | THE DAILY — thisweek.fin</title>\n<style>{CSS}</style>\n' + header + editions_html + footer

def main():
    files = sorted(glob.glob(os.path.join(ROOT, "data", "*.json")), reverse=True)
    editions = [json.load(open(f)) for f in files]
    latest = editions[0]

    home_html = build_home(latest, archive_href=ARCHIVE_URL_PLACEHOLDER)
    with open(os.path.join(ROOT, "artifact_home.html"), "w") as f:
        f.write(home_html)

    archive_html = build_archive(editions, home_href=HOME_URL_PLACEHOLDER)
    with open(os.path.join(ROOT, "artifact_archive.html"), "w") as f:
        f.write(archive_html)

    print("Built artifact_home.html and artifact_archive.html")

if __name__ == "__main__":
    main()
