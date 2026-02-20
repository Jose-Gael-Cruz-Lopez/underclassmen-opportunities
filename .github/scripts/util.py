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
    "category",  # Internship, Program, or Research
    "opportunity_type",
    "target_year",
    "sponsorship",
    "active",
    "is_visible",
    "date_posted",
    "date_updated",
    "source"
]

# Valid categories
VALID_CATEGORIES = ["Internship", "Program", "Research", "Scholarship"]


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


def sanitize_table_cell(value):
    """Escape pipe characters and newlines in a markdown table cell value."""
    if not isinstance(value, str):
        value = str(value)
    value = value.replace("|", "\\|")
    value = value.replace("\n", " ")
    return value.strip()


def format_locations(locations):
    """Format location list for display."""
    if not locations:
        return "N/A"
    if len(locations) == 1:
        return sanitize_table_cell(locations[0])
    if len(locations) <= 3:
        return ", ".join(sanitize_table_cell(loc) for loc in locations)
    # For many locations, use expandable details
    joined = ", ".join(sanitize_table_cell(loc) for loc in locations)
    return f"<details><summary>{len(locations)} locations</summary>{joined}</details>"


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
    """Format the application link as a blue button."""
    # Blue "Apply" button using shields.io
    button_url = "https://img.shields.io/badge/Apply-blue?style=for-the-badge"
    return f'<a href="{url}"><img src="{button_url}" alt="Apply"></a>'


def format_date(timestamp):
    """Format Unix timestamp as readable date."""
    dt = datetime.fromtimestamp(timestamp, tz=PST)
    return dt.strftime("%b %d")


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
