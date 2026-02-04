"""
Utility functions for managing underclassmen opportunity listings.
"""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LISTINGS_FILE = os.path.join(SCRIPT_DIR, "listings.json")
README_FILE = os.path.join(SCRIPT_DIR, "..", "..", "README.md")
PST = ZoneInfo("America/Los_Angeles")

# Required fields for each listing
REQUIRED_FIELDS = [
    "id",
    "company_name",
    "title",
    "url",
    "locations",
    "season",
    "opportunity_type",
    "target_year",
    "sponsorship",
    "active",
    "is_visible",
    "date_posted",
    "date_updated",
    "source"
]


def get_listings_from_json():
    """Load listings from the JSON file."""
    if not os.path.exists(LISTINGS_FILE):
        return []
    with open(LISTINGS_FILE, "r") as f:
        return json.load(f)


def save_listings_to_json(listings):
    """Save listings to the JSON file."""
    with open(LISTINGS_FILE, "w") as f:
        json.dump(listings, f, indent=2)


def check_schema(listings):
    """Validate that all listings have required fields."""
    for listing in listings:
        for field in REQUIRED_FIELDS:
            if field not in listing:
                raise ValueError(f"Listing {listing.get('id', 'unknown')} missing field: {field}")
    return True


def sort_listings(listings):
    """Sort listings by active status, date posted (newest first), then company name."""
    return sorted(
        listings,
        key=lambda x: (
            not x.get("active", False),  # Active first
            -x.get("date_posted", 0),     # Newest first
            x.get("company_name", "").lower()
        )
    )


def format_locations(locations):
    """Format location list for display."""
    if not locations:
        return "N/A"
    if len(locations) == 1:
        return locations[0]
    if len(locations) <= 3:
        return " | ".join(locations)
    # For many locations, use expandable details
    return f"<details><summary>{len(locations)} locations</summary>{' | '.join(locations)}</details>"


def get_sponsorship_badge(sponsorship):
    """Return emoji badge for sponsorship status."""
    badges = {
        "Does Not Offer Sponsorship": " :no_entry_sign:",
        "U.S. Citizenship Required": " :us:",
        "U.S. Work Authorization Required": " :no_entry_sign:",
    }
    return badges.get(sponsorship, "")


def get_status_badge(active):
    """Return emoji badge for active status."""
    return "" if active else " :lock:"


def format_link(url):
    """Format the application link as a button."""
    # Add UTM parameters for tracking
    separator = "&" if "?" in url else "?"
    tracked_url = f"{url}{separator}utm_source=underclassmen-opportunities"
    return f'<a href="{tracked_url}"><img src="https://i.imgur.com/u1KNU8z.png" width="118" alt="Apply"></a>'


def format_date(timestamp):
    """Format Unix timestamp as readable date."""
    dt = datetime.fromtimestamp(timestamp, tz=PST)
    return dt.strftime("%b %d")


def create_md_table(listings, prev_company=None):
    """
    Create a markdown table from listings.
    Uses arrow symbol for duplicate companies.
    """
    rows = []
    header = "| Company | Role | Location | Application | Date Posted |"
    separator = "| ------- | ---- | -------- | ----------- | ----------- |"
    rows.append(header)
    rows.append(separator)

    current_company = prev_company
    for listing in listings:
        if not listing.get("is_visible", True):
            continue

        company = listing["company_name"]
        # Use arrow for repeated company names
        display_company = company if company != current_company else "↳"
        current_company = company

        title = listing["title"]
        title += get_sponsorship_badge(listing.get("sponsorship", ""))
        title += get_status_badge(listing.get("active", True))

        location = format_locations(listing.get("locations", []))
        link = format_link(listing["url"]) if listing.get("active", True) else ":lock:"
        date = format_date(listing["date_posted"])

        row = f"| {display_company} | {title} | {location} | {link} | {date} |"
        rows.append(row)

    return "\n".join(rows)


def embed_table(filepath, table, start_marker, end_marker):
    """Embed the generated table between markers in a file."""
    with open(filepath, "r") as f:
        content = f.read()

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        raise ValueError(f"Could not find markers in {filepath}")

    new_content = (
        content[:start_idx + len(start_marker)]
        + "\n"
        + table
        + "\n"
        + content[end_idx:]
    )

    with open(filepath, "w") as f:
        f.write(new_content)


def set_output(name, value):
    """Set a GitHub Actions output variable."""
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            # Handle multiline values
            if "\n" in str(value):
                import uuid
                delimiter = uuid.uuid4().hex
                f.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")
            else:
                f.write(f"{name}={value}\n")
    else:
        print(f"::set-output name={name}::{value}")


def fail(message):
    """Set error output and exit."""
    set_output("error_message", message)
    print(f"Error: {message}")
    exit(1)


def get_current_timestamp():
    """Get current Unix timestamp."""
    return int(datetime.now(tz=PST).timestamp())


def generate_uuid():
    """Generate a new UUID for a listing."""
    import uuid
    return str(uuid.uuid4())


def clean_url(url):
    """Clean and normalize a URL."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    # Remove common tracking parameters
    tracking_params = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"]
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    cleaned_params = {k: v for k, v in params.items() if k not in tracking_params}
    cleaned_query = urlencode(cleaned_params, doseq=True)
    cleaned_url = urlunparse(parsed._replace(query=cleaned_query))
    return cleaned_url
