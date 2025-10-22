"""
Connect Playwright to the running persistent Chrome session (hybrid mode).
- Assumes Chrome is running with: --remote-debugging-port=9222 and --user-data-dir
- Started via start_hybrid_session.py

This script attaches to the existing Chrome instance using CDP and
interacts with the already-open persistent context (your Chrome profile).
"""

from pathlib import Path
import sys
import time

from playwright.sync_api import sync_playwright

DEBUG_PORT = 9222
CDP_URL = f"http://localhost:{DEBUG_PORT}"


def ensure_output_dir() -> Path:
    out_dir = Path("data") / "data_output" / "run_summary"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def connect_and_probe():
    print("Connecting Playwright to existing Chrome over CDP...")
    with sync_playwright() as pw:
        # Attach to the running Chrome instance
        browser = pw.chromium.connect_over_cdp(CDP_URL)
        print("✓ Connected to Chrome via CDP")

        contexts = browser.contexts
        if not contexts:
            print("✗ No browser contexts found. Make sure Chrome was started with remote debugging and a user-data-dir.")
            sys.exit(1)

        # When Chrome is started with a user-data-dir, the persistent context will appear here
        context = contexts[0]
        print(f"Found {len(contexts)} context(s). Using the first persistent context.")

        # If a page is already open (e.g., started URL), reuse it. Otherwise create one.
        page = context.pages[0] if context.pages else context.new_page()

        try:
            print(f"Attached to page. URL: {page.url}")
        except Exception:
            print("Page has no URL yet (about:blank). Navigating to example page...")
            page.goto("https://example.com")

        # Probe the page (get title)
        title = page.title()
        print(f"Page title: {title}")

        # Take a screenshot to confirm attachment
        out_dir = ensure_output_dir()
        shot_path = out_dir / "playwright_connected.png"
        page.screenshot(path=str(shot_path))
        print(f"Screenshot saved to: {shot_path}")

        # Do not close the browser; we only detach when script ends
        print("Playwright successfully attached to your persistent Chrome session.")
        print("You can keep interacting via this script or extend it as needed.")


if __name__ == "__main__":
    try:
        connect_and_probe()
    except Exception as e:
        print(f"ERROR: Failed to connect or interact with Chrome: {e}")
        print("Hint: Ensure Chrome is running with --remote-debugging-port=9222 (start_hybrid_session.py)")
        sys.exit(1)
