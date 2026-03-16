#!/usr/bin/env python3
"""
Conference ticket checker.
Monitors a list of URLs for 'Early Bird' text and alerts when page content changes.

Usage:
    python3 check_conferences.py

Add your URLs to the URLS list below.
Snapshots are saved in ./snapshots/
Audit log is written to ./audit_log.txt
Alerts are delivered as native macOS desktop notifications.
"""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Optional, List, Dict
from playwright.sync_api import sync_playwright

# --- Configuration ---
URLS = [
    "https://uxdx.com/",
    "https://config.figma.com/",
    "https://smashingconf.com/conferences/",
    "https://www.hatchconference.com/",
    "https://worldusabilitycongress.com/",
    "https://uxbri.org/",
    "https://leadingdesign.com/",
    "https://www.uxcon.io/",
    "https://www.uxconference.org/",
    "https://uxpa.org/",
    "https://www.aiga.org/design/aiga-design-conference",
    "https://designmatters.io/",
    "https://push-conference.com/",
    "https://2025.ux-india.org/",
    "https://www.uxyall.org/",
    "https://sxsw.com/",
    "https://rosenfeldmedia.com/designops-summit/",
    "https://sdn-youngtalentboard.org/conference/",
    "https://vancouver.websummit.com/",
    "https://websummit.com/",
    "https://afrotechconference.com/",
    "https://developer.apple.com/",
    "https://io.google/",
    "https://2026.uxlondon.com/",
    "https://www.renderatl.com/",
    "https://canux.io/",
    "https://merlien.com/",
    "https://www.qrca.org/",
    "https://rosenfeldmedia.com/advancing-research/",
    "https://thequirksevent.com/",
    "https://joinlearners.com/research-week/",
    "https://epicpeople.org",
    "https://www.designup.io",
    "https://ifdesign.com/",
    "https://www.clarityconf.com/",
]

SNAPSHOT_DIR = "snapshots"
EARLY_BIRD_KEYWORD = "Early Bird"

AUDIT_LOG = "audit_log.txt"
# ---------------------


def slugify(url: str) -> str:
    """Turn a URL into a safe filename."""
    return hashlib.md5(url.encode()).hexdigest()


def snapshot_path(url: str) -> str:
    return os.path.join(SNAPSHOT_DIR, f"{slugify(url)}.json")


def load_snapshot(url: str) -> Optional[dict]:
    path = snapshot_path(url)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def save_snapshot(url: str, text: str) -> None:
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    data = {
        "url": url,
        "text": text,
        "captured_at": datetime.now().isoformat(),
    }
    with open(snapshot_path(url), "w") as f:
        json.dump(data, f, indent=2)


def log_audit(checked: List[str], alerts: List[Dict]) -> None:
    """Append a run summary to audit_log.txt."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(AUDIT_LOG, "a") as f:
        f.write(f"[{timestamp}] Checked {len(checked)} URL(s). "
                f"Alerts: {len(alerts)}\n")
        for result in alerts:
            tag = f"EARLY BIRD + CHANGED" if result["has_early_bird"] and result["changed"] \
                else "EARLY BIRD" if result["has_early_bird"] \
                else "CHANGED"
            f.write(f"  [{tag}] {result['url']}\n")


def notify(title: str, message: str) -> None:
    """Send a native macOS desktop notification via osascript."""
    script = (
        f'display notification "{message}" '
        f'with title "{title}" '
        f'sound name "Default"'
    )
    try:
        subprocess.run(["osascript", "-e", script], check=True)
    except Exception as e:
        print(f"  [NOTIFY] Failed to send notification: {e}")


def print_alert(url: str, has_early_bird: bool) -> None:
    width = 72
    border = "!" * width
    print()
    print(border)
    print(border)
    label = "  EARLY BIRD DETECTED  " if has_early_bird else "  PAGE CONTENT CHANGED  "
    print(f"{'!' * 4}{label.center(width - 8)}{'!' * 4}")
    print(f"  URL: {url}")
    if has_early_bird:
        print(f"  '{EARLY_BIRD_KEYWORD}' text found on this page!")
    print(f"  Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(border)
    print(border)
    print()


def check_url(page, url: str) -> dict:
    """Load a URL with Playwright, extract text, compare to snapshot."""
    result = {"url": url, "changed": False, "has_early_bird": False, "error": None}

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        # Wait a moment for any JS-rendered content to settle
        page.wait_for_timeout(2000)
        text = page.inner_text("body")
    except Exception as e:
        result["error"] = str(e)
        print(f"  [ERROR] Could not load {url}: {e}")
        return result

    result["has_early_bird"] = EARLY_BIRD_KEYWORD.lower() in text.lower()

    previous = load_snapshot(url)
    if previous is None:
        print(f"  [NEW]  First snapshot saved for {url}")
    elif previous["text"] != text:
        result["changed"] = True

    save_snapshot(url, text)
    return result


def main() -> None:
    if not URLS:
        print("No URLs configured. Edit the URLS list in check_conferences.py.")
        sys.exit(1)

    print(f"\nChecking {len(URLS)} URL(s) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    alerts = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Identify as a regular browser to avoid basic bot blocks
        page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})

        for url in URLS:
            print(f"  Checking: {url}")
            result = check_url(page, url)

            if result["error"]:
                continue

            if result["has_early_bird"]:
                print(f"    -> '{EARLY_BIRD_KEYWORD}' FOUND")
            else:
                print(f"    -> '{EARLY_BIRD_KEYWORD}' not found")

            if result["changed"]:
                print(f"    -> Content has CHANGED since last run")
            else:
                print(f"    -> No change since last run")

            if result["has_early_bird"] or result["changed"]:
                alerts.append(result)

        browser.close()

    print("-" * 60)

    if alerts:
        for result in alerts:
            print_alert(result["url"], result["has_early_bird"])
            tag = "Early Bird detected!" if result["has_early_bird"] else "Page content changed"
            notify("Conference Bot Alert", f"{tag}\n{result['url']}")
    else:
        print("No changes detected and no Early Bird text found.")

    log_audit(URLS, alerts)
    print(f"\nSnapshots saved to ./{SNAPSHOT_DIR}/\n")
    print(f"Audit log updated: ./{AUDIT_LOG}")


if __name__ == "__main__":
    main()
