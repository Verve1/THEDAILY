#!/usr/bin/env python3
"""
Research today's top business/finance news and write data/YYYY-MM-DD.json
for THE DAILY (thisweek.fin), following the confirmed schema.

FREE architecture — no paid API:
  1. Pull real, live headlines from several free public business/finance RSS
     feeds (no API key, no cost).
  2. Send those real headlines + summaries to Groq's free-tier chat API
     (https://console.groq.com — genuinely free tier, no credit card,
     generous rate limits vastly beyond the one call/day this needs) to
     select the most important stories and write them into the exact JSON
     schema. The model is only asked to select/write from facts it was
     given, not to "know" the news itself — RSS is the source of truth.

Run automatically by .github/workflows/daily-edition.yml every weekday
morning. Can also be run manually/locally:

    GROQ_API_KEY=gsk_... python3 scripts/generate_edition.py

Requires: pip install groq feedparser
"""
import json
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import feedparser
from groq import Groq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")

SGT = ZoneInfo("Asia/Singapore")
now_sgt = datetime.now(SGT)
DATE_STR = now_sgt.strftime("%Y-%m-%d")
WEEKDAY = now_sgt.strftime("%A")
DISPLAY_DATE = now_sgt.strftime("%A, %B %d, %Y").upper()

OUT_PATH = os.path.join(DATA_DIR, f"{DATE_STR}.json")

if os.path.exists(OUT_PATH):
    print(f"{OUT_PATH} already exists — refusing to overwrite. Exiting cleanly.")
    sys.exit(0)

# --- Step 1: pull real headlines from free public RSS feeds -----------------
# These are ordinary public RSS feeds, no key required. Feed URLs do move
# occasionally — if one starts failing, swap in a replacement; the loop
# below skips any feed that errors rather than failing the whole run.
FEEDS = [
    "https://finance.yahoo.com/news/rssindex",
    "https://www.cnbc.com/id/10001147/device/rss/rss.html",   # CNBC Business
    "https://www.marketwatch.com/rss/topstories",
    "https://www.investing.com/rss/news_25.rss",               # Investing.com economy news
]

headlines = []
for url in FEEDS:
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:12]:
            headlines.append({
                "title": entry.get("title", "").strip(),
                "summary": re.sub("<[^<]+?>", "", entry.get("summary", "")).strip()[:400],
                "link": entry.get("link", ""),
                "source": feed.feed.get("title", url),
            })
    except Exception as e:
        print(f"Skipping feed {url}: {e}")

if len(headlines) < 5:
    sys.exit(f"Only found {len(headlines)} headlines across all feeds — too few to build an edition. Aborting.")

headlines_blob = "\n\n".join(
    f"- [{h['source']}] {h['title']}\n  {h['summary']}\n  {h['link']}"
    for h in headlines
)

# --- Step 2: use an existing edition as the schema template ------------------
example_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".json"))
if not example_files:
    sys.exit("No existing data/*.json found to use as a schema example.")
with open(os.path.join(DATA_DIR, example_files[-1])) as f:
    SCHEMA_EXAMPLE = f.read()

SYSTEM_PROMPT = f"""You are the editor of THE DAILY, a business/finance newspaper \
(brand: thisweek.fin). You will be given a list of real headlines pulled today from \
public RSS feeds (Yahoo Finance, CNBC, MarketWatch, Investing.com). Use ONLY the facts, \
numbers, and links in that list — do not invent stories, statistics, or URLs that are \
not present in what you were given.

Respond with ONE valid JSON object and NOTHING ELSE — no markdown code fences, no \
commentary before or after. Follow this exact schema (a real past edition — copy its \
structure and field names exactly, only the content changes):

{SCHEMA_EXAMPLE}

Requirements:
- "date": "{DATE_STR}", "weekday": "{WEEKDAY}", "displayDate": "{DISPLAY_DATE}"
- "top3" has exactly 3 items: rank 1 / position "center" is the single most important \
story in the headlines below; rank 2 / position "left" and rank 3 / position "right" \
are the next two most important.
- Every "source" must use a real "name" and "url" taken from the headlines list below \
— never a URL that isn't in that list.
- Match the tone of the example: concise, factual, "why it matters" framing.
- Fill in every section (business, markets, technology, companies, whatToWatch) using \
real items from the list — if the list has too few technology or company stories, keep \
that section shorter rather than inventing content, but never leave "stories" empty.
- For "markets" -> "data", only include index/price figures if they appear explicitly \
in the headlines/summaries below; otherwise omit entries you don't have real numbers for.

TODAY'S REAL HEADLINES:

{headlines_blob}
"""

client = Groq()  # reads GROQ_API_KEY from the environment

response = client.chat.completions.create(
    model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
    max_tokens=8000,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Write today's edition now, as a single JSON object."},
    ],
)

text = response.choices[0].message.content

match = re.search(r"\{.*\}", text, re.DOTALL)
if not match:
    sys.exit(f"No JSON object found in model output:\n\n{text}")

edition = json.loads(match.group(0))

# Belt-and-suspenders: force the date fields regardless of what the model wrote.
edition["date"] = DATE_STR
edition["weekday"] = WEEKDAY
edition["displayDate"] = DISPLAY_DATE

with open(OUT_PATH, "w") as f:
    json.dump(edition, f, indent=2)
    f.write("\n")

print(f"Wrote {OUT_PATH} from {len(headlines)} real headlines across {len(FEEDS)} feeds.")
