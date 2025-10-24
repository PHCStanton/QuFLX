"""
Connect Playwright to the already running persistent Chrome session and
focus or navigate to a specific site URL.

Usage (PowerShell):
  python connect_site.py "https://mgx.dev/chat/de193f6b288d4edaad941d690ea4b798"

Assumptions:
- Chrome is already running with --remote-debugging-port=9222 and a user-data-dir
  (start via start_hybrid_session.py)
- Your login/session state lives in that persistent profile, so Playwright
  will attach and reuse it.
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

DEBUG_PORT = int(os.environ.get("CHROME_DEBUG_PORT", "9222"))
CDP_URL = f"http://localhost:{DEBUG_PORT}"


def ensure_output_dir() -> Path:
    out_dir = Path("data") / "data_output" / "run_summary"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def sanitize_filename(url: str) -> str:
    parsed = urlparse(url)
    safe = f"{parsed.netloc}{parsed.path}".replace("/", "_")
    return "target_" + "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in safe)
def connect_and_focus(url: str):
    print(f"Connecting Playwright to Chrome via CDP at {CDP_URL}...")
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(CDP_URL)
        print("✓ Connected to Chrome")

        if not browser.contexts:
            print("✗ No contexts found. Ensure Chrome was started with a user-data-dir.")
            sys.exit(1)

        context = browser.contexts[0]
        pages = context.pages

        # Try to find an existing page that matches the target URL (prefix or exact match)
        target_page = None
        for p in pages:
            try:
                if p.url.startswith(url) or url.startswith(p.url):
                    target_page = p
                    break
            except Exception:
                # Some pages may not have a valid URL yet
                continue

        if target_page is None:
            print("No existing tab for target URL found; opening a new page...")
            target_page = context.new_page()
            target_page.goto(url)
        else:
            print(f"Found existing tab: {target_page.url}")
            try:
                target_page.bring_to_front()
            except Exception:
                pass

        # Wait for the DOM to be ready (best-effort)
        try:
            target_page.wait_for_load_state("domcontentloaded", timeout=5000)
        except PlaywrightTimeoutError:
            print("DOM did not reach 'domcontentloaded' within timeout; proceeding.")

        # Collect basic info and take a screenshot
        title = "(unknown)"
        try:
            title = target_page.title()
        except Exception:
            pass
        print(f"Page title: {title}")

        out_dir = ensure_output_dir()
        shot_name = sanitize_filename(url) + ".png"
        shot_path = out_dir / shot_name
        try:
            target_page.screenshot(path=str(shot_path), full_page=False)
            print(f"Screenshot saved: {shot_path}")
        except Exception as e:
            print(f"Screenshot failed: {e}")

        print("Playwright attached and focused the requested site.")
if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to the URL you provided if none is passed
        default_url = "https://mgx.dev/chat/de193f6b288d4edaad941d690ea4b798"
        print("No URL argument provided; using default:")
        print(default_url)
        target_url = default_url
    else:
        target_url = sys.argv[1]

    try:
        connect_and_focus(target_url)
    except Exception as e:
        print(f"ERROR: Could not connect or focus the site: {e}")
        print("Hint: Make sure Chrome is running via start_hybrid_session.py and remote debugging is enabled on port 9222.")
        sys.exit(1)
