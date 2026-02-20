#!/usr/bin/env python3
"""
Update README.md with the latest listings from listings.json.

This script reads the listings data, generates markdown tables,
and embeds them in the README file between the marker comments.
"""

import os
from datetime import datetime
import util


def main():
    try:
        # Load listings
        listings = util.get_listings_from_json()

        # Validate schema
        util.check_schema(listings)

        # Separate listings by category
        internship_listings = []
        program_listings = []
        research_listings = []
        scholarship_listings = []

        for listing in listings:
            if not listing.get("is_visible", True):
                continue

            category = listing.get("category", "Internship")
            if category == "Internship":
                internship_listings.append(listing)
            elif category == "Program":
                program_listings.append(listing)
            elif category == "Research":
                research_listings.append(listing)
            elif category == "Scholarship":
                scholarship_listings.append(listing)

        # Sort listings
        internship_listings = util.sort_listings(internship_listings)
        program_listings = util.sort_listings(program_listings)
        research_listings = util.sort_listings(research_listings)
        scholarship_listings = util.sort_listings(scholarship_listings)

        # Generate tables
        internships_table = create_internships_table(internship_listings)
        programs_table = create_programs_table(program_listings)
        research_table = create_research_table(research_listings)
        scholarships_table = create_scholarships_table(scholarship_listings)

        # Get README path
        readme_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..",
            "README.md"
        )

        # Embed tables in README
        util.embed_table(
            readme_path,
            internships_table,
            "<!-- INTERNSHIPS_TABLE_START -->",
            "<!-- INTERNSHIPS_TABLE_END -->"
        )

        util.embed_table(
            readme_path,
            programs_table,
            "<!-- PROGRAMS_TABLE_START -->",
            "<!-- PROGRAMS_TABLE_END -->"
        )

        util.embed_table(
            readme_path,
            research_table,
            "<!-- RESEARCH_TABLE_START -->",
            "<!-- RESEARCH_TABLE_END -->"
        )

        util.embed_table(
            readme_path,
            scholarships_table,
            "<!-- SCHOLARSHIPS_TABLE_START -->",
            "<!-- SCHOLARSHIPS_TABLE_END -->"
        )

        # Set commit message
        now = datetime.now(util.PST)
        timestamp = now.strftime("%Y-%m-%d %H:%M PST")
        util.set_output("commit_message", f"Update README ({timestamp})")

        print(f"Successfully updated README:")
        print(f"  - {len(internship_listings)} internships")
        print(f"  - {len(program_listings)} programs")
        print(f"  - {len(research_listings)} research opportunities")
        print(f"  - {len(scholarship_listings)} scholarships")

    except Exception as e:
        util.fail(str(e))


def create_internships_table(listings):
    """Create a table for internships."""
    rows = []
    header = "| Company | Role | Location | Application | Date Posted |"
    separator = "| ------- | ---- | -------- | ----------- | ----------- |"
    rows.append(header)
    rows.append(separator)

    prev_company = None
    prev_title = None
    for listing in listings:
        company = listing["company_name"]
        title = listing["title"]

        # Only use arrow when same company but DIFFERENT role
        if company == prev_company and title != prev_title:
            display_company = "↳"
        else:
            display_company = company
        prev_company = company
        prev_title = title

        display_title = util.sanitize_table_cell(title)
        display_title += util.get_sponsorship_badge(listing.get("sponsorship", ""))
        display_title += util.get_status_badge(listing.get("active", True))

        location = util.format_locations(listing.get("locations", []))
        link = util.format_link(listing["url"]) if listing.get("active", True) else ":lock:"
        date = util.format_date(listing["date_posted"])

        row = f"| {util.sanitize_table_cell(display_company)} | {display_title} | {location} | {link} | {date} |"
        rows.append(row)

    return "\n".join(rows)


def create_programs_table(listings):
    """Create a table for programs (fellowships, externships, etc.)."""
    rows = []
    header = "| Company | Program | Type | Location | Application | Date Posted |"
    separator = "| ------- | ------- | ---- | -------- | ----------- | ----------- |"
    rows.append(header)
    rows.append(separator)

    for listing in listings:
        company = util.sanitize_table_cell(listing["company_name"])
        title = util.sanitize_table_cell(listing["title"])
        title += util.get_sponsorship_badge(listing.get("sponsorship", ""))
        title += util.get_status_badge(listing.get("active", True))

        opp_type = util.sanitize_table_cell(listing.get("opportunity_type", ""))
        location = util.format_locations(listing.get("locations", []))
        link = util.format_link(listing["url"]) if listing.get("active", True) else ":lock:"
        date = util.format_date(listing["date_posted"])

        row = f"| {company} | {title} | {opp_type} | {location} | {link} | {date} |"
        rows.append(row)

    return "\n".join(rows)


def create_research_table(listings):
    """Create a table for research programs."""
    rows = []
    header = "| University/Organization | Program | Field | Location | Application | Date Posted |"
    separator = "| ----------------------- | ------- | ----- | -------- | ----------- | ----------- |"
    rows.append(header)
    rows.append(separator)

    for listing in listings:
        company = util.sanitize_table_cell(listing["company_name"])
        title = util.sanitize_table_cell(listing["title"])
        title += util.get_sponsorship_badge(listing.get("sponsorship", ""))
        title += util.get_status_badge(listing.get("active", True))

        field = util.sanitize_table_cell(listing.get("field", ""))
        location = util.format_locations(listing.get("locations", []))
        link = util.format_link(listing["url"]) if listing.get("active", True) else ":lock:"
        date = util.format_date(listing["date_posted"])

        row = f"| {company} | {title} | {field} | {location} | {link} | {date} |"
        rows.append(row)

    return "\n".join(rows)


def create_scholarships_table(listings):
    """Create a table for scholarships."""
    rows = []
    header = "| Organization | Scholarship | Amount | Application | Deadline |"
    separator = "| ------------ | ----------- | ------ | ----------- | -------- |"
    rows.append(header)
    rows.append(separator)

    for listing in listings:
        company = util.sanitize_table_cell(listing["company_name"])
        title = util.sanitize_table_cell(listing["title"])
        title += util.get_status_badge(listing.get("active", True))

        amount = util.sanitize_table_cell(listing.get("scholarship_amount", "Varies"))
        link = util.format_link(listing["url"]) if listing.get("active", True) else ":lock:"
        deadline = util.sanitize_table_cell(listing.get("deadline", "Varies"))

        row = f"| {company} | {title} | {amount} | {link} | {deadline} |"
        rows.append(row)

    return "\n".join(rows)


if __name__ == "__main__":
    main()
