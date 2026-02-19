#!/usr/bin/env python3
"""
Auto-extract opportunity details from a URL using AI.

This script:
1. Fetches the webpage content
2. Uses OpenAI API to extract structured data
3. Adds the opportunity to listings.json
"""

import json
import os
import sys
import re
import requests
from bs4 import BeautifulSoup
import util

# Try to import OpenAI
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def fetch_page_content(url):
    """Fetch and parse webpage content."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            script.decompose()

        # Get text content
        text = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)

        # Truncate if too long (for API limits)
        if len(text) > 12000:
            text = text[:12000] + "\n...[truncated]"

        # Also get the title
        title_tag = soup.find("title")
        page_title = title_tag.get_text() if title_tag else ""

        return {
            "text": text,
            "title": page_title,
            "url": url
        }

    except Exception as e:
        return {
            "text": f"Error fetching page: {str(e)}",
            "title": "",
            "url": url,
            "error": str(e)
        }


def extract_with_openai(page_content, additional_notes=""):
    """Use OpenAI to extract structured data from page content."""
    if not HAS_OPENAI:
        util.fail("OpenAI library not installed. Run: pip install openai")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        util.fail("OPENAI_API_KEY environment variable not set. Add it as a repository secret.")

    client = OpenAI(api_key=api_key)

    prompt = f"""Analyze this job/internship posting and extract the following information.
This is for a repository tracking UNDERCLASSMEN opportunities (freshman/sophomore students).

Page Title: {page_content['title']}
URL: {page_content['url']}
Additional Notes from submitter: {additional_notes}

Page Content:
{page_content['text']}

---

Extract and return a JSON object with these fields:
- company_name: The company or organization name
- title: The role/program title (e.g., "STEP Intern", "Explore Program", "REU")
- locations: Array of locations (e.g., ["San Francisco, CA", "Remote"]). Use ["Multiple Locations"] if many or unspecified.
- category: One of "Internship", "Program", or "Research"
  - "Internship" = traditional internship programs (STEP, Explore, etc.)
  - "Program" = fellowships, externships, bootcamps (Code2040, MLH Fellowship)
  - "Research" = university/lab research programs (REU, SURF)
- opportunity_type: More specific type (e.g., "Internship", "Fellowship", "Externship", "Research")
- field: For research programs, what field (e.g., "Computer Science", "STEM"). Empty string for non-research.
- season: "Summer", "Fall", "Winter", "Spring", or "Multiple"
- sponsorship: "Offers Sponsorship", "Does Not Offer Sponsorship", "U.S. Citizenship Required", or "Not Specified"
- is_underclassmen: true if this is specifically for freshmen/sophomores, false otherwise

IMPORTANT: Only set is_underclassmen to true if the posting EXPLICITLY mentions it's for freshmen, sophomores, first-year, second-year, or underclassmen students.

Return ONLY valid JSON, no other text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured data from job postings. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )

        result_text = response.choices[0].message.content.strip()

        # Clean up markdown code blocks if present
        if result_text.startswith("```"):
            result_text = re.sub(r"^```json?\n?", "", result_text)
            result_text = re.sub(r"\n?```$", "", result_text)

        return json.loads(result_text)

    except json.JSONDecodeError as e:
        util.fail(f"Failed to parse AI response as JSON: {e}\nResponse: {result_text}")
    except Exception as e:
        util.fail(f"OpenAI API error: {str(e)}")


def parse_issue_body(body):
    """Parse the issue body to get URL and notes."""
    lines = body.strip().split("\n")
    data = {}

    current_field = None
    current_value = []

    for line in lines:
        if line.startswith("### "):
            if current_field and current_value:
                data[current_field] = "\n".join(current_value).strip()
            # Convert "Link to Opportunity" -> "link_to_opportunity"
            current_field = line[4:].strip().lower().replace(" ", "_").replace("?", "").replace("(", "").replace(")", "")
            current_value = []
        elif current_field:
            if line.strip() and line.strip() != "_No response_":
                current_value.append(line)

    if current_field and current_value:
        data[current_field] = "\n".join(current_value).strip()

    return data


def extract_url_from_body(body):
    """Try multiple methods to extract URL from issue body."""
    # Method 1: Parse structured fields
    data = parse_issue_body(body)

    # Try various field names
    url_fields = [
        "link_to_opportunity",
        "link",
        "url",
        "link_to_opportunity_posting",
        "application_link"
    ]

    for field in url_fields:
        if field in data and data[field]:
            url = data[field].strip()
            if url.startswith("http"):
                return url, data

    # Method 2: Find any URL in the body
    url_pattern = r'https?://[^\s<>"\')\]]+'
    matches = re.findall(url_pattern, body)
    if matches:
        return matches[0], data

    return None, data


def main():
    if len(sys.argv) < 2:
        util.fail("Missing event data file path")

    event_path = sys.argv[1]

    print(f"Reading event from: {event_path}")

    with open(event_path, "r") as f:
        event = json.load(f)

    issue = event.get("issue", {})
    body = issue.get("body", "")
    username = issue.get("user", {}).get("login", "unknown")

    print(f"Issue body:\n{body}\n")

    # Extract URL from body
    url, data = extract_url_from_body(body)

    if not url:
        util.fail("No URL found in issue body. Please make sure to include a valid URL.")

    url = util.clean_url(url)
    print(f"Extracted URL: {url}")

    notes = data.get("any_additional_context_optional", "") or data.get("notes", "")

    print(f"Fetching content from: {url}")

    # Fetch page content
    page_content = fetch_page_content(url)

    if "error" in page_content:
        util.fail(f"Failed to fetch page: {page_content['error']}")

    print(f"Page title: {page_content['title']}")
    print(f"Content length: {len(page_content['text'])} chars")
    print("Extracting details with AI...")

    # Extract with AI
    extracted = extract_with_openai(page_content, notes)

    print(f"Extracted: {json.dumps(extracted, indent=2)}")

    # Validate extracted data
    company_name = extracted.get("company_name", "").strip()
    title = extracted.get("title", "").strip()
    locations = extracted.get("locations", [])
    category = extracted.get("category", "")

    if not company_name or company_name == "Unknown":
        util.fail("AI extraction failed: could not determine the company name. Please use the Quick Add template instead.")
    if not title or title == "Unknown":
        util.fail("AI extraction failed: could not determine the role/program title. Please use the Quick Add template instead.")
    if not isinstance(locations, list) or len(locations) == 0:
        locations = ["Multiple Locations"]
    if category not in util.VALID_CATEGORIES:
        util.fail(f"AI extraction returned invalid category '{category}'. Expected one of: {util.VALID_CATEGORIES}. Please use the Quick Add template instead.")

    # Sanitize locations — remove any that look like URLs or HTML
    clean_locations = []
    for loc in locations:
        loc = loc.strip()
        if loc and not loc.startswith("http") and "<" not in loc:
            clean_locations.append(loc)
    if not clean_locations:
        clean_locations = ["Multiple Locations"]
    locations = clean_locations

    # Check if it's actually for underclassmen
    if not extracted.get("is_underclassmen", False):
        util.set_output("needs_review", "true")
        util.set_output("warning", "This opportunity may not be specifically for underclassmen. A maintainer needs to verify before it can be added. Add the 'approved' label again after review.")
        print("WARNING: Not confirmed as underclassmen-specific. Skipping auto-add.")
        util.set_output("commit_message", "")
        sys.exit(0)

    # Check for duplicates (by URL or by company+title)
    listings = util.get_listings_from_json()
    for listing in listings:
        if listing["url"] == url:
            util.set_output("is_duplicate", "true")
            util.set_output("duplicate_id", listing["id"])
            util.set_output("duplicate_reason", f"This URL already exists in the repository")
            util.set_output("commit_message", "")
            print(f"DUPLICATE DETECTED: URL already exists (ID: {listing['id']})")
            sys.exit(0)
        if (listing["company_name"].lower() == company_name.lower() and
                listing["title"].lower() == title.lower()):
            util.set_output("is_duplicate", "true")
            util.set_output("duplicate_id", listing["id"])
            util.set_output("duplicate_reason", f"'{company_name} - {title}' already exists in the repository")
            util.set_output("commit_message", "")
            print(f"DUPLICATE DETECTED: {company_name} - {title} already exists (ID: {listing['id']})")
            sys.exit(0)

    # Create the listing
    new_listing = {
        "id": util.generate_uuid(),
        "company_name": company_name,
        "title": title,
        "url": url,
        "locations": locations,
        "season": extracted.get("season", "Summer"),
        "category": category,
        "opportunity_type": extracted.get("opportunity_type", "Internship"),
        "target_year": ["Freshman (1st year)", "Sophomore (2nd year)"],
        "sponsorship": extracted.get("sponsorship", "Not Specified"),
        "active": True,
        "is_visible": True,
        "date_posted": util.get_current_timestamp(),
        "date_updated": util.get_current_timestamp(),
        "source": username
    }

    # Add field for research
    if category == "Research" and extracted.get("field"):
        new_listing["field"] = extracted["field"]

    # Save
    listings.append(new_listing)
    util.save_listings_to_json(listings)

    # Set outputs
    company = new_listing["company_name"]
    title = new_listing["title"]
    util.set_output("commit_message", f"Add {company} - {title}")
    util.set_output("contributor_name", username)
    util.set_output("contributor_email", "actions@github.com")
    util.set_output("extracted_data", json.dumps(extracted))

    print(f"Successfully added: {company} - {title}")


if __name__ == "__main__":
    main()
