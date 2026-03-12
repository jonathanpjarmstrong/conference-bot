# Conference Bot

Monitors conference websites for ticket updates and Early Bird pricing. Sends a native macOS desktop notification and logs every check to a local audit file.

## Features

- Detects "Early Bird" text on any page
- Alerts when page content changes between runs
- Native macOS desktop notifications (no external services)
- Audit log with a timestamped record of every run
- Runs headlessly via Playwright + Chromium

## Setup

1. Install dependencies:
   ```bash
   pip3 install playwright
   python3 -m playwright install chromium
   ```

2. Add your URLs to the `URLS` list in `check_conferences.py`:
   ```python
   URLS = [
       "https://example-conference.com/tickets",
   ]
   ```

3. Run manually:
   ```bash
   python3 check_conferences.py
   ```

## Automated scheduling

A cron job runs the script every Monday at 9:00 AM. To set it up:

```bash
crontab -e
```

Add this line:
```
0 9 * * 1 /usr/bin/python3 /Users/jonathanarmstrong/conference-bot/check_conferences.py >> /Users/jonathanarmstrong/conference-bot/cron.log 2>&1
```

## Output files

| File | Description |
|------|-------------|
| `snapshots/` | Per-URL page text snapshots (JSON) |
| `audit_log.txt` | Timestamped record of every run |
| `cron.log` | stdout/stderr from scheduled runs |

Both `snapshots/` and `audit_log.txt` are excluded from version control via `.gitignore`.
