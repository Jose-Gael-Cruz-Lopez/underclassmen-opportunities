#!/usr/bin/env python3
"""
weekly_digest.py — generate a markdown digest of new and closing-soon entries.

Reads README.md, parses every <!-- *_TABLE_START --> ... <!-- *_TABLE_END -->.
Outputs a markdown summary to digest.md with two sections:
  1. New this week (entries with Date Posted in last 7 days)
  2. Closing soon (entries currently flagged 🔥 [CLOSING SOON])

Sets GITHUB_OUTPUT has_content=true if either section is non-empty.
"""

import os
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from closing_soon import CLOSING_SOON_DAYS

PST = ZoneInfo("America/Los_Angeles")
README = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")
DIGEST = os.path.join(os.path.dirname(__file__), "..", "..", "digest.md")

TABLE_RE = re.compile(r"<!-- (\w+)_TABLE_START -->(.*?)<!-- \1_TABLE_END -->", re.DOTALL)
DATE_POSTED_RE = re.compile(r"^([A-Z][a-z]{2})\s+(\d{1,2}),?\s+(\d{4})$")
URL_RE = re.compile(r'href="([^"]+)"')

SECTION_LABELS = {
    "INTERNSHIPS": "Internships",
    "PROGRAMS": "Programs & Fellowships",
    "RESEARCH": "Research",
    "SCHOLARSHIPS": "Scholarships",
    "HBCU": "HBCU",
    "WOMEN": "Women in Tech",
    "RISING_FRESHMEN": "Rising Freshmen",
    "STATE": "State Grants",
}


def parse_date_posted(text: str):
    m = DATE_POSTED_RE.match(text.strip())
    if not m:
        return None
    try:
        return datetime.strptime(
            f"{m.group(1)} {m.group(2)} {m.group(3)}", "%b %d %Y"
        ).replace(tzinfo=PST)
    except ValueError:
        return None


def parse_table(section_key: str, body: str):
    lines = [l for l in body.split("\n") if l.strip().startswith("|")]
    if len(lines) < 3:
        return []

    headers = [h.strip() for h in lines[0].split("|")[1:-1]]
    data_lines = [l for l in lines[1:] if not re.match(r"^\|\s*-+", l.strip())]

    rows = []
    for line in data_lines:
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) != len(headers):
            continue
        row = dict(zip(headers, cells))
        rows.append((section_key, row))
    return rows


def build_row_summary(section_key, row):
    org = (
        row.get("Company")
        or row.get("Organization")
        or row.get("State")
        or row.get("University/Organization")
        or ""
    )
    title_field = (
        row.get("Role")
        or row.get("Program")
        or row.get("Scholarship")
        or row.get("Opportunity")
        or ""
    )
    title = re.sub(r"\s*—\s*Deadline:.*$", "", title_field, flags=re.IGNORECASE).strip()

    application = row.get("Application", "")
    url_m = URL_RE.search(application)
    url = url_m.group(1) if url_m else ""

    deadline_raw = row.get("Deadline") or ""
    if not deadline_raw:
        m = re.search(r"Deadline:\s*([^|]+?)(?:\s*\(Event:|$)", title_field, re.IGNORECASE)
        if m:
            deadline_raw = m.group(1).strip()

    section = SECTION_LABELS.get(section_key, section_key.title())
    line = f"- **[{org} — {title}]({url})** *(_{section}_)*"
    if deadline_raw and deadline_raw not in ("Rolling", "Check site", "—"):
        line += f" — deadline: **{deadline_raw}**"
    return line


def main():
    with open(README, "r") as f:
        content = f.read()

    today = datetime.now(tz=PST)
    cutoff = today - timedelta(days=7)

    all_rows = []
    for m in TABLE_RE.finditer(content):
        all_rows.extend(parse_table(m.group(1), m.group(2)))

    new_rows = []
    closing_rows = []
    for section_key, row in all_rows:
        status = row.get("Status", "")
        if "CLOSED" in status:
            continue

        date_posted_text = row.get("Date Posted") or ""
        if date_posted_text:
            d = parse_date_posted(date_posted_text)
            if d and d >= cutoff:
                new_rows.append((section_key, row))

        if "CLOSING SOON" in status:
            closing_rows.append((section_key, row))

    has_content = bool(new_rows or closing_rows)

    out = []
    out.append(f"# 📬 Weekly Digest — {today.strftime('%B %d, %Y')}\n")
    out.append(
        f"_Auto-generated. Source: [README.md](https://github.com/Jose-Gael-Cruz-Lopez/underclassmen-opportunities)._\n"
    )

    if closing_rows:
        out.append(f"\n## 🔥 Closing soon ({len(closing_rows)})\n")
        out.append(f"Apply now — these deadlines are within {CLOSING_SOON_DAYS} days:\n")
        for s, r in closing_rows:
            out.append(build_row_summary(s, r))

    if new_rows:
        out.append(f"\n## 🆕 New this week ({len(new_rows)})\n")
        out.append("Added in the last 7 days:\n")
        for s, r in new_rows:
            out.append(build_row_summary(s, r))

    if not has_content:
        out.append("\nNo new entries or closing-soon flags this week. Stay tuned 🌱\n")

    out.append(
        f"\n---\n_Want to contribute? [Open an issue](https://github.com/Jose-Gael-Cruz-Lopez/underclassmen-opportunities/issues/new/choose)._"
    )

    with open(DIGEST, "w") as f:
        f.write("\n".join(out))

    print(f"Digest written: {len(closing_rows)} closing soon, {len(new_rows)} new.")
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as f:
            f.write(f"has_content={'true' if has_content else 'false'}\n")
            f.write(f"closing_count={len(closing_rows)}\n")
            f.write(f"new_count={len(new_rows)}\n")


if __name__ == "__main__":
    main()
