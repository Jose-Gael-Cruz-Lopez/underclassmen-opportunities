#!/usr/bin/env python3
"""
closing_soon.py — flag opportunities closing within 14 days as 🔥 [CLOSING SOON].

Scans every <!-- *_TABLE_START --> ... <!-- *_TABLE_END --> region in README.md.
For each row with status ✅ [OPEN] or 🔥 [CLOSING SOON]:
  - Find the earliest upcoming date in the row
  - If 0–14 days away: flip status to 🔥 [CLOSING SOON]
  - If >14 days away: flip status back to ✅ [OPEN]
  - If unparseable / past / Rolling / Check site: leave alone

[OPENS SOON] and [CLOSED] rows are never modified.
Idempotent — safe to run daily.
"""

import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

PST = ZoneInfo("America/Los_Angeles")
README = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")

OPEN = "✅ **[OPEN]**"
CLOSING = "🔥 **[CLOSING SOON]**"

# Deadlines this many days out (or fewer) get the 🔥 badge.
# Keep in sync with the weekly audit runbook, which uses the same window.
# weekly_digest.py imports this constant for its "closing soon" copy.
CLOSING_SOON_DAYS = 14

MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December|"
    "Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
)
# Matches "Aug 15, 2026" and also day ranges like "Oct 28–31, 2026", where the
# range's START day is captured — an event running Oct 28–31 should start
# flagging on Oct 14, not Oct 17. Cross-month ranges ("Sep 15–Dec 15, 2026")
# still match only their trailing date, which is the intended end-of-window.
DATE_RE = re.compile(
    rf"\b({MONTHS})\.?\s+(\d{{1,2}})(?:\s*[–—-]\s*\d{{1,2}})?,?\s+(\d{{4}})\b"
)

TABLE_RE = re.compile(r"(<!-- \w+_TABLE_START -->)(.*?)(<!-- \w+_TABLE_END -->)", re.DOTALL)


def parse_date(month: str, day: str, year: str):
    """Return a datetime or None."""
    m = month.replace(".", "")
    if m == "Sept":
        m = "Sep"
    for fmt in ("%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(f"{m} {day} {year}", fmt).replace(tzinfo=PST)
        except ValueError:
            continue
    return None


def earliest_upcoming(text: str, today: datetime):
    """Find earliest date in text that is >= today's date. None if none found."""
    upcoming = []
    for m in DATE_RE.finditer(text):
        d = parse_date(m.group(1), m.group(2), m.group(3))
        if d and d.date() >= today.date():
            upcoming.append(d)
    return min(upcoming) if upcoming else None


def date_posted_index(body: str):
    """Column index of the 'Date Posted' header in this table, or None.

    That column holds the day a listing was added, which is NOT a deadline.
    A row added today would otherwise look like it closes in 0 days.
    """
    for line in body.split("\n"):
        if line.startswith("| ") and "Status" in line:
            cells = [c.strip().lower() for c in line.strip().strip("|").split("|")]
            return cells.index("date posted") if "date posted" in cells else None
    return None


def strip_column(row: str, index):
    """Row text with the given cell removed, for date scanning."""
    if index is None:
        return row
    cells = row.strip().strip("|").split("|")
    if index < len(cells):
        cells = cells[:index] + cells[index + 1:]
    return "|".join(cells)


def update_row(row: str, today: datetime, skip_index=None):
    """Return (new_row, changed)."""
    has_open = OPEN in row
    has_closing = CLOSING in row
    if not (has_open or has_closing):
        return row, False
    deadline = earliest_upcoming(strip_column(row, skip_index), today)
    if not deadline:
        return row, False
    days_until = (deadline.date() - today.date()).days
    target = CLOSING if 0 <= days_until <= CLOSING_SOON_DAYS else OPEN
    current = CLOSING if has_closing else OPEN
    if target == current:
        return row, False
    return row.replace(current, target, 1), True


def process_table_body(body: str, today: datetime):
    lines = body.split("\n")
    skip = date_posted_index(body)
    changed = 0
    for i, line in enumerate(lines):
        if not line.startswith("| "):
            continue
        if "Status |" in line or re.match(r"\|\s*-+", line):
            continue
        new_line, did = update_row(line, today, skip)
        if did:
            lines[i] = new_line
            changed += 1
    return "\n".join(lines), changed


def main():
    with open(README, "r") as f:
        content = f.read()

    today = datetime.now(tz=PST)
    total = 0

    def replace(m):
        nonlocal total
        new_body, n = process_table_body(m.group(2), today)
        total += n
        return m.group(1) + new_body + m.group(3)

    new_content = TABLE_RE.sub(replace, content)

    if new_content != content:
        with open(README, "w") as f:
            f.write(new_content)

    print(f"Updated {total} row(s).")
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as f:
            f.write(f"changes={total}\n")


if __name__ == "__main__":
    main()
