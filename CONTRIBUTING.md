# Contributing to Underclassmen Opportunities

Thank you for your interest in contributing! This repository aims to help freshmen and sophomores find opportunities specifically designed for them.

## How to Add an Opportunity

### Just Paste the Link! (Recommended)

The easiest way to contribute:

1. Go to **Issues** → **New Issue**
2. Select **"Add Opportunity (Just Paste Link)"**
3. Paste the URL to the opportunity
4. Submit!

**That's it!** AI will automatically extract:
- Company name
- Role/Program title
- Location
- Category (Internship/Program/Research/Scholarship)
- Deadline
- Season
- Sponsorship info

### Alternative Methods

| Template | When to Use |
|----------|-------------|
| **Just Paste Link** | Default - paste URL, AI extracts everything |
| **Quick Add** | If AI extraction fails, manually fill 4 fields |
| **New Opportunity** | Want full control over all details |

---

## What Qualifies as an Underclassmen Opportunity?

This repository is **specifically for programs that target freshmen and sophomores**—students who are typically in their first or second year of college.

### Eligible Students and Current Applications

Programs must explicitly target **current college freshmen or sophomores**, or an equivalent early-year graduation cohort. In the 2026–27 academic year these are typically **Class of 2030 (freshmen)** and **Class of 2029 (sophomores)**. Follow the provider's academic-year and degree-length rules; a graduation year alone is not proof of eligibility.

The **Rising Freshmen** and **State-Based Scholarships & Grants** sections also accept initial awards specifically for incoming college freshmen. Incoming Fall 2027 freshmen typically graduate in 2031. Targeted incoming-freshman awards at HBCUs or in STEM may be placed in the relevant specialist section. School-age contests and generic scholarships open to all class years do not qualify. State award renewals are not separate opportunities.

Before adding a listing:

- Verify the exact current cycle on an official program page and its live application form or official recruiting feed.
- Record the eligible class years, geographic restrictions, deadline and timezone where published, and the verification date.
- Check each regional session separately; archive a closed session even if another location is open.
- Use “Not published (live application)” when a real application has no stated deadline. Do not invent a rolling deadline.
- Keep notification signups, expressions of interest, old cycles, and applications without verifiable current eligibility in `ARCHIVE.md` until an open application can be confirmed.
- Archive generic all-year programs, broad financial aid, professional conferences, and school-age contests even if freshmen could theoretically qualify.
- State every provider-defined degree-length, transfer, institutional, or gender exception. A restricted freshman/sophomore scholarship award may use a shared application, but the row must identify that award rather than advertise the provider's broader undergraduate scholarship programme.
- List each distinct application once, in its most relevant category. Use cross-references when it fits another section; do not multiply rows for awards sharing one application.
- A 403/429 response or JavaScript requirement is not proof of a dead link. Confirm removal, an expired deadline, a closed form, or an eligibility mismatch before assigning the reason.

### Examples of What We Include

- **NVIDIA Ignite** — current first- and second-year students, with a verified application window.
- **Jane Street FTTP / FOCUS** — current first-year students, with separate applications for each open location.
- **MLT Career Prep** — the current sophomore cohort, with published application deadlines.

### What Does NOT Belong Here

- **General internships open to all years** — use a general internship board instead
- **Opportunities accepting juniors or seniors** - These belong in the general listings
- **Full-time/new-grad positions** - For graduating students
- **Opportunities requiring significant prior experience** - Underclassmen programs should be accessible to early students

---

## Categories

Keep all nine sections in README.md, even when a category has no verified open applications. Move outdated table rows into the corresponding ARCHIVE.md section; preserve the main heading, table header, and table markers.

| Category | Description | Examples |
|----------|-------------|----------|
| **Internship** | Traditional internship programs for underclassmen | NVIDIA Ignite |
| **Program** | Fellowships, externships, bootcamps | Jane Street FTTP / FOCUS, MLT Career Prep |
| **Ambassador** | Freshman/sophomore-focused campus leadership applications | Institution-specific underclassmen ambassador cohorts |
| **Research** | University/lab research programs | Verified current freshman/sophomore research cohorts |
| **Scholarship** | Financial awards explicitly targeting first-/second-year students | Restricted freshman/sophomore award tracks |
| **HBCU** | Underclassmen or incoming-freshman opportunities at HBCUs/MSIs | Verified HBCU freshman scholarship cohorts |
| **Women in Tech** | First-/second-year technology, science, and engineering opportunities with a women/gender-minority focus | HRT WiTTI, targeted STEM scholarships |
| **Rising Freshmen** | Current first-year or incoming college freshman cohorts | Initial college freshman scholarship applications |
| **State-Based Scholarships & Grants** | State/regional awards with incoming-freshman or early-college application gates | Initial Tennessee Promise application |

---

## Closing or Editing an Opportunity

### Closing (Application No Longer Open)

1. Go to **Issues** → **New Issue**
2. Select **Close Opportunity**
3. Provide company name and role title
4. Submit

### Editing (Information Changed)

Editing via issues is not currently supported. To update a listing:
1. Open a **Close Opportunity** issue to remove the old listing
2. Open a new **Add Opportunity** issue with the corrected details

---

## How the Automation Works

1. **User submits** a link via the issue template
2. **Maintainer reviews** and adds the `approved` label
3. **AI extracts** company, role, location, category, etc. from the page
4. **Details are recorded** in `.github/scripts/listings.json` as an intake log
5. **Issue is closed** with a summary of what was extracted
6. **A maintainer verifies current application status and underclassmen eligibility, then adds the row to `README.md` by hand**

> **Note:** step 6 is manual on purpose. `README.md` is the source of truth — it
> carries status badges (✅ / 🔥 / ⏳) and the category tables that the extractor doesn't
> model, so nothing writes to it automatically. Expect a short delay between
> your issue being approved and the listing appearing on the site.

---

## Guidelines

- **Search existing issues** before submitting to avoid duplicates
- **Verify the opportunity** is specifically for underclassmen
- **Use official links** - no referral links or affiliate URLs
- Be respectful and help maintain accurate information

---

Thank you for helping underclassmen find great opportunities!
