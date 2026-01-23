#!/usr/bin/env python3
"""
Unit tests for CR-Tracker scrapers
"""

import unittest
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wiki_scraper import clean_text, parse_date, parse_runtime
from beacon_scraper import generate_schedule_urls, extract_beacon_content


class TestWikiScraperHelpers(unittest.TestCase):
    """Tests for wiki_scraper helper functions"""

    def test_clean_text_removes_edit_tags(self):
        self.assertEqual(clean_text("Episode Title[edit]"), "Episode Title")

    def test_clean_text_removes_reference_numbers(self):
        self.assertEqual(clean_text("Episode Title[1][2]"), "Episode Title")

    def test_clean_text_strips_whitespace(self):
        self.assertEqual(clean_text("  Episode Title  "), "Episode Title")

    def test_clean_text_handles_empty(self):
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text(None), "")

    def test_parse_date_full_month(self):
        self.assertEqual(parse_date("January 16, 2026"), "2026-01-16")

    def test_parse_date_abbreviated_month(self):
        self.assertEqual(parse_date("Jan 16, 2026"), "2026-01-16")

    def test_parse_date_iso_format(self):
        self.assertEqual(parse_date("2026-01-16"), "2026-01-16")

    def test_parse_date_european_format(self):
        self.assertEqual(parse_date("16 January 2026"), "2026-01-16")

    def test_parse_date_handles_empty(self):
        self.assertEqual(parse_date(""), "")
        self.assertEqual(parse_date(None), "")

    def test_parse_runtime_full_format(self):
        self.assertEqual(parse_runtime("4:15:13"), "4:15:13")

    def test_parse_runtime_short_format(self):
        self.assertEqual(parse_runtime("45:30"), "45:30:00")

    def test_parse_runtime_handles_empty(self):
        self.assertEqual(parse_runtime(""), "")
        self.assertEqual(parse_runtime(None), "")


class TestBeaconScraperHelpers(unittest.TestCase):
    """Tests for beacon_scraper helper functions"""

    def test_generate_schedule_urls_finds_mondays(self):
        # Start on a Wednesday, should find the next Monday
        start = datetime(2024, 5, 8)  # Wednesday
        end = datetime(2024, 5, 15)   # Wednesday

        urls = generate_schedule_urls(start, end)

        # Should find Monday May 13
        dates = [date for date, url, source in urls]
        self.assertTrue(any(d.day == 13 and d.month == 5 for d in dates))

    def test_generate_schedule_urls_formats_correctly(self):
        start = datetime(2024, 5, 13)  # Monday
        end = datetime(2024, 5, 13)

        urls = generate_schedule_urls(start, end)

        # Check critrole.com URL format
        critrole_urls = [url for date, url, source in urls if source == 'critrole']
        self.assertTrue(any('may-13th-2024' in url for url in critrole_urls))

    def test_generate_schedule_urls_ordinal_suffixes(self):
        # Test 1st, 2nd, 3rd, 4th
        test_cases = [
            (datetime(2024, 7, 1), '1st'),   # July 1st
            (datetime(2024, 9, 2), '2nd'),   # Sept 2nd
            (datetime(2024, 6, 3), '3rd'),   # June 3rd
            (datetime(2024, 5, 6), '6th'),   # May 6th
        ]

        for start, expected_suffix in test_cases:
            urls = generate_schedule_urls(start, start)
            critrole_urls = [url for date, url, source in urls if source == 'critrole']
            if critrole_urls:
                self.assertTrue(
                    any(expected_suffix in url for url in critrole_urls),
                    f"Expected {expected_suffix} in URL for {start}"
                )


class TestBeaconContentExtraction(unittest.TestCase):
    """Tests for beacon content extraction"""

    def test_extract_cooldown_content(self):
        html = """
        <html><body>
        <p>Critical Role Cooldown: Campaign 4, Episode 12</p>
        </body></html>
        """
        content = extract_beacon_content(html, datetime(2024, 5, 13))

        cooldowns = [c for c in content if c['series'] == 'Critical Role Cooldown']
        self.assertEqual(len(cooldowns), 1)
        self.assertEqual(cooldowns[0]['campaign'], 'Campaign 4')
        self.assertEqual(cooldowns[0]['episode_number'], '12')

    def test_extract_fireside_chat_with_guest(self):
        html = """
        <html><body>
        <p>Fireside Chat with Sam Riegel</p>
        </body></html>
        """
        content = extract_beacon_content(html, datetime(2024, 5, 13))

        firesides = [c for c in content if c['series'] == 'Fireside Chat']
        self.assertEqual(len(firesides), 1)
        self.assertIn('Sam', firesides[0]['title'])  # Regex captures first word after "with"

    def test_extract_weird_kids_episode(self):
        html = """
        <html><body>
        <p>Weird Kids Episode 5</p>
        </body></html>
        """
        content = extract_beacon_content(html, datetime(2024, 5, 13))

        weird_kids = [c for c in content if c['series'] == 'Weird Kids']
        self.assertEqual(len(weird_kids), 1)
        self.assertEqual(weird_kids[0]['episode_number'], '5')

    def test_extract_inside_mighty_nein(self):
        html = """
        <html><body>
        <p>Inside The Mighty Nein | Episodes 1-5</p>
        </body></html>
        """
        content = extract_beacon_content(html, datetime(2024, 5, 13))

        imn = [c for c in content if c['series'] == 'Inside The Mighty Nein']
        self.assertEqual(len(imn), 1)
        self.assertEqual(imn[0]['episode_number'], '1-5')

    def test_extract_no_content(self):
        html = """
        <html><body>
        <p>Just some random text with no beacon content</p>
        </body></html>
        """
        content = extract_beacon_content(html, datetime(2024, 5, 13))
        self.assertEqual(len(content), 0)


class TestDataValidation(unittest.TestCase):
    """Tests for data validation (placeholder for validate_data.py tests)"""

    def test_placeholder(self):
        # Will be expanded when validate_data.py is created
        pass


if __name__ == '__main__':
    unittest.main()
