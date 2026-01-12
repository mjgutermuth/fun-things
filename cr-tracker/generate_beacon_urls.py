#!/usr/bin/env python3
"""
Generate Beacon URLs for Critical Role Cooldown episodes based on observed patterns
"""

import csv
import re

def slugify(text):
    """Convert text to URL-friendly slug"""
    # Convert to lowercase
    text = text.lower()
    # Replace special characters and spaces with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def generate_beacon_url(series, episode_number, title, airdate):
    """
    Generate Beacon URL based on patterns observed:

    Campaign 3: https://beacon.tv/content/3-83-cr-cooldown-c3-e83
    Campaign 4: https://beacon.tv/content/cr-cooldown-c4-e001
    Age of Umbra: https://beacon.tv/content/age-of-umbra-cooldown-e1
    Wildemount Wildlings: https://beacon.tv/content/wildemount-wildings-cooldown-e1
    Thresher: https://beacon.tv/content/thresher-cooldown-e1
    ExU Divergence: https://beacon.tv/content/exu-cooldown-divergence-e1
    Specials: https://beacon.tv/content/[descriptive-slug]
    """

    base_url = "https://beacon.tv/content/"

    # Campaign 3 cooldowns - pattern: 3-{ep}-cr-cooldown-c3-e{ep}
    if 'C3x' in episode_number and episode_number.startswith('C3x'):
        ep_num = episode_number.replace('C3x', '')
        return f"{base_url}3-{ep_num}-cr-cooldown-c3-e{ep_num}"

    # Campaign 4 cooldowns - pattern: cr-cooldown-c4-e{ep:03d}
    if 'C4x' in episode_number and episode_number.startswith('C4x'):
        ep_num = episode_number.replace('C4x', '')
        ep_num_padded = ep_num.zfill(3)  # Pad to 3 digits
        return f"{base_url}cr-cooldown-c4-e{ep_num_padded}"

    # Age of Umbra - pattern: age-of-umbra-cooldown-e{ep}
    if series == 'Age of Umbra' and episode_number.isdigit():
        return f"{base_url}age-of-umbra-cooldown-e{episode_number}"

    # Wildemount Wildlings - pattern: wildemount-wildings-cooldown-e{ep}
    # Note: "Wildings" not "Wildlings" in URL
    if 'Wildemount Wildlings' in series and episode_number.isdigit():
        return f"{base_url}wildemount-wildings-cooldown-e{episode_number}"

    # Thresher - pattern: thresher-cooldown-e{ep}
    if series == 'Thresher' and episode_number.isdigit():
        return f"{base_url}thresher-cooldown-e{episode_number}"

    # ExU Divergence - pattern: exu-cooldown-divergence-e{ep}
    if 'E4x' in episode_number and 'Divergence' in title:
        ep_num = episode_number.replace('E4x', '')
        return f"{base_url}exu-cooldown-divergence-e{ep_num}"

    # Special cases - Daggerheart
    if 'Menagerie Returns' in title:
        return f"{base_url}daggerheart-cooldown-the-menagerie-returns-live-one-shot-open-beta"

    if 'Ménagerie a Trois' in title or 'Menagerie a Trois' in title:
        return f"{base_url}cr-cooldown-dh-03-menagerie-a-trois"

    # Candela Obscura Live
    if 'Candela' in title and 'Silver Screen' in title:
        return f"{base_url}candela-obscura-cooldown-candela-obscura-live-the-circle-of-the-silver-screen"

    # Jester and Fjord's Wedding
    if 'Jester and Fjord' in title or "Fjord's Wedding" in title:
        return f"{base_url}cr-cooldown-jester-and-fjords-wedding-live-from-radio-city-music-hall"

    # Inside The Mighty Nein - specific patterns based on episode ranges
    if series == 'Inside The Mighty Nein':
        if 'Premiere Cocktail Party' in title:
            return f"{base_url}inside-the-mighty-nein-premiere-cocktail-party"
        elif '1-5' in episode_number or 'Episodes 1-5' in title:
            return f"{base_url}inside-the-mighty-nein-episodes-1-5"
        elif '6-8' in episode_number or 'Episodes 6-8' in title:
            return f"{base_url}inside-the-mighty-nein-episodes-6-8"
        else:
            # Generic pattern for future episodes
            slug = slugify(title)
            return f"{base_url}{slug}"

    # Generic specials - try to create a reasonable slug from title
    if 'Special' in episode_number or not episode_number.isdigit():
        # Extract the meaningful part of the title
        title_clean = title.replace('Cooldown:', '').replace('(Special)', '').strip()
        slug = slugify(title_clean)
        return f"{base_url}cr-cooldown-{slug}"

    # Other series - generic pattern
    series_slug = slugify(series)
    return f"{base_url}{series_slug}-cooldown-e{episode_number}"

def main():
    """Read beacon_links_needed.csv and generate URLs"""

    input_file = 'beacon_links_needed.csv'
    output_file = 'beacon_links_generated.csv'

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Generate URLs for each row
    for row in rows:
        series = row['series']
        episode_number = row['episode_number']
        title = row['title']
        airdate = row['airdate']

        generated_url = generate_beacon_url(series, episode_number, title, airdate)
        row['generated_url'] = generated_url
        row['manual_check'] = ''  # Column for marking if URL needs verification

    # Write output
    fieldnames = ['series', 'episode_number', 'title', 'airdate', 'current_url', 'generated_url', 'manual_check']

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✓ Generated URLs for {len(rows)} episodes")
    print(f"✓ Saved to {output_file}")
    print("\nSample URLs generated:")
    for i, row in enumerate(rows[:5]):
        print(f"  {row['episode_number']:10} → {row['generated_url']}")

    # Count by pattern type
    print("\nPattern breakdown:")
    patterns = {}
    for row in rows:
        if 'C3x' in row['episode_number']:
            patterns['Campaign 3'] = patterns.get('Campaign 3', 0) + 1
        elif 'C4x' in row['episode_number']:
            patterns['Campaign 4'] = patterns.get('Campaign 4', 0) + 1
        elif row['series'] == 'Age of Umbra':
            patterns['Age of Umbra'] = patterns.get('Age of Umbra', 0) + 1
        elif 'Wildemount' in row['series']:
            patterns['Wildemount Wildlings'] = patterns.get('Wildemount Wildlings', 0) + 1
        elif row['series'] == 'Thresher':
            patterns['Thresher'] = patterns.get('Thresher', 0) + 1
        elif 'E4x' in row['episode_number']:
            patterns['ExU Divergence'] = patterns.get('ExU Divergence', 0) + 1
        else:
            patterns['Other/Special'] = patterns.get('Other/Special', 0) + 1

    for pattern, count in sorted(patterns.items()):
        print(f"  {pattern:25}: {count:3} episodes")

if __name__ == '__main__':
    main()
