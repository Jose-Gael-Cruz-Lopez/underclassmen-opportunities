#!/usr/bin/env python3
"""
lint_tables.py — structural linter for the opportunity tables.

Checks README.md (marker-delimited regions) and ARCHIVE.md (## sections) for the
formatting mistakes that silently break GitHub's markdown table rendering or the
web app's parser:

  - blank line inside a table region (ends the table; following rows render as
    raw pipe-delimited text)
  - START/END marker sharing a line with a row
  - missing or malformed header / separator row
  - row whose column count differs from its header
  - unescaped "|" inside a cell
  - duplicate rows
  - unknown or malformed status badge
  - 🔥 [CLOSING SOON] rows not grouped at the top of their table
  - malformed Apply button markup
  - unbalanced START/END markers
  - trailing whitespace on a table row

Exit code 1 if any error is found, so CI can gate on it.
"""

import re
import sys
import os

README = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")
ARCHIVE = os.path.join(os.path.dirname(__file__), "..", "..", "ARCHIVE.md")

TABLE_RE = re.compile(r"(<!-- (\w+)_TABLE_START -->)(.*?)(<!-- \2_TABLE_END -->)", re.DOTALL)
SEP_RE = re.compile(r"^\|[\s\-|:]+\|$")
STATUSES = {"✅ **[OPEN]**", "🔥 **[CLOSING SOON]**", "⏳ **[OPENS SOON]**",
            "🔒 **[CLOSED]**", "❌ **[DISCONTINUED]**"}
CLOSING = "🔥 **[CLOSING SOON]**"
APPLY_RE = re.compile(r'<a href="[^"]+"><img src="https://img\.shields\.io/badge/[^"]+" alt="Apply"></a>')

errors = []
warnings = []


def cells(line):
    """Split a table row into cells, honouring escaped pipes."""
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def check_table(label, lines, require_status=True):
    """lines: the table's lines, already blank-stripped."""
    if len(lines) < 2:
        errors.append(f"{label}: table has no header + separator")
        return
    header, sep = lines[0], lines[1]
    if not header.startswith("| "):
        errors.append(f"{label}: header does not start with '| '")
    if not SEP_RE.match(sep.strip()):
        errors.append(f"{label}: second line is not a separator row -> {sep[:60]!r}")
        return
    ncols = len(cells(header))
    if len(cells(sep)) != ncols:
        errors.append(f"{label}: separator has {len(cells(sep))} cols, header has {ncols}")
    if require_status and cells(header)[0].lower() != "status":
        errors.append(f"{label}: first column is {cells(header)[0]!r}, expected 'Status'")

    seen = {}
    flags = []
    for i, row in enumerate(lines[2:], start=1):
        if not row.startswith("| "):
            errors.append(f"{label} row {i}: does not start with '| ' -> {row[:60]!r}")
            continue
        if not row.rstrip().endswith("|"):
            errors.append(f"{label} row {i}: does not end with '|'")
        if row != row.rstrip():
            warnings.append(f"{label} row {i}: trailing whitespace")
        c = cells(row)
        if len(c) != ncols:
            errors.append(f"{label} row {i}: {len(c)} cols, header has {ncols} -> {c[1][:40] if len(c) > 1 else '?'!r}")
            continue
        if require_status and c[0] not in STATUSES:
            errors.append(f"{label} row {i}: bad status {c[0][:40]!r}")
        flags.append(CLOSING in c[0])
        if row in seen:
            errors.append(f"{label} row {i}: exact duplicate of row {seen[row]}")
        else:
            seen[row] = i
        # Apply cell: either a shields.io button or the :lock: placeholder
        apply_cell = next((x for x in c if "img.shields.io" in x or x == ":lock:"), None)
        if apply_cell and "img.shields.io" in apply_cell and not APPLY_RE.search(apply_cell):
            errors.append(f"{label} row {i}: malformed Apply button -> {apply_cell[:70]!r}")

    k = sum(flags)
    if flags[:k] != [True] * k or any(flags[k:]):
        errors.append(f"{label}: 🔥 CLOSING SOON rows are not grouped at the top")


def check_readme():
    md = open(README, encoding="utf-8").read()
    starts = re.findall(r"<!-- (\w+)_TABLE_START -->", md)
    ends = re.findall(r"<!-- (\w+)_TABLE_END -->", md)
    if starts != ends:
        errors.append(f"README: unbalanced markers -> starts={starts} ends={ends}")
    for m in TABLE_RE.finditer(md):
        name, body = m.group(2), m.group(3)
        label = f"README/{name}"
        if not body.startswith("\n"):
            errors.append(f"{label}: START marker shares a line with content")
        if not body.endswith("\n"):
            errors.append(f"{label}: END marker shares a line with content")
        raw = body.split("\n")[1:-1] if len(body.split("\n")) > 2 else []
        for i, l in enumerate(raw):
            if l.strip() == "":
                errors.append(f"{label}: blank line inside table (breaks rendering) at offset {i}")
        check_table(label, [l for l in raw if l.strip()])
    return len(starts)


def check_archive():
    txt = open(ARCHIVE, encoding="utf-8").read()
    section, buf, n = None, [], 0
    for line in txt.split("\n") + ["## __EOF__"]:
        if line.startswith("## "):
            if section and buf:
                check_table(f"ARCHIVE/{section}", buf)
                n += 1
            section, buf = line[3:].strip(), []
        elif line.startswith("|"):
            buf.append(line)
    return n


tables = check_readme()
arch = check_archive()

print(f"checked {tables} README tables + {arch} ARCHIVE tables")
for w in warnings:
    print(f"  warn:  {w}")
for e in errors:
    print(f"  ERROR: {e}")
print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
sys.exit(1 if errors else 0)
