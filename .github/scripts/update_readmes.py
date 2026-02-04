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

        # Separate listings by type
        summer_listings = []
        yearround_listings = []

        for listing in listings:
            if not listing.get("is_visible", True):
                continue
            if listing.get("season") == "Year-Round":
                yearround_listings.append(listing)
            else:
                summer_listings.append(listing)

        # Sort listings
        summer_listings = util.sort_listings(summer_listings)
        yearround_listings = util.sort_listings(yearround_listings)

        # Generate tables
        summer_table = util.create_md_table(summer_listings)

        # Year-round table has different columns
        yearround_table = create_yearround_table(yearround_listings)

        # Get README path
        readme_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..",
            "README.md"
        )

        # Embed tables in README
        util.embed_table(
            readme_path,
            summer_table,
            "<!-- TABLE_START -->",
            "<!-- TABLE_END -->"
        )

        util.embed_table(
            readme_path,
            yearround_table,
            "<!-- YEARROUND_TABLE_START -->",
            "<!-- YEARROUND_TABLE_END -->"
        )

        # Set commit message
        now = datetime.now(util.PST)
        timestamp = now.strftime("%Y-%m-%d %H:%M PST")
        util.set_output("commit_message", f"Update README ({timestamp})")

        print(f"Successfully updated README with {len(summer_listings)} summer and {len(yearround_listings)} year-round opportunities")

    except Exception as e:
        util.fail(str(e))


def create_yearround_table(listings):
    """Create a table specifically for year-round programs."""
    rows = []
    header = "| Company | Program | Type | Application | Notes |"
    separator = "| ------- | ------- | ---- | ----------- | ----- |"
    rows.append(header)
    rows.append(separator)

    for listing in listings:
        company = listing["company_name"]
        title = listing["title"]
        title += util.get_sponsorship_badge(listing.get("sponsorship", ""))
        title += util.get_status_badge(listing.get("active", True))

        opp_type = listing.get("opportunity_type", "")
        link = util.format_link(listing["url"]) if listing.get("active", True) else ":lock:"
        notes = listing.get("notes", "")

        row = f"| {company} | {title} | {opp_type} | {link} | {notes} |"
        rows.append(row)

    return "\n".join(rows)


if __name__ == "__main__":
    main()
