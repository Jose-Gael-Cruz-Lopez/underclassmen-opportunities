"""API-free intake fixtures; all production listing I/O is mocked."""

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.dont_write_bytecode = True
import util


def forbidden_external_call(*args, **kwargs):
    raise AssertionError("Fixtures must not call an external service")


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Import without requiring network/AI packages. The tested path supplies mocked
# page content and extracted data rather than calling these integrations.
requests_stub = types.ModuleType("requests")
requests_stub.get = forbidden_external_call
bs4_stub = types.ModuleType("bs4")
bs4_stub.BeautifulSoup = forbidden_external_call
openai_stub = types.ModuleType("openai")
openai_stub.OpenAI = forbidden_external_call
with patch.dict(sys.modules, {
    "requests": requests_stub,
    "bs4": bs4_stub,
    "openai": openai_stub,
}):
    auto_extract = load_script("auto_extract")
contribution_approved = load_script("contribution_approved")
assert auto_extract.util is util and contribution_approved.util is util


class RejectedExtraction(Exception):
    pass


class IntakeFixtures(unittest.TestCase):
    def setUp(self):
        self.listings_path = SCRIPTS / "listings.json"
        self.original_digest = hashlib.sha256(self.listings_path.read_bytes()).digest()
        self.saved = []
        self.outputs = {}
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(util, "get_listings_from_json", side_effect=lambda: []))
        self.stack.enter_context(patch.object(
            util, "save_listings_to_json",
            side_effect=lambda listings: self.saved.append(copy.deepcopy(listings)),
        ))
        self.stack.enter_context(patch.object(
            util, "set_output",
            side_effect=lambda name, value: self.outputs.update({name: value}),
        ))
        self.stack.enter_context(patch.object(util, "generate_uuid", return_value="fixture-id"))
        self.stack.enter_context(patch.object(util, "get_current_timestamp", return_value=1791950400))
        self.stack.enter_context(patch.object(
            util, "fail", side_effect=lambda message: self.reject(message),
        ))

    @staticmethod
    def reject(message):
        raise RejectedExtraction(message)

    def tearDown(self):
        self.assertEqual(
            self.original_digest,
            hashlib.sha256(self.listings_path.read_bytes()).digest(),
            "A fixture changed production listings.json",
        )

    def extract(self, **overrides):
        data = {
            "company_name": "Fixture University",
            "title": "Freshman Arts Scholarship",
            "category": "Scholarship",
            "opportunity_type": "Scholarship",
            "locations": ["Fixture, NY"],
            "is_underclassmen": True,
            "target_year": ["Freshman (1st year)"],
        }
        data.update(overrides)
        with tempfile.TemporaryDirectory(prefix="intake-fixture-") as directory:
            event_path = Path(directory) / "event.json"
            event_path.write_text(json.dumps({"issue": {
                "body": "### Link to Opportunity\nhttps://example.edu/scholarship",
                "user": {"login": "fixture"},
            }}))
            with (
                patch.object(sys, "argv", ["auto_extract.py", str(event_path)]),
                patch.object(auto_extract, "fetch_page_content", return_value={
                    "url": "https://example.edu/scholarship",
                    "title": "Fixture",
                    "text": "Fixture content",
                }),
                patch.object(auto_extract, "extract_with_openai", return_value=data),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                auto_extract.main()

    def test_requires_explicit_true_underclassmen_flag(self):
        for value in (False, None, "true", 1):
            with self.subTest(value=value):
                with self.assertRaisesRegex(RejectedExtraction, "did not explicitly confirm"):
                    self.extract(is_underclassmen=value)
                self.assertEqual(self.saved, [])

    def test_rejects_missing_or_invalid_target_year(self):
        for value in (None, [], "Freshman (1st year)", ["Junior"], [True], [{}]):
            with self.subTest(value=value):
                with self.assertRaisesRegex(RejectedExtraction, "missing or invalid target_year"):
                    self.extract(target_year=value)
                self.assertEqual(self.saved, [])

    def test_preserves_each_allowed_cohort_as_inactive_intake(self):
        for value in auto_extract.ALLOWED_TARGET_YEARS:
            with self.subTest(value=value):
                self.extract(target_year=[value])
                listing = self.saved[-1][0]
                self.assertEqual(listing["target_year"], [value])
                self.assertFalse(listing["active"])
                self.assertFalse(listing["is_visible"])
                self.assertEqual(listing["category"], "Scholarship")
                self.assertTrue(util.check_schema([listing]))
                self.assertIn("maintainer", self.outputs["warning"])

    def test_preserves_current_cohorts_and_removes_duplicates(self):
        self.extract(target_year=[
            "Freshman (1st year)", "Sophomore (2nd year)", "Freshman (1st year)",
        ])
        self.assertEqual(self.saved[-1][0]["target_year"], [
            "Freshman (1st year)", "Sophomore (2nd year)",
        ])

    def test_full_scholarship_template(self):
        body = """### Link to Opportunity Posting
https://example.edu/incoming-arts
### Company/Organization Name
Fixture University
### Program/Role Title
Incoming Arts Scholarship
### Category
Scholarship - Named first-/second-year or incoming college freshman awards
### Type of Opportunity
Scholarship
### Target Year
Incoming College Freshman
### Is this opportunity currently accepting applications?
Yes
"""
        self.approve(body, quick=False)
        listing = self.saved[-1][0]
        self.assertEqual(listing["target_year"], ["Incoming College Freshman"])

    def test_quick_scholarship_template(self):
        body = """### Link
https://example.edu/sophomore-journalism
### Company/Organization
Fixture Foundation
### Role/Program Name
Sophomore Journalism Scholarship
### Category
Scholarship
"""
        self.approve(body, quick=True)

    def approve(self, body, quick):
        data = contribution_approved.parse_issue_body(body, ["new_opportunity"])
        with contextlib.redirect_stdout(io.StringIO()):
            contribution_approved.handle_new_opportunity(data, "fixture", is_quick_add=quick)
        listing = self.saved[-1][0]
        self.assertEqual(listing["category"], "Scholarship")
        self.assertEqual(listing["opportunity_type"], "Scholarship")
        self.assertFalse(listing["active"])
        self.assertFalse(listing["is_visible"])
        self.assertTrue(util.check_schema([listing]))


if __name__ == "__main__":
    unittest.main()
