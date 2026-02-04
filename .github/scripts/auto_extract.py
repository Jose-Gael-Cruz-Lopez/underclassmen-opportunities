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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text content
        text = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)

        # Truncate if too long (for API limits)
        if len(text) > 15000:
            text = text[:15000] + "\n...[truncated]"

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
        util.fail("OPENAI_API_KEY environment variable not set")

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
            current_field = line[4:].strip().lower().replace(" ", "_")
            current_value = []
        elif current_field:
            if line.strip() != "_No response_":
                current_value.append(line)

    if current_field and current_value:
        data[current_field] = "\n".join(current_value).strip()

    return data


def main():
    if len(sys.argv) < 2:
        util.fail("Missing event data file path")

    event_path = sys.argv[1]
    with open(event_path, "r") as f:
        event = json.load(f)

    issue = event.get("issue", {})
    body = issue.get("body", "")
    username = issue.get("user", {}).get("login", "unknown")

    # Parse issue body
    data = parse_issue_body(body)

    url = data.get("link_to_opportunity", "") or data.get("link", "")
    url = util.clean_url(url)

    if not url:
        util.fail("No URL found in issue body")

    notes = data.get("any_additional_context?_(optional)", "") or data.get("notes", "")

    print(f"Fetching content from: {url}")

    # Fetch page content
    page_content = fetch_page_content(url)

    if "error" in page_content:
        util.fail(f"Failed to fetch page: {page_content['error']}")

    print("Extracting details with AI...")

    # Extract with AI
    extracted = extract_with_openai(page_content, notes)

    print(f"Extracted: {json.dumps(extracted, indent=2)}")

    # Check if it's actually for underclassmen
    if not extracted.get("is_underclassmen", False):
        util.set_output("warning", "This opportunity may not be specifically for underclassmen. Please verify before approving.")
        print("WARNING: This may not be an underclassmen-specific opportunity!")

    # Check for duplicates
    listings = util.get_listings_from_json()
    for listing in listings:
        if listing["url"] == url:
            util.fail(f"Duplicate: This opportunity already exists (ID: {listing['id']})")

    # Create the listing
    new_listing = {
        "id": util.generate_uuid(),
        "company_name": extracted.get("company_name", "Unknown"),
        "title": extracted.get("title", "Unknown"),
        "url": url,
        "locations": extracted.get("locations", ["Multiple Locations"]),
        "season": extracted.get("season", "Summer"),
        "category": extracted.get("category", "Internship"),
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
    if extracted.get("category") == "Research" and extracted.get("field"):
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
