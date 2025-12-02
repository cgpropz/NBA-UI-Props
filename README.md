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