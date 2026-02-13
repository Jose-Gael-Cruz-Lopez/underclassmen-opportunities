You are working on the GitHub repository: https://github.com/Jose-Gael-Cruz-Lopez/underclassmen-opportunities

## PROJECT OVERVIEW

This is an automated GitHub repository that tracks internships, programs, and research opportunities specifically for college freshmen and sophomores (underclassmen). Users submit opportunities by creating a GitHub Issue with just a link, and an AI-powered GitHub Action automatically extracts the details (company name, role, location, category, etc.) and adds them to the README tables.

## REPOSITORY STRUCTURE

```
underclassmen-opportunities/
├── README.md                              # Main page with 3 tables
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
    │   ├── update_readmes.py              # Generates README tables from listings.json
    │   ├── util.py                        # Shared utilities (formatting, JSON I/O, etc.)
    │   ├── listings.json                  # THE DATA: all opportunities stored here
    │   └── requirements.txt               # Python dependencies
    └── workflows/
        ├── auto_extract.yml               # Triggered when 'approved' label added to issue
        ├── contribution_approved.yml      # Processes non-AI submissions
        └── update_readmes.yml             # Auto-updates README when listings.json changes
```

## HOW THE AUTOMATION WORKS

1. User creates an issue using the "Add Opportunity (Just Paste Link)" template — they only paste a URL
2. A maintainer reviews and adds the `approved` label
3. The `auto_extract.yml` workflow triggers:
   - Fetches the webpage using `requests` + `BeautifulSoup`
   - Sends page content to OpenAI GPT-4o-mini to extract structured data
   - AI returns JSON with: company_name, title, locations, category, opportunity_type, season, sponsorship, field (for research)
   - Script adds the new listing to `listings.json`
   - Runs `update_readmes.py` to regenerate all README tables
   - Commits and pushes to main
   - Comments on the issue with extracted details, then closes the issue

## THE THREE README TABLES

The README has three sections with tables between HTML comment markers:

1. **Underclassmen Internships** (`<!-- INTERNSHIPS_TABLE_START -->` / `<!-- INTERNSHIPS_TABLE_END -->`)
   - Columns: Company | Role | Location | Application | Date Posted
   - For traditional internship programs (STEP, Explore, etc.)

2. **Underclassmen Programs (Fellowships, Externships, etc.)** (`<!-- PROGRAMS_TABLE_START -->` / `<!-- PROGRAMS_TABLE_END -->`)
   - Columns: Company | Program | Type | Location | Application | Date Posted
   - For fellowships, externships, bootcamps

3. **Underclassmen Research Programs** (`<!-- RESEARCH_TABLE_START -->` / `<!-- RESEARCH_TABLE_END -->`)
   - Columns: University/Organization | Program | Field | Location | Application | Date Posted
   - For REU, SURF, lab research programs

## KNOWN BUGS AND ISSUES TO FIX

### BUG 1: TABLE COLUMNS GET MISALIGNED (CRITICAL)
When the AI extracts data, sometimes fields end up in the wrong columns. For example:
- The "Apply" button appears in the Location column
- "London" appears in the Application column instead of the Location column
- This happens because the AI sometimes returns locations that contain pipe characters "|" or the data isn't properly sanitized before being placed in markdown table cells

**Root cause:** The `create_programs_table()` and `create_research_table()` functions in `update_readmes.py` don't sanitize the data. If a location contains "|" it breaks the markdown table. Also, the AI extraction sometimes returns data in wrong fields.

**Fix needed:**
- In `util.py`, add a `sanitize_table_cell()` function that escapes pipe characters "|" in all cell values
- Apply this sanitization in ALL table creation functions in `update_readmes.py`
- In `auto_extract.py`, add validation that extracted data makes sense (e.g., location should look like a location, not a URL or button)

### BUG 2: DUPLICATE ENTRIES WITH ARROW SYMBOL
When CrowdStrike was added, it appeared twice with an "↳" arrow. The arrow feature is meant to show multiple roles from the same company, but it's showing for duplicate entries.

**Root cause:** The `create_internships_table()` function uses "↳" when the current company matches the previous company. But if the same company+role is added twice (duplicate), it shows the arrow instead of being caught as a duplicate.

**Fix needed:**
- In `auto_extract.py`, improve duplicate detection to also check by company_name + title (not just URL)
- In `update_readmes.py`, consider removing the arrow feature entirely OR ensure it only shows when there are genuinely different roles from the same company

### BUG 3: WORKFLOW RACE CONDITIONS
Both `auto_extract.yml` and `contribution_approved.yml` trigger on the `approved` label. They could both run simultaneously and overwrite each other.

**Fix needed:**
- Add concurrency control to `auto_extract.yml` matching what `contribution_approved.yml` already has
- Add `git pull origin main --rebase` before pushing in both workflows
- Consider consolidating into a single workflow

### BUG 4: EDIT OPPORTUNITY DOESN'T ACTUALLY EDIT
The `handle_edit_opportunity()` function in `contribution_approved.py` only updates the timestamp — it doesn't parse or apply the actual changes described in the issue.

**Fix needed:**
- Either implement proper editing (parse the changes text and update fields)
- Or remove the edit template and tell users to close + re-add

### BUG 5: GIT PUSH CAN FAIL SILENTLY
The workflow does `git push origin main` without checking if main has been updated since checkout. If another workflow pushed in between, this fails.

**Fix needed:**
- Add `git fetch origin main && git rebase origin/main` before every push
- Add retry logic for push failures

### BUG 6: NON-UNDERCLASSMEN OPPORTUNITIES STILL GET ADDED
When AI sets `is_underclassmen: false`, a warning is shown but the listing is still added.

**Fix needed:**
- When `is_underclassmen` is false, don't auto-add the listing
- Instead, add a "needs-review" label and comment asking the maintainer to verify
- Only add on a second approval

## ADDITIONAL IMPROVEMENTS NEEDED

### 1. VALIDATE AI EXTRACTION OUTPUT
After OpenAI returns JSON, validate:
- `company_name` is not empty or "Unknown"
- `title` is not empty or "Unknown"
- `locations` is a non-empty array of strings that look like locations
- `category` is one of: "Internship", "Program", "Research"
- `url` is a valid URL
- No field contains HTML or markdown syntax that would break tables

### 2. ADD ERROR RECOVERY
If the AI extraction fails or returns bad data:
- Don't commit broken data
- Comment on the issue with what went wrong
- Suggest using the Quick Add template instead

### 3. MAKE THE APPLY BUTTON CONSISTENT
The Apply button should ALWAYS be a blue shields.io badge:
```
<a href="URL"><img src="https://img.shields.io/badge/Apply-blue?style=for-the-badge" alt="Apply"></a>
```
Make sure this is the ONLY format used everywhere — in util.py's `format_link()` function AND in the README. Never use the old gray imgur button (`https://i.imgur.com/u1KNU8z.png`).

### 4. CLEAN UP UNUSED CODE
- Remove `create_md_table()` from `util.py` — it's unused (update_readmes.py has its own table functions)
- Remove unused imports

### 5. TEST THE FULL FLOW
After making all fixes:
1. Run `update_readmes.py` locally to verify tables generate correctly
2. Verify the workflow YAML files are syntactically correct
3. Ensure listings.json passes schema validation
4. Test edge cases: locations with commas, long titles, special characters

## IMPORTANT CONSTRAINTS

- The Apply button MUST be blue using shields.io: `https://img.shields.io/badge/Apply-blue?style=for-the-badge`
- The OpenAI API key is stored as a GitHub secret called `OPENAI_API_KEY`
- The AI model used is `gpt-4o-mini`
- All timestamps are in Pacific Standard Time (PST)
- The listings.json is the single source of truth — the README is auto-generated from it
- Never commit broken README tables
- Each listing in listings.json MUST have these required fields: id, company_name, title, url, locations, season, category, opportunity_type, target_year, sponsorship, active, is_visible, date_posted, date_updated, source

## WHAT SUCCESS LOOKS LIKE

When done:
1. Pasting a link and adding `approved` label should correctly extract ALL details
2. The extracted data should land in the CORRECT table (Internship/Program/Research)
3. ALL columns should be properly aligned — no data in wrong columns
4. The Apply button should always be blue and in the Application column
5. No duplicate entries
6. No broken markdown tables
7. The workflow should handle errors gracefully and never commit bad data
8. The edit functionality should either work properly or be removed

Please read every file in the repository, fix all the bugs listed above, test the scripts, and commit the fixes. Start by reading all files to understand the current state, then fix issues one by one.
