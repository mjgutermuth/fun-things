#!/usr/bin/env python3
"""
Update Critical Role CSV to add canon tracking columns
"""

import csv

# Define canon episodes with their prerequisites
CANON_EPISODES = {
    # Campaign 1 Canon Content
    'Special|Specials|C1E36a|The Story of Vox Machina': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'None',
        'prerequisite_notes': 'Early C1 recap - watch anytime'
    },
    'Special|Specials|C2E52a|The Search For Grog': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'C1E115',
        'prerequisite_notes': 'After Campaign 1 finale'
    },
    'Special|Specials|C2E68a|The Search For Bob': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'C2E52a',
        'prerequisite_notes': 'After The Search For Grog'
    },
    'Special|Specials|C2E76a|Dalen\'s Closet': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'C2E68a',
        'prerequisite_notes': 'After The Search For Bob'
    },
    'Special|Specials|C2E86b|The Adventures of the Darrington Brigade': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'C1E115',
        'prerequisite_notes': 'After Campaign 1 finale (10 years later)'
    },

    # Campaign 2 Canon Content
    'Special|Specials|C3E040a|The Mighty Nein Reunited Part 1': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'C2E141',
        'prerequisite_notes': 'After Campaign 2 finale'
    },
    'Special|Specials|C3E040b|The Mighty Nein Reunited Part 2': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'C3E040a',
        'prerequisite_notes': 'After The Mighty Nein Reunited Part 1'
    },

    # Exandria Unlimited - all episodes are canon
    # Prime series (episodes 1-8)
    'Miniseries|Miniseries|1|The Nameless Ones': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'None',
        'prerequisite_notes': 'Standalone - no prerequisite'
    },
    'Miniseries|Miniseries|2|The Oh No Plateau': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU1',
        'prerequisite_notes': 'After EXU Prime E1'
    },
    'Miniseries|Miniseries|3|A Glorious Return': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU2',
        'prerequisite_notes': 'After EXU Prime E2'
    },
    'Miniseries|Miniseries|4|By the Road': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU3',
        'prerequisite_notes': 'After EXU Prime E3'
    },
    'Miniseries|Miniseries|5|A Test of Worth': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU4',
        'prerequisite_notes': 'After EXU Prime E4'
    },
    'Miniseries|Miniseries|6|The Gift Among the Green': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU5',
        'prerequisite_notes': 'After EXU Prime E5'
    },
    'Miniseries|Miniseries|7|Beyond the Heart City': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU6',
        'prerequisite_notes': 'After EXU Prime E6'
    },
    'Miniseries|Miniseries|8|What Comes Next': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU7',
        'prerequisite_notes': 'After EXU Prime E7'
    },

    # Kymal series
    'Miniseries|Miniseries|9|Exandria Unlimited: Kymal, Part 1': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU8',
        'prerequisite_notes': 'After EXU Prime + during Campaign 3'
    },
    'Miniseries|Miniseries|10|Exandria Unlimited: Kymal, Part 2': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU9',
        'prerequisite_notes': 'After EXU Kymal Part 1'
    },

    # Calamity series
    'Miniseries|Miniseries|11|Excelsior': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'C3E1',
        'prerequisite_notes': 'Historical lore - helpful after C3 starts'
    },
    'Miniseries|Miniseries|12|Bitterness and Dread': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU11',
        'prerequisite_notes': 'After EXU Calamity E1'
    },
    'Miniseries|Miniseries|13|Blood and Shadow': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU12',
        'prerequisite_notes': 'After EXU Calamity E2'
    },
    'Miniseries|Miniseries|14|Fire and Ruin': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU13',
        'prerequisite_notes': 'After EXU Calamity E3'
    },

    # Divergence series (EXU Season 4)
    'Miniseries|Exandria Unlimited|15|Give and Take': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU14',
        'prerequisite_notes': 'After EXU Calamity - post-Calamity era'
    },
    'Miniseries|Exandria Unlimited|16|Seven of Them': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU15',
        'prerequisite_notes': 'After EXU Divergence E1'
    },
    'Miniseries|Exandria Unlimited|17|Mirror and Key': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU16',
        'prerequisite_notes': 'After EXU Divergence E2'
    },
    'Miniseries|Exandria Unlimited|18|By Heart Alone': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'EXU17',
        'prerequisite_notes': 'After EXU Divergence E3'
    },

    # Campaign 3 Canon Specials
    'Special|Specials|C3E076a|The Mighty Nein Reunion: Echoes of the Solstice': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'C2E141',
        'prerequisite_notes': 'After Campaign 2 finale (post-Apogee Solstice)'
    },
    'Special|Specials|AU1E08a|Tag Team at the Teeth – The Misty Ascent': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'C3E1',
        'prerequisite_notes': 'Mighty Nein + Bells Hells crossover'
    },
    'Special|Specials|AU1E08b|Tag Team at the Teeth – Beyond the Shroud': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'AU1E08a',
        'prerequisite_notes': 'After Tag Team Part 1'
    },
    'Special|Specials|AU1E08d|Oaths & Ash – Indianapolis Live Show 2025': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'C3E1',
        'prerequisite_notes': 'Bells Hells live show'
    },
    'Special|Specials|C4E04b|Jester and Fjord\'s Wedding - Live from Radio City Music Hall': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'C2E141',
        'prerequisite_notes': 'After Campaign 2 finale'
    },

    # Lore specials
    'Special|Specials|C2E141f|Exandria: An Intimate History': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'None',
        'prerequisite_notes': 'World lore - watch anytime'
    },
    'Special|Specials|C3E051a|Exandria: An Intimate Appendix - Ruidus and the Gods': {
        'is_canon': 'TRUE',
        'prerequisite_episode': 'None',
        'prerequisite_notes': 'Lore about Ruidus - watch anytime'
    },
}

def update_csv(input_file, output_file):
    """Add canon columns to CSV"""
    rows = []

    # Read existing CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        # Add new headers
        new_headers = list(headers) + ['is_canon', 'prerequisite_episode', 'prerequisite_notes']

        for row in reader:
            # Create episode_id for lookup
            episode_id = row['episode_id']

            # Check if this episode is canon
            if episode_id in CANON_EPISODES:
                canon_info = CANON_EPISODES[episode_id]
                row['is_canon'] = canon_info['is_canon']
                row['prerequisite_episode'] = canon_info['prerequisite_episode']
                row['prerequisite_notes'] = canon_info['prerequisite_notes']
            else:
                # Default to non-canon
                row['is_canon'] = 'FALSE'
                row['prerequisite_episode'] = ''
                row['prerequisite_notes'] = ''

            rows.append(row)

    # Write updated CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Updated {len(rows)} episodes")
    canon_count = sum(1 for r in rows if r['is_canon'] == 'TRUE')
    print(f"📖 Marked {canon_count} episodes as canon")

if __name__ == '__main__':
    input_file = '/Users/melinda/workspace/fun-things/cr-tracker/cr_episodes_series_airdates.csv'
    output_file = '/Users/melinda/workspace/fun-things/cr-tracker/cr_episodes_series_airdates.csv'
    update_csv(input_file, output_file)
