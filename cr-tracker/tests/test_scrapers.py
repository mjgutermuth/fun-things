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
from beacon_scraper import (
    generate_schedule_urls, extract_beacon_content, normalize_live_show_title,
    parse_generic_title, parse_release_date_from_li, is_excluded_from_generic_fallback,
    is_manually_reworded_generic_duplicate,
)


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


class TestLiveShowDedup(unittest.TestCase):
    """Tests for normalize_live_show_title, which folds away cosmetic reworking
    of a live show's title between weekly critrole.com schedule postings so the
    same release doesn't get added to the CSV twice."""

    def test_strips_critical_role_filler_segment(self):
        a = 'Oaths & Ash | Critical Role | Indianapolis Live Show 2025'
        b = 'Oaths & Ash | Indianapolis Live Show 2025'
        self.assertEqual(normalize_live_show_title(a), normalize_live_show_title(b))

    def test_keeps_cooldown_distinct_from_main_show(self):
        main = 'Oaths & Ash | Indianapolis Live Show 2025'
        cooldown = 'Critical Role Cooldown | Oaths & Ash | Indianapolis Live Show 2025'
        self.assertNotEqual(normalize_live_show_title(main), normalize_live_show_title(cooldown))

    def test_keeps_distinct_backstage_pieces_separate(self):
        vip_access = 'Darktow | Beacon Backstage Pass – VIP Access: Edinburgh Live Show 2026'
        road_to = 'Darktow | Beacon Backstage Pass – Road To Edinburgh Live Show 2026'
        self.assertNotEqual(normalize_live_show_title(vip_access), normalize_live_show_title(road_to))

    def test_keeps_main_show_distinct_from_cooldown_multi_segment(self):
        main = 'Darktow | | Echoes of Exandria | Edinburgh Live Show 2026'
        cooldown = 'Critical Role Cooldown | Darktow | Edinburgh Live Show 2026'
        self.assertNotEqual(normalize_live_show_title(main), normalize_live_show_title(cooldown))


class TestGenericFallback(unittest.TestCase):
    """Tests for the generic fallback pass (Pattern 13 in extract_beacon_content)
    that adds schedule content not caught by any of the other, series-specific
    patterns - covering the helpers it relies on, plus end-to-end behavior."""

    def test_parse_generic_title_episode(self):
        is_cooldown, series_key, ep = parse_generic_title('Age of Umbra: Sallowlands | Episode 4')
        self.assertFalse(is_cooldown)
        self.assertEqual(series_key, 'Age of Umbra: Sallowlands')
        self.assertEqual(ep, '4')

    def test_parse_generic_title_cooldown(self):
        is_cooldown, series_key, ep = parse_generic_title(
            'Critical Role Cooldown | Age of Umbra: Sallowlands | Episode 4')
        self.assertTrue(is_cooldown)
        self.assertEqual(series_key, 'Age of Umbra: Sallowlands')
        self.assertEqual(ep, '4')

    def test_parse_generic_title_non_standard(self):
        is_cooldown, series_key, ep = parse_generic_title('Age of Umbra: Sallowlands | Level Up!')
        self.assertFalse(is_cooldown)
        self.assertEqual(series_key, 'Age of Umbra: Sallowlands | Level Up!')
        self.assertEqual(ep, '')

    def test_parse_release_date_from_li_thursday(self):
        li = 'Airs Thursday, July 30th at 7pm Pacific on Twitch and YouTube'
        self.assertEqual(parse_release_date_from_li(li, datetime(2026, 7, 27)), '2026-07-30')

    def test_parse_release_date_from_li_no_weekday_falls_back_to_week_date(self):
        self.assertEqual(parse_release_date_from_li('no day mentioned here', datetime(2026, 7, 27)),
                          '2026-07-27')

    def test_excludes_third_party_shows(self):
        self.assertTrue(is_excluded_from_generic_fallback("Viva La Dirt League's Daggerheart: Azerim"))
        self.assertTrue(is_excluded_from_generic_fallback('Tales From The Stinky Dragon, Campaign 3: Kanon'))
        self.assertTrue(is_excluded_from_generic_fallback('UNEND Season 3'))
        self.assertTrue(is_excluded_from_generic_fallback('UNEND | Season 3 Roundtable'))
        self.assertTrue(is_excluded_from_generic_fallback('Critical Role Abridged'))
        self.assertTrue(is_excluded_from_generic_fallback('Something is coming…'))

    def test_does_not_exclude_bonus_content_of_in_scope_series(self):
        # Bonus/tutorial segments of an in-scope series aren't third-party -
        # they should still be added, just without an episode number.
        self.assertFalse(is_excluded_from_generic_fallback(
            'Get Your Sheet Together | Multiclassing in Daggerheart!'))
        self.assertFalse(is_excluded_from_generic_fallback(
            'Age of Umbra: Sallowlands | Level Up!'))

    def test_manually_reworded_generic_duplicate_matches_known_rows(self):
        self.assertTrue(is_manually_reworded_generic_duplicate(
            'Age of Umbra: Sallowlands | Episode 1', '1'))
        self.assertTrue(is_manually_reworded_generic_duplicate(
            'Critical Role Cooldown | Age of Umbra: Sallowlands | Episode 2', '2'))
        self.assertTrue(is_manually_reworded_generic_duplicate(
            'Age of Umbra: Sallowlands | Episode 6', '6'))
        self.assertTrue(is_manually_reworded_generic_duplicate(
            '[PROJEKT] Funball | Echoes of Exandria | Berlin Live Show 2026', ''))
        self.assertTrue(is_manually_reworded_generic_duplicate(
            'Tale Gate | Discussing Up To C4E31', ''))
        self.assertTrue(is_manually_reworded_generic_duplicate(
            'Episode 4 | Discussing Up To C4E31', ''))

    def test_manually_reworded_generic_duplicate_does_not_match_unlisted_episode(self):
        # Episode 7 hasn't been manually cleaned up, so it must NOT be
        # treated as a duplicate - it should still get added normally.
        self.assertFalse(is_manually_reworded_generic_duplicate(
            'Age of Umbra: Sallowlands | Episode 7', '7'))

    def test_fallback_adds_unrecognized_series(self):
        html = """
        <html><body>
        <div class="elementor-widget-container">
          <h3><strong>Age of Umbra: Sallowlands | Episode 4</strong></h3>
          <p>description</p>
          <ul>
            <li><strong><em>Airs Thursday, July 30th at 7pm Pacific on Twitch and YouTube</em></strong></li>
          </ul>
        </div>
        </body></html>
        """
        content = extract_beacon_content(html, datetime(2026, 7, 27))
        matches = [c for c in content if c['series'] == 'Age of Umbra: Sallowlands']
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['episode_number'], '4')
        self.assertEqual(matches[0]['release_date'], '2026-07-30')

    def test_fallback_skips_content_already_claimed_by_weird_kids_pattern(self):
        html = """
        <html><body>
        <div class="elementor-widget-container">
          <h3><strong>Weird Kids</strong></h3>
          <p>description</p>
          <ul>
            <li><strong><em>Episode 20 releases Tuesday, July 28th at 10am Pacific on YouTube</em></strong></li>
          </ul>
        </div>
        </body></html>
        """
        content = extract_beacon_content(html, datetime(2026, 7, 27))
        # Weird Kids' own pattern (Pattern 3) should claim this - the fallback
        # must not also add a second, differently-shaped row for it.
        weird_kids_rows = [c for c in content if 'weird kids' in c['title'].lower()
                           or c['series'] == 'Weird Kids']
        self.assertEqual(len(weird_kids_rows), 1)

    def test_fallback_excludes_third_party_widget(self):
        html = """
        <html><body>
        <div class="elementor-widget-container">
          <h3><strong>Viva La Dirt League's Daggerheart: Azerim</strong></h3>
          <p>description</p>
          <ul>
            <li><strong><em>Episode 29 releases Tuesday, July 28th at 12am Pacific on Beacon</em></strong></li>
          </ul>
        </div>
        </body></html>
        """
        content = extract_beacon_content(html, datetime(2026, 7, 27))
        self.assertEqual(len(content), 0)


class TestDataValidation(unittest.TestCase):
    """Tests for data validation (placeholder for validate_data.py tests)"""

    def test_placeholder(self):
        # Will be expanded when validate_data.py is created
        pass


if __name__ == '__main__':
    unittest.main()
