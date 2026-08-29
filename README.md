# THE DAILY — thisweek.fin

Automated daily business & finance newspaper. Static site, no backend, no database.

## Structure
```
data/YYYY-MM-DD.json   <- one file per edition. NEVER edit or delete past editions.
site/                  <- generated output (do not hand-edit; regenerate instead)
  index.html           <- latest edition = homepage
  archive/index.html   <- archive listing by month
  archive/YYYY-MM-DD.html  <- permanent per-day edition page
  styles.css
  assets/logo.png
generate.py             <- builds site/ from data/*.json
generate_artifacts.py   <- builds self-contained single-file versions for Claude Artifacts (inlines CSS + logo)
```

## Daily workflow
1. Research the day's top business/finance stories (Reuters, Bloomberg, WSJ, FT, primary sources, SEC filings, company IR pages).
2. Write a new `data/YYYY-MM-DD.json` following the schema in an existing file — do not overwrite yesterday's file.
3. Run `python3 generate.py` — rebuilds index.html + appends a new archive page + rebuilds the archive index. Old archive pages are untouched.
4. Deploy `site/` (see below).

## Deploying to a real public URL
This is a static site — any static host works. Simplest options:

**Vercel** (recommended, free tier, custom domain support)
```
npm i -g vercel
cd site
vercel --prod
```

**Netlify**
```
npm i -g netlify-cli
cd site
netlify deploy --prod --dir .
```

**GitHub Pages**
```
# from the daily/ folder
git init
git add site
git subtree push --prefix site origin gh-pages   # or use a GitHub Action to publish site/ on push
```
Then enable Pages on the `gh-pages` branch (or `/site` folder) in repo settings.

Any of these gives a permanent URL you can put in your Instagram bio / social profile. Point a custom domain (e.g. daily.thisweek.fin) at it once you're happy with it.

## Automating the daily refresh
Two options, in increasing order of autonomy:

1. **Manual-trigger, Claude-assisted (safest, recommended to start):** each morning, message this Claude session (or a scheduled Claude task) "run today's edition." Claude researches, writes the new JSON, runs generate.py, and — per your approval-gate preference — shows you the draft before it goes live. You approve, then it deploys (`vercel --prod` / `netlify deploy --prod` / git push).
2. **Fully automated:** a scheduled task (cron / GitHub Action / Vercel Cron) triggers a script every morning that calls an LLM with web search to research + write the JSON, runs generate.py, and auto-deploys. No approval gate — only turn this on once you trust the output quality.

Do not enable (2) until you've reviewed several editions produced by (1).
