#!/usr/bin/env python3
"""
closing_soon.py — flag opportunities closing within 7 days as 🔥 [CLOSING SOON].

Scans every <!-- *_TABLE_START --> ... <!-- *_TABLE_END --> region in README.md.
For each row with status ✅ [OPEN] or 🔥 [CLOSING SOON]:
  - Find the earliest upcoming date in the row
  - If 0–7 days away: flip status to 🔥 [CLOSING SOON]
  - If >7 days away: flip status back to ✅ [OPEN]
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

MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December|"
    "Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
)
DATE_RE = re.compile(rf"\b({MONTHS})\s+(\d{{1,2}}),?\s+(\d{{4}})\b")

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


def update_row(row: str, today: datetime):
    """Return (new_row, changed)."""
    has_open = OPEN in row
    has_closing = CLOSING in row
    if not (has_open or has_closing):
        return row, False
    deadline = earliest_upcoming(row, today)
    if not deadline:
        return row, False
    days_until = (deadline.date() - today.date()).days
    target = CLOSING if 0 <= days_until <= 7 else OPEN
    current = CLOSING if has_closing else OPEN
    if target == current:
        return row, False
    return row.replace(current, target, 1), True


def process_table_body(body: str, today: datetime):
    lines = body.split("\n")
    changed = 0
    for i, line in enumerate(lines):
        if not line.startswith("| "):
            continue
        if "Status |" in line or re.match(r"\|\s*-+", line):
            continue
        new_line, did = update_row(line, today)
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
