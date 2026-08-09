You are working on the GitHub repository: https://github.com/Jose-Gael-Cruz-Lopez/underclassmen-opportunities

## PROJECT OVERVIEW

This is an automated GitHub repository that tracks internships, programs, and research opportunities specifically for college freshmen and sophomores (underclassmen). Users submit opportunities by creating a GitHub Issue with just a link, and an AI-powered GitHub Action automatically extracts the details (company name, role, location, category, etc.) and adds them to the README tables.

## REPOSITORY STRUCTURE

```
underclassmen-opportunities/
├── README.md                              # SOURCE OF TRUTH — 9 hand-maintained tables
├── CONTRIBUTING.md                        # Contribution guide
└── .github/
    ├── ISSUE_TEMPLATE/
    │   ├── link_only.yaml                 # PRIMARY: Just paste a URL, AI extracts everything
    │   ├── quick_add.yaml                 # FALLBACK: 4 fields (link, company, title, category)
    │   ├── new_opportunity.yaml           # FULL: All fields manual
    │   ├── edit_opportunity.yaml          # Edit existing listing
    │   ├── close_opportunity.yaml         # Mark listing as closed
    │   └── other.yaml                     # General feedback
    ├── scripts/
    │   ├── auto_extract.py                # Fetches URL + uses OpenAI to extract details
    │   ├── contribution_approved.py       # Processes manual submissions
    │   ├── update_readmes.py              # DISARMED — stale generator, do not run (see below)
    │   ├── util.py                        # Shared utilities (formatting, JSON I/O, etc.)
    │   ├── listings.json                  # THE DATA: all opportunities stored here
    │   └── requirements.txt               # Python dependencies
    └── workflows/
        ├── auto_extract.yml               # Triggered when 'approved' label added to issue
        ├── contribution_approved.yml      # Processes non-AI submissions
        └── update_readmes.yml             # DISARMED — manual workflow_dispatch only
```

## HOW THE AUTOMATION WORKS

1. User creates an issue using the "Add Opportunity (Just Paste Link)" template — they only paste a URL
2. A maintainer reviews and adds the `approved` label
3. The `auto_extract.yml` workflow triggers:
   - Fetches the webpage using `requests` + `BeautifulSoup`
   - Sends page content to OpenAI GPT-4o-mini to extract structured data
   - AI returns JSON with: company_name, title, locations, category, opportunity_type, season, sponsorship, field (for research)
   - Script adds the new listing to `listings.json` (intake log only)
   - Commits and pushes `listings.json` to main
   - Comments on the issue with extracted details, then closes the issue
   - A maintainer then adds the row to `README.md` **by hand**

> **`update_readmes.py` is NOT run by any workflow (disarmed 2026-08-08).**
> `README.md` is the source of truth. The generator only knows 4 of the 9
> tables and emits a schema with no `Status` column, and `listings.json` has
> diverged (only ~10 of its 112 entries still match the README). Running it
> would delete every status badge and replace live rows with stale data.
> `update_readmes.yml` is now `workflow_dispatch`-only. Do not re-enable it
> until the generator emits the live schema for all nine tables **and** a dry
> run produces an empty diff.

## THE NINE README TABLES

The README has nine sections with tables between HTML comment markers. Every
table's first column is `Status`, holding exactly one of
`✅ **[OPEN]**`, `🔥 **[CLOSING SOON]**`, or `⏳ **[OPENS SOON]**`.

1. **Underclassmen Internships** (`<!-- INTERNSHIPS_TABLE_START/END -->`)
   - Status | Company | Role | Location | Application | Date Posted
   - Deadline is embedded in the Role text ("— Deadline: Rolling")

2. **Underclassmen Programs (Fellowships, Externships, etc.)** (`<!-- PROGRAMS_TABLE_START/END -->`)
   - Status | Company | Program | Type | Location | Application | Date Posted

3. **Ambassador Programs** (`<!-- AMBASSADORS_TABLE_START/END -->`)
   - Status | Company | Program | Type | Location | Application | Date Posted

4. **Underclassmen Research Programs** (`<!-- RESEARCH_TABLE_START/END -->`)
   - Status | University/Organization | Program | Field | Location | Application | Date Posted
   - Currently empty; keep the header and empty table in place

5. **Scholarships** (`<!-- SCHOLARSHIPS_TABLE_START/END -->`)
   - Status | Organization | Scholarship | Amount | Application | Deadline

6. **HBCU Opportunities** (`<!-- HBCU_TABLE_START/END -->`)
   - Status | Organization | Opportunity | Type | Location | Application | Date Posted

7. **Women in Tech Opportunities** (`<!-- WOMEN_TABLE_START/END -->`)
   - Status | Organization | Opportunity | Type | Location | Application | Date Posted

8. **Rising Freshmen & Class of 2030** (`<!-- RISING_FRESHMEN_TABLE_START/END -->`)
   - Status | Organization | Opportunity | Type | Location | Application | Deadline

9. **State-Based Scholarships & Grants** (`<!-- STATE_TABLE_START/END -->`)
   - Status | State | Program | Award | Eligibility | Application | Deadline

Some programs are listed in two tables on purpose (e.g. WomenHack and
GirlsWhoML in both Programs and Women in Tech; Jane Street WiSE in both Women
in Tech and Rising Freshmen). Any edit must be applied to **every** instance so
the tables never contradict each other.

## RESOLVED BUG LOG (verified 2026-08-08 — do not "re-fix" these)

Every item in the original bug list has been addressed. Verified against the
code, not assumed. Left here so nobody re-opens settled ground.

| # | Original bug | Status |
|---|---|---|
| 1 | Table columns misaligned by unescaped `\|` | **Fixed** — `util.sanitize_table_cell()` escapes pipes and newlines; called in all four table builders (12 call sites) |
| 2 | Duplicate entries showing the `↳` arrow | **Fixed upstream** — `auto_extract.py` now rejects duplicates by URL *and* by `company_name + title`. The arrow code still exists in `create_internships_table()` but that generator is disarmed and the README uses 0 arrows |
| 3 | Both label-triggered workflows could race | **Fixed** — both declare `concurrency: {group: add_opportunity, cancel-in-progress: false}` |
| 4 | Edit Opportunity didn't actually edit | **Fixed** — `handle_edit_opportunity()` now fails fast and tells the user to close + re-add |
| 5 | `git push` could fail silently | **Fixed** — both workflows do `git fetch && git rebase` with a 3-attempt retry loop |
| 6 | Non-underclassmen listings still added | **By design** — a maintainer applying the `approved` label *is* the review gate. `auto_extract.py` logs a warning and proceeds. Intentional, not a bug |

Additional improvements from the original list are also done: AI output is
validated (empty/`Unknown` company or title, bad category, URL-shaped or
HTML-bearing locations all rejected with a "use Quick Add" message);
`format_link()` emits only the blue shields.io badge and no imgur URL survives
anywhere; `create_md_table()` has been removed from `util.py`; imports are clean.

## IF YOU ARE ASKED TO "FIX THE README GENERATOR"

Read the disarm note above first. The generator is not broken in a way you can
patch in isolation — it is missing five of the nine tables and the entire
`Status` column, and `listings.json` no longer reflects the README. Re-arming
it without rebuilding both halves will silently destroy live data. The correct
order is: regenerate `listings.json` from `README.md`, extend the generator to
all nine tables with their real schemas, prove a dry run diffs empty, and only
then restore the trigger.

## IMPORTANT CONSTRAINTS

- The Apply button MUST be blue using shields.io: `https://img.shields.io/badge/Apply-blue?style=for-the-badge`
- The OpenAI API key is stored as a repository secret named **`OPEN_AI`**, which
  `auto_extract.yml` maps to the `OPENAI_API_KEY` environment variable the
  script reads. The secret is not called `OPENAI_API_KEY`.
- The AI model used is `gpt-4o-mini`
- All timestamps are in Pacific Standard Time (PST)
- **`README.md` is the single source of truth.** `listings.json` is a
  submission intake log only, and it has diverged — do not treat it as
  authoritative and do not regenerate the README from it
- Never commit broken README tables
- Each listing in listings.json MUST have these required fields: id, company_name, title, url, locations, season, category, opportunity_type, target_year, sponsorship, active, is_visible, date_posted, date_updated, source

## WHAT SUCCESS LOOKS LIKE

When done:
1. Pasting a link and adding `approved` label correctly extracts ALL details
   into `listings.json`, and the issue is closed with a summary
2. A maintainer adds the row to the right one of the nine README tables by hand
3. Every table keeps its `Status` column, matching column counts, and no
   duplicate rows
4. The Apply button is always the blue shields.io badge in the Application column
5. No duplicate entries
6. No broken markdown tables
7. The workflow handles errors gracefully and never commits bad data
8. `python3 .github/scripts/closing_soon.py` reports `Updated 0 row(s)` —
   meaning the badges in the README already agree with the 14-day rule

The bug list that used to live here is resolved; see the RESOLVED BUG LOG
above before starting work, and do not re-fix settled items. If you are making
changes, read the repository first to understand the current state.
