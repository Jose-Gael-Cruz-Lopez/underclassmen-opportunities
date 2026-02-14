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
- Category (Internship/Program/Research)
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

This repository is **specifically for programs that target first and second-year students**. Examples include:

- **Google STEP** - Student Training in Engineering Program for 1st/2nd year students
- **Microsoft Explore** - Designed for freshmen and sophomores
- **Meta University** - For students early in their college career
- **Bank of America Freshman Analyst** - Explicitly for first-year students
- **Fellowships** like Code2040, MLH Fellowship that welcome underclassmen
- **Research programs** like REU, SURF that accept underclassmen

### What Does NOT Belong Here

- General internships open to all years (use [Summer2026-Internships](https://github.com/vanshb03/Summer2026-Internships) instead)
- Opportunities requiring junior/senior standing
- Full-time/new-grad positions
- Opportunities requiring significant prior experience

---

## Categories

Opportunities are organized into three sections:

| Category | Description | Examples |
|----------|-------------|----------|
| **Internship** | Traditional internship programs for underclassmen | STEP, Explore, Meta University |
| **Program** | Fellowships, externships, bootcamps | Code2040, MLH Fellowship, SEO Tech |
| **Research** | University/lab research programs | REU, SURF, NASA OSSI |

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

## For Maintainers: Setup

To enable AI auto-extraction, add an OpenAI API key:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `OPENAI_API_KEY`
4. Value: Your OpenAI API key

---

## How the Automation Works

1. **User submits** a link via the issue template
2. **Maintainer reviews** and adds the `approved` label
3. **AI extracts** company, role, location, category, etc. from the page
4. **Automation adds** the opportunity to the correct table
5. **Issue is closed** with a summary of what was added

---

## Guidelines

- **Search existing issues** before submitting to avoid duplicates
- **Verify the opportunity** is specifically for underclassmen
- **Use official links** - no referral links or affiliate URLs
- Be respectful and help maintain accurate information

---

Thank you for helping underclassmen find great opportunities!
