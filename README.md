# NBA UI Props — Automation & Deployment

## Automation (GitHub Actions)
- `/.github/workflows/update-data.yml` schedules:
  - PrizePicks odds: every 10 minutes
  - Gamelogs: daily at 7:00 AM
  - DVP data: daily at 7:00 AM
- It runs the existing scripts:
  - `Fetch_PP_Odds.py`, `Fetch_Gamelogs.py` or `Gamelogs.py`, `dvp_parser.py`
  - Rebuilds UI with `UI_DATA_BUILDER_PERFECT.py` + `generate_players.py`
- Commits JSON and generated pages back to `main`.

Dependencies are installed from `requirements.txt`.

## Static Site Deployment (GitHub Pages)
- `/.github/workflows/deploy.yml` publishes the repo root to GitHub Pages on push to `main`.
- Enable GitHub Pages in repository Settings → Pages → Source: `GitHub Actions`.

## Custom Domain
Domain: `cgedge.com`

Already added: `CNAME` file with `cgedge.com` at repo root.

DNS steps:
1. In your DNS provider, create records for `cgedge.com`:
  - If using apex/root domain, add A records pointing to GitHub Pages IPs:
    - 185.199.108.153
    - 185.199.109.153
    - 185.199.110.153
    - 185.199.111.153
  - Optionally add an AAAA record for IPv6: `2606:50c0:8000::153` (and variants if desired).
  - For `www.cgedge.com`, add a CNAME to `<your-username>.github.io`.
2. In the repo Settings → Pages, set Custom domain to `cgedge.com` and enable HTTPS.
3. Wait for DNS propagation, then verify `https://cgedge.com` loads the site.

## Local Development
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python UI_DATA_BUILDER_PERFECT.py
python generate_players.py
python3 -m http.server 5502
```
Open `http://localhost:5502`.

## Notes
- If scripts require API keys, use repo Secrets and read via environment variables.
- Adjust schedules in `update-data.yml` cron fields as needed (UTC timezone).
- If you prefer Netlify/Vercel, point them at the repo and keep GitHub Actions for data refresh.

### Secrets used in Actions
Add these in Settings → Secrets and variables → Actions → New repository secret:
- `PP_API_KEY`: PrizePicks API key (if applicable)
- `PP_API_URL`: PrizePicks API base URL
- `DVP_API_URL`: DVP JSON endpoint
- `BR_USER_AGENT`: Custom UA string for scraping BR safely

Scripts can read them via:
```python
import os
PP_API_KEY = os.environ.get('PP_API_KEY')
PP_API_URL = os.environ.get('PP_API_URL')
DVP_API_URL = os.environ.get('DVP_API_URL')
BR_USER_AGENT = os.environ.get('BR_USER_AGENT', 'Mozilla/5.0')
```

#### Optional secrets/vars
- `PP_LEAGUE_ID`: Defaults to `7` (NBA).
- `GAMELOGS_URL`: If you host a CSV for gamelogs, set the URL here.
- `HTTP_PROXY`: If the PrizePicks API geoblocks CI, set an HTTPS-capable proxy URL; used by `Fetch_PP_Odds.py`.
- `PP_PER_PAGE` / `PP_PAGE` / `PP_SINGLE_STAT`: Tuning params for odds API (strings: e.g. `"500"`, `"1"`, `"true"`).

#### Quick setup via GitHub UI
1) Repo → Settings → Secrets and variables → Actions → New repository secret
2) Add:
  - Name: `PP_API_URL` → Value: `https://api.prizepicks.com/projections` (or your endpoint)
  - Name: `DVP_API_URL` → Value: `<your-dvp-endpoint>.json`
  - Name: `BR_USER_AGENT` → Value: A normal browser UA (e.g., Chrome on macOS)
  - Name: `PP_API_KEY` → Value: Your key/token (if needed for your endpoint)
  - (Optional) `GAMELOGS_URL`, `HTTP_PROXY`, `PP_LEAGUE_ID`, `PP_PER_PAGE`, `PP_PAGE`, `PP_SINGLE_STAT`

#### Optional setup via GitHub CLI (gh)
```bash
gh secret set PP_API_URL --body "https://api.prizepicks.com/projections"
gh secret set DVP_API_URL --body "https://example.com/nba_dvp_latest.json"
gh secret set BR_USER_AGENT --body "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
# If needed
gh secret set PP_API_KEY --body "<your_pp_key>"
# Optional
gh secret set GAMELOGS_URL --body "https://example.com/Full_Gamelogs25.csv"
gh secret set HTTP_PROXY --body "http://user:pass@proxy-host:port"
gh secret set PP_LEAGUE_ID --body "7"
gh secret set PP_PER_PAGE --body "500"
gh secret set PP_PAGE --body "1"
gh secret set PP_SINGLE_STAT --body "true"
```

After adding secrets, you can manually run the workflow:
- GitHub → Actions → "Update NBA UI Data" → "Run workflow"