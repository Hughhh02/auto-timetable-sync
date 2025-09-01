\
"""
Run this locally ONCE to capture your SIT SSO session (cookies) after MFA.
It saves Playwright storage state to auth/sit_storage.json.
Subsequent scheduled runs can reuse this storage to fetch the ICS headlessly.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

# Set to the page where your ICS export button/link is visible after login
TIMETABLE_LANDING_URL = (
    # Example placeholder; replace with your actual landing page after SSO
    "https://in4sit.singaporetech.edu.sg/"
)

STORAGE_PATH = Path("auth/sit_storage.json")
STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=150)
        ctx = browser.new_context()  # no storage initially
        page = ctx.new_page()

        print("Opening SIT portal; complete SSO + MFA manually, then press ENTER in this terminal.")
        page.goto(TIMETABLE_LANDING_URL, timeout=120000)

        # Give user time to log in; they will press Enter in terminal when finished.
        input("After you see your timetable/dashboard, press ENTER here to save session...")

        ctx.storage_state(path=str(STORAGE_PATH))
        print(f"[ok] Saved storage state to {STORAGE_PATH.resolve()}")
        browser.close()

if __name__ == "__main__":
    main()
