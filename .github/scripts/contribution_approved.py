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


def handle_new_opportunity(data, username):
    """Handle adding a new opportunity."""
    listings = util.get_listings_from_json()

    # Clean and validate URL
    url = util.clean_url(data.get("link_to_opportunity_posting", ""))
    if not url:
        util.fail("Missing required field: URL")

    # Check for duplicates
    for listing in listings:
        if listing["url"] == url:
            util.fail(f"Duplicate: This opportunity already exists (ID: {listing['id']})")

    # Parse locations
    locations_str = data.get("location", "")
    locations = [loc.strip() for loc in locations_str.split("|") if loc.strip()]

    # Parse target year
    target_year_str = data.get("target_year", "")
    target_year = [y.strip() for y in target_year_str.split(",") if y.strip()]

    # Create new listing
    new_listing = {
        "id": util.generate_uuid(),
        "company_name": data.get("company/organization_name", "").strip(),
        "title": data.get("program/role_title", "").strip(),
        "url": url,
        "locations": locations,
        "season": data.get("what_season_is_this_opportunity_for?", "Summer"),
        "opportunity_type": data.get("type_of_opportunity", "Internship"),
        "target_year": target_year,
        "sponsorship": data.get("sponsorship/citizenship_requirements", "Not Specified"),
        "active": data.get("is_this_opportunity_currently_accepting_applications?", "Yes") == "Yes",
        "is_visible": True,
        "date_posted": util.get_current_timestamp(),
        "date_updated": util.get_current_timestamp(),
        "source": username
    }

    # Validate required fields
    if not new_listing["company_name"]:
        util.fail("Missing required field: Company Name")
    if not new_listing["title"]:
        util.fail("Missing required field: Title")

    listings.append(new_listing)
    util.save_listings_to_json(listings)

    # Set outputs
    company = new_listing["company_name"]
    title = new_listing["title"]
    util.set_output("commit_message", f"Add {company} - {title}")
    util.set_output("contributor_name", username)
    email = data.get("email_associated_with_your_github_account_(optional)", "")
    util.set_output("contributor_email", email if email else "actions@github.com")

    print(f"Successfully added: {company} - {title}")


def handle_edit_opportunity(data, username):
    """Handle editing an existing opportunity."""
    listings = util.get_listings_from_json()

    url = util.clean_url(data.get("url_of_the_opportunity_to_edit", ""))
    if not url:
        util.fail("Missing required field: URL of opportunity to edit")

    # Find the listing
    found = None
    for listing in listings:
        if listing["url"] == url:
            found = listing
            break

    if not found:
        util.fail(f"Could not find opportunity with URL: {url}")

    # Parse changes from the description
    changes_text = data.get("what_changes_need_to_be_made?", "")

    # Update timestamp
    found["date_updated"] = util.get_current_timestamp()

    util.save_listings_to_json(listings)

    company = found["company_name"]
    title = found["title"]
    util.set_output("commit_message", f"Edit {company} - {title}")
    util.set_output("contributor_name", username)
    util.set_output("contributor_email", "actions@github.com")

    print(f"Successfully edited: {company} - {title}")


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

    # Handle based on label
    if "new_opportunity" in labels:
        handle_new_opportunity(data, username)
    elif "edit_opportunity" in labels:
        handle_edit_opportunity(data, username)
    elif "close_opportunity" in labels:
        handle_close_opportunity(data, username)
    else:
        util.fail(f"Unknown issue type. Labels: {labels}")


if __name__ == "__main__":
    main()
