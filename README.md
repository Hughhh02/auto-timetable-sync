# Auto Timetable Sync (ICS → Always Up-to-Date)

This project keeps your class timetable **always up to date** by fetching the latest `.ics` file on a schedule and republishing it to a stable URL you can subscribe to in Google Calendar, Apple Calendar, or Outlook.

## Why this works
Many school portals only let you export an ICS **once**, and the export quickly goes stale as classes move. This tool fetches (or logs in and downloads) the latest ICS on a schedule and **mirrors** it to `public/calendar.ics`. If you host this repo with **GitHub Pages**, you get a stable public URL that your calendar app can auto-refresh.

---

## Two ways to fetch your ICS

### 1) PUBLIC_ICS_URL (simplest — if your ICS has a stable, unauthenticated URL)
- Example: `https://my.school.edu/timetable/export.ics?studentId=123`
- The workflow will `GET` that URL on a schedule and publish the result.

### 2) PLAYWRIGHT_LOGIN (use if your portal requires login)
- We use **Playwright** headless browser to log in and click the portal's “Export/Download ICS” button.
- You must fill in: login URL, username/password, and a CSS selector or link text for the ICS download.
- The downloaded file is saved as `public/calendar.ics`.

> **Privacy note:** Publishing your ICS to GitHub Pages exposes event details publicly. If you need privacy, consider hosting the mirrored ICS on your own device/server and subscribe to `http://your-ip:8000/calendar.ics`, or deploy to a private server/Nextcloud and subscribe via its public share link that you control.

---

## Quick Start (Public ICS URL)

1. **Create a new GitHub repository** and push this project.
2. Enable **GitHub Pages** for the repo (Settings → Pages → Build from branch → `main` / `/root`).
3. In your repo, go to **Settings → Secrets and variables → Actions → New repository secret**, and add:
   - `PUBLIC_ICS_URL` = your school ICS URL
4. Commit/push. The workflow runs every 2 hours by default and republishes to `public/calendar.ics`.
5. Your subscribe URL will be:
   - `https://<your-username>.github.io/<repo-name>/calendar.ics`
6. Subscribe to that URL in Google Calendar (Add → From URL) or Apple Calendar (File → New Calendar Subscription).

### Switch to Playwright Login (if needed)

1. Add these **secrets** in GitHub:
   - `FETCH_MODE` = `PLAYWRIGHT_LOGIN`
   - `PORTAL_LOGIN_URL` = the login page URL, e.g., `https://portal.my.school.edu/login`
   - `PORTAL_USERNAME` = your username
   - `PORTAL_PASSWORD` = your password
   - `ICS_DOWNLOAD_SELECTOR` = a CSS selector for the ICS download button or link once logged in
     - Example: `a#export-ics` or `a.download-ics` or `text=Export .ics` (text selector also works)
2. In `fetch_and_publish.py`, optionally tweak the navigation steps (see `login_and_download_via_playwright()`).
3. Commit/push — the workflow will use Playwright to log in headlessly and save the ICS.

---

## Local development / private hosting (keeps ICS private)

If you prefer to keep the ICS private, run it locally on a laptop or a Raspberry Pi and expose only the ICS file:

```bash
# 1) Create a .env file (see .env.example)
cp .env.example .env

# 2) Install deps
pip install -r requirements.txt
playwright install chromium

# 3) Run a one-shot fetch (public URL mode)
python fetch_and_publish.py

# Or run as a simple HTTP server on your LAN so Google Calendar can subscribe:
python -m http.server --directory public 8000
# Subscribe to: http://<your-ip>:8000/calendar.ics  (Note: Google Calendar must access it from the internet)
```

You can put this in a `cron` (Linux/macOS) or Task Scheduler (Windows) to run every few hours.

---

## Folder structure

```
public/
  └── calendar.ics   # mirrored timetable (output)
fetch_and_publish.py # main script: fetch → publish
.github/workflows/update.yml # runs every 2 hours on GitHub Actions
```

---

## Advanced (merge / transform events)
Out of the box we **mirror** the ICS as-is. If you want to filter, rename or merge events (e.g., only module code, move campus to location), see `transform_ics()` in `fetch_and_publish.py`. It's a single function where you can rewrite event fields using Python.

---

## Troubleshooting

- **Google Calendar not updating?** It can take several hours for Google to refresh ICS feeds. You can force an update by changing the subscribed URL (e.g., append `?v=<timestamp>`), but it will still honor its internal cache windows.
- **Portal behind VPN/SSO?** Use the Playwright mode on a server that has access, or run locally on a machine that can log in, then host the mirrored ICS yourself.
- **Playwright selector not found?** In your browser DevTools, right-click the ICS export link and copy a CSS selector **or** use text selectors like `text="Export timetable"`.
- **Private data on GitHub Pages?** Consider a private self-hosted option or a Nextcloud instance with a password-protected public link.


---

## SIT SSO (works with MFA)

SIT uses SSO/MFA, so automated username+password in CI usually isn't enough. Use a **storage-state** approach:

### Option A — Local + Private (recommended)
1. Install deps and Playwright browsers:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
2. Run the interactive saver and complete SSO/MFA in the real browser window:
   ```bash
   python save_sso_session.py
   ```
   This saves `auth/sit_storage.json` (cookies/session).  
3. Edit `.env`:
   ```env
   FETCH_MODE=PLAYWRIGHT_LOGIN
   PORTAL_POST_LOGIN_URL=https://myportal.singaporetech.edu.sg/   # or your timetable page
   ICS_DOWNLOAD_SELECTOR=text=Export .ics   # or your real selector
   ```
4. Test one-shot fetch:
   ```bash
   python fetch_and_publish.py
   ```
5. Automate with cron/Task Scheduler on the same machine (so the session stays valid).

### Option B — GitHub Actions with storage state
1. Base64 the storage file created locally:
   ```bash
   base64 -w0 auth/sit_storage.json > storage.b64
   ```
2. Add a GitHub secret `STORAGE_STATE_B64` with the base64 content.
3. In the workflow, before running the script, reconstruct the file:
   ```yaml
   - name: Restore storage state
     if: ${{ secrets.STORAGE_STATE_B64 != '' }}
     run: |
       mkdir -p auth
       echo "${{ secrets.STORAGE_STATE_B64 }}" | base64 -d > auth/sit_storage.json
   ```
4. Set secrets:
   - `FETCH_MODE=PLAYWRIGHT_LOGIN`
   - `PORTAL_POST_LOGIN_URL=https://myportal.singaporetech.edu.sg/` (or your timetable page)
   - `ICS_DOWNLOAD_SELECTOR` e.g. `text=Export .ics` or a precise CSS selector for the export button/link

> Note: Cookies expire occasionally. If the job fails with 401/redirect to login, run `save_sso_session.py` again and update the secret.

### Finding the ICS selector
- Open DevTools on your timetable page after login.
- Right-click the “Export iCal/ICS” button → Copy selector.
- Try simple **text selectors** first, e.g., `text=Export iCal`, `text=Download .ics`.
- Paste that into `ICS_DOWNLOAD_SELECTOR`.

