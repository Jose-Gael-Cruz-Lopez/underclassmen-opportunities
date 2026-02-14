#!/usr/bin/env python3
"""
Process approved contribution issues and update listings.

This script handles three types of contributions:
1. new_opportunity - Add a new opportunity to the listings
2. edit_opportunity - Edit an existing opportunity
3. close_opportunity - Mark an opportunity as closed/inactive
"""

import json
import os
import sys
import re
import util


def parse_issue_body(body, labels):
    """Parse the issue body based on issue type."""
    lines = body.strip().split("\n")
    data = {}

    current_field = None
    current_value = []

    for line in lines:
        # Check for field headers (### Field Name)
        if line.startswith("### "):
            if current_field and current_value:
                data[current_field] = "\n".join(current_value).strip()
            current_field = line[4:].strip().lower().replace(" ", "_")
            current_value = []
        elif current_field:
            # Skip "_No response_" placeholders
            if line.strip() != "_No response_":
                current_value.append(line)

    # Don't forget the last field
    if current_field and current_value:
        data[current_field] = "\n".join(current_value).strip()

    return data


def handle_new_opportunity(data, username, is_quick_add=False):
    """Handle adding a new opportunity."""
    listings = util.get_listings_from_json()

    # Get URL - handle both full and quick templates
    url = data.get("link_to_opportunity_posting", "") or data.get("link", "")
    url = util.clean_url(url)
    if not url:
        util.fail("Missing required field: URL")

    # Check for duplicates
    for listing in listings:
        if listing["url"] == url:
            util.fail(f"Duplicate: This opportunity already exists (ID: {listing['id']})")

    # Get company name - handle both templates
    company_name = (data.get("company/organization_name", "") or
                    data.get("company/organization", "")).strip()

    # Get title - handle both templates
    title = (data.get("program/role_title", "") or
             data.get("role/program_name", "")).strip()

    # Parse locations (default to "Multiple Locations" if not provided)
    locations_str = data.get("location", "") or data.get("location_(optional)", "")
    if locations_str:
        # Support semicolon, pipe, or newline as separators
        import re
        locations = [loc.strip() for loc in re.split(r'[;|\n]', locations_str) if loc.strip()]
    else:
        locations = ["Multiple Locations"]

    # Get category (for quick add) or infer from opportunity type
    category = data.get("category", "Internship")
    # Clean up category if it has the full description
    if "Internship" in category:
        category = "Internship"
    elif "Program" in category:
        category = "Program"
    elif "Research" in category:
        category = "Research"

    # Get opportunity type or use defaults based on category
    opportunity_type = data.get("type_of_opportunity", "")
    if not opportunity_type or is_quick_add:
        if category == "Internship":
            opportunity_type = "Internship"
        elif category == "Program":
            opportunity_type = "Fellowship"
        elif category == "Research":
            opportunity_type = "Research"

    # Get field for research programs
    field = data.get("field/area_(for_research_programs_only)", "") or data.get("research_field_(optional,_for_research_only)", "")

    # Parse target year (default for quick add)
    target_year_str = data.get("target_year", "")
    if target_year_str:
        target_year = [y.strip() for y in target_year_str.split(",") if y.strip()]
    else:
        target_year = ["Freshman (1st year)", "Sophomore (2nd year)"]

    # Get season (default to Summer)
    season = data.get("what_season_is_this_opportunity_for?", "Summer")

    # Get sponsorship (default to Not Specified)
    sponsorship = data.get("sponsorship/citizenship_requirements", "Not Specified")

    # Get active status (default to Yes/True)
    active_str = data.get("is_this_opportunity_currently_accepting_applications?", "Yes")
    active = active_str == "Yes" or active_str == ""

    # Create new listing
    new_listing = {
        "id": util.generate_uuid(),
        "company_name": company_name,
        "title": title,
        "url": url,
        "locations": locations,
        "season": season,
        "category": category,
        "opportunity_type": opportunity_type,
        "target_year": target_year,
        "sponsorship": sponsorship,
        "active": True if is_quick_add else active,
        "is_visible": True,
        "date_posted": util.get_current_timestamp(),
        "date_updated": util.get_current_timestamp(),
        "source": username
    }

    # Add field for research programs
    if category == "Research" and field:
        new_listing["field"] = field

    # Validate required fields
    if not new_listing["company_name"]:
        util.fail("Missing required field: Company Name")
    if not new_listing["title"]:
        util.fail("Missing required field: Title")

    listings.append(new_listing)
    util.save_listings_to_json(listings)

    # Set outputs
    util.set_output("commit_message", f"Add {company_name} - {title}")
    util.set_output("contributor_name", username)
    email = data.get("email_associated_with_your_github_account_(optional)", "")
    util.set_output("contributor_email", email if email else "actions@github.com")

    print(f"Successfully added: {company_name} - {title}")


def handle_edit_opportunity(data, username):
    """Editing is not supported via automation. Direct users to close + re-add."""
    util.fail(
        "Editing via issues is not currently supported. "
        "To update a listing, please:\n"
        "1. Open a 'Close Opportunity' issue to remove the old listing\n"
        "2. Open a new 'Add Opportunity' issue with the corrected details"
    )


def handle_close_opportunity(data, username):
    """Handle closing an opportunity."""
    listings = util.get_listings_from_json()

    company_name = data.get("company/organization_name", "").strip()
    title = data.get("program/role_title", "").strip()
    url = data.get("job_url_(optional)", "").strip()

    if not company_name or not title:
        util.fail("Missing required fields: Company Name and Title")

    # Find matching listings
    matches = []
    for listing in listings:
        if (listing["company_name"].lower() == company_name.lower() and
            listing["title"].lower() == title.lower()):
            matches.append(listing)

    # If URL provided, filter by URL
    if url:
        url = util.clean_url(url)
        matches = [m for m in matches if m["url"] == url]

    if not matches:
        util.fail(f"Could not find opportunity: {company_name} - {title}")

    if len(matches) > 1:
        util.fail(f"Found multiple matches for {company_name} - {title}. Please provide the URL to identify the specific listing.")

    # Mark as inactive
    matches[0]["active"] = False
    matches[0]["date_updated"] = util.get_current_timestamp()

    util.save_listings_to_json(listings)

    util.set_output("commit_message", f"Close {company_name} - {title}")
    util.set_output("contributor_name", username)
    util.set_output("contributor_email", "actions@github.com")

    print(f"Successfully closed: {company_name} - {title}")


def main():
    if len(sys.argv) < 2:
        util.fail("Missing event data file path")

    event_path = sys.argv[1]
    with open(event_path, "r") as f:
        event = json.load(f)

    issue = event.get("issue", {})
    body = issue.get("body", "")
    labels = [l.get("name", "") for l in issue.get("labels", [])]
    username = issue.get("user", {}).get("login", "unknown")

    # Parse the issue body
    data = parse_issue_body(body, labels)

    # Check if this is a quick add
    is_quick_add = "quick_add" in labels

    # Handle based on label
    if "new_opportunity" in labels:
        handle_new_opportunity(data, username, is_quick_add=is_quick_add)
    elif "edit_opportunity" in labels:
        handle_edit_opportunity(data, username)
    elif "close_opportunity" in labels:
        handle_close_opportunity(data, username)
    else:
        util.fail(f"Unknown issue type. Labels: {labels}")


if __name__ == "__main__":
    main()
