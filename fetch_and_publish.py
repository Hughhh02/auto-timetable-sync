def login_and_download_via_playwright() -> bytes:
    """
    SIT SSO-friendly: if a saved storage state exists, reuse it and skip any form typing.
    Only fall back to manual login (via save_sso_session.py) if storage is missing.
    """
    headless = os.getenv("HEADLESS", "1") != "0"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)

        # Reuse storage state (cookies) if present; this is key for SSO/MFA.
        if STORAGE_PATH.exists():
            ctx = browser.new_context(accept_downloads=True, storage_state=str(STORAGE_PATH))
        else:
            # We don't want to attempt auto-typing into SSO forms; require session first.
            browser.close()
            raise RuntimeError(
                "No saved SSO session found. Run 'python save_sso_session.py', complete SSO/MFA, "
                "and try again."
            )

        page = ctx.new_page()

        # Go straight to the page that has the ICS export button/link if provided
        target = PORTAL_POST_LOGIN_URL or "about:blank"
        page.goto(target, timeout=120000)
        page.wait_for_load_state("networkidle", timeout=60000)

        # Click the ICS export and capture the download
        if not ICS_DOWNLOAD_SELECTOR:
            browser.close()
            raise RuntimeError("ICS_DOWNLOAD_SELECTOR is empty. Set it in your .env.")

        # Optional: give the page a moment to render any SPA content
        try:
            page.wait_for_timeout(800)
        except Exception:
            pass

        with page.expect_download(timeout=60000) as dl_info:
            if ICS_DOWNLOAD_SELECTOR.startswith("text="):
                page.get_by_text(ICS_DOWNLOAD_SELECTOR.replace("text=", "")).click()
            else:
                page.click(ICS_DOWNLOAD_SELECTOR)
        download = dl_info.value
        ics_bytes = download.content()
        browser.close()
        return ics_bytes
