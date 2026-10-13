#!/usr/bin/env python3
"""Offline structural checks for Ukrainian CEDICT. Python 3.9+, standard library.

Exit 0: checks passed; 1: invalid data; 2: unreadable input/usage error.
This is not linguistic, provenance, licensing, or human-review certification.
"""

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

STRINGS = ('id', 'traditional', 'simplified', 'pinyin', 'raw_source',
           'translation_status', 'review_status')
ARRAYS = ('english_segments', 'ukrainian_segments', 'uncertainty_flags',
          'uncertainty_notes')
BOOLS = ('model_reviewed', 'human_validation', 'has_known_uncertainty')
INTS = ('source_line', 'correction_count')
FIELDS = set(STRINGS + ARRAYS + BOOLS + INTS + ('review_rating_before_corrections',))
RATINGS = {'pass', 'minor', 'major', 'unresolved'}
FLAGS = {'translator_uncertainty', 'review_residual_uncertainty'}
HASH_FILES = {'dictionary.json', 'dictionary.csv', 'source.json', 'translation_prompt.txt'}
# Preserve complete Chinese references (including traditional|simplified pairs)
# and all bracketed text. Counter comparison also detects additions/repetitions.
HAN = r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323af]+'
REFERENCES = re.compile(HAN + r'(?:\|' + HAN + r')?(?:\[[^\]\n]+\])?|\[[^\]\n]+\]')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root):
    errors = []

    def check(ok, category, message):
        if not ok:
            errors.append(f'{category}: {message}')

    data = json.loads((root / 'dictionary.json').read_text(encoding='utf-8'))
    progress = json.loads((root / 'progress.json').read_text(encoding='utf-8'))
    source = json.loads((root / 'source.json').read_text(encoding='utf-8'))
    check(type(data) is list and bool(data), 'schema', 'dictionary must be a nonempty array')
    check(type(progress) is dict, 'schema', 'progress must be an object')
    check(type(source) is dict, 'schema', 'source must be an object')
    if errors:
        return errors, {}

    for index, row in enumerate(data):
        label = f'row {index}'
        if type(row) is not dict:
            check(False, 'schema', f'{label} must be an object')
            continue
        check(set(row) == FIELDS, 'schema', f'{label}: unexpected or missing fields')
        for key in STRINGS:
            check(type(row.get(key)) is str and bool(row[key].strip()),
                  'schema', f'{label}.{key} must be nonempty text')
        for key in ARRAYS:
            value = row.get(key)
            check(type(value) is list and all(type(s) is str and s.strip() for s in value),
                  'schema', f'{label}.{key} must be an array of nonempty strings')
        for key in BOOLS:
            check(type(row.get(key)) is bool, 'schema', f'{label}.{key} must be boolean')
        for key in INTS:
            check(type(row.get(key)) is int and row[key] >= (1 if key == 'source_line' else 0),
                  'schema', f'{label}.{key} must be a valid nonnegative integer')
        rating = row.get('review_rating_before_corrections')
        check(rating is None or (type(rating) is str and rating in RATINGS),
              'schema', f'{label}: unknown review rating')
    if errors:
        return errors, {}

    seen = set()
    previous_line = 0
    for row in data:
        label = row['id']
        expected = hashlib.sha256('\t'.join(row[k] for k in
                                 ('traditional', 'simplified', 'pinyin')).encode('utf-8')).hexdigest()[:16]
        check(label == expected, 'id', f'{label}: expected {expected}')
        check(label not in seen, 'id', f'{label}: duplicate ID')
        seen.add(label)
        check(row['source_line'] > previous_line, 'source_order', f'{label}: source lines must strictly increase')
        previous_line = row['source_line']
        en, uk = row['english_segments'], row['ukrainian_segments']
        check(bool(en) and len(en) == len(uk), 'alignment', f'{label}: segment counts differ or are empty')
        raw = f"{row['traditional']} {row['simplified']} [{row['pinyin']}] /{'/'.join(en)}/"
        check(row['raw_source'] == raw, 'source_fields', f'{label}: raw_source differs from source fields')
        for index, (english, ukrainian) in enumerate(zip(en, uk)):
            old, new = collections.Counter(REFERENCES.findall(english)), collections.Counter(REFERENCES.findall(ukrainian))
            check(old == new, 'references', f'{label}[{index}]: missing={dict(old-new)}, added={dict(new-old)}')
        check(row['translation_status'] == 'model_generated', 'status', f'{label}: unknown translation status')
        reviewed = row['model_reviewed']
        check(row['review_status'] == ('model_reviewed' if reviewed else 'not_model_reviewed'),
              'status', f'{label}: inconsistent model review status')
        check((row['review_rating_before_corrections'] in RATINGS) if reviewed
              else (row['review_rating_before_corrections'] is None),
              'status', f'{label}: inconsistent review rating')
        check(row['human_validation'] is False, 'status', f'{label}: human-validation evidence is not supported by this snapshot schema')
        check(row['has_known_uncertainty'] == bool(row['uncertainty_flags'] or row['uncertainty_notes']),
              'status', f'{label}: inconsistent uncertainty status')
        check(set(row['uncertainty_flags']) <= FLAGS, 'status', f'{label}: unknown uncertainty flag')
        check(len(row['uncertainty_flags']) == len(set(row['uncertainty_flags'])),
              'status', f'{label}: duplicate uncertainty flag')

    with (root / 'dictionary.csv').open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        check(reader.fieldnames is not None and len(reader.fieldnames) == len(FIELDS)
              and set(reader.fieldnames) == FIELDS, 'csv', 'header fields differ from schema')
        csv_rows = list(reader)
    check(len(csv_rows) == len(data), 'csv', 'record count differs from JSON')
    for index, (row, csv_row) in enumerate(zip(data, csv_rows)):
        for key, value in row.items():
            raw = csv_row.get(key)
            if key in ARRAYS:
                try:
                    equal = json.loads(raw) == value
                except (TypeError, ValueError):
                    equal = False
            else:
                expected = '' if value is None else str(value).lower() if type(value) is bool else str(value)
                equal = raw == expected
            check(equal, 'csv', f'row {index}.{key} differs from JSON')
        check(None not in csv_row, 'csv', f'row {index}: surplus columns')

    counts = {
        'records': len(data),
        'aligned_segments': sum(len(row['english_segments']) for row in data),
        'model_reviewed_records': sum(row['model_reviewed'] for row in data),
        'corrected_segments': sum(row['correction_count'] for row in data),
        'records_with_corrections': sum(row['correction_count'] > 0 for row in data),
        'known_flagged_records': sum(row['has_known_uncertainty'] for row in data),
        'human_validated_records': sum(row['human_validation'] for row in data),
    }
    saved = progress.get('counts')
    check(type(saved) is dict and set(saved) == set(counts), 'progress', 'count fields differ from schema')
    for key, value in counts.items():
        check(type(saved) is dict and type(saved.get(key)) is int and saved[key] == value,
              'progress', f'{key}: expected {value}')
    ratings = dict(collections.Counter(row['review_rating_before_corrections'] for row in data if row['model_reviewed']))
    check(progress.get('pre_correction_model_review_ratings') == ratings, 'progress', 'review rating counts differ')
    total = source.get('source_entries')
    check(type(total) is int and total >= len(data), 'source', 'invalid source entry count')
    check(progress.get('full_pinned_source_records') == total, 'progress', 'full source count differs')
    if type(total) is int and total > 0:
        check(progress.get('full_source_translation_coverage_percent') == round(100 * len(data) / total, 4),
              'progress', 'coverage percentage differs')
    check(progress.get('human_validation') is False and progress.get('complete_for_published_subset') is True
          and progress.get('complete_for_full_source') is False, 'progress', 'unexpected draft/completeness status')
    check(source.get('license') == 'CC BY-SA 4.0' and bool(source.get('attribution')),
          'source', 'missing source attribution or unexpected license')
    hashes = progress.get('data_sha256')
    check(type(hashes) is dict and set(hashes) == HASH_FILES, 'hash', 'unexpected hash manifest fields')
    if type(hashes) is dict:
        for name in sorted(HASH_FILES):
            check(hashes.get(name) == sha256(root / name), 'hash', f'{name}: SHA-256 mismatch')

    return errors, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1],
                        help='dataset directory (default: parent of scripts/)')
    args = parser.parse_args()
    try:
        errors, counts = validate(args.root)
    except (OSError, UnicodeError, ValueError, csv.Error) as exc:
        print(f'INPUT ERROR: {exc}', file=sys.stderr)
        return 2
    for error in errors:
        print(f'ERROR {error}', file=sys.stderr)
    if counts:
        print(json.dumps(counts, ensure_ascii=False, sort_keys=True))
    if errors:
        print(f'FAIL: {len(errors)} error(s).', file=sys.stderr)
        return 1
    print('PASS: offline structural checks only; translation quality is not certified.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
