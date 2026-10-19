#!/usr/bin/env python3
"""Replay a public model-reviewed overlay against the unchanged frozen source."""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
SOURCE = '166a286a68f278b73c3307284dbee879451c262608b1cbe0f8e9d6eca2d4474b'
MODELS = {'gpt-6-astra', 'gpt-6.1-sol'}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())


def load(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def eligible(decision):
    return (decision['record_disposition'] in ['accept', 'correct']
            and not decision.get('unresolved_reasons') and not decision.get('unresolved_flags')
            and not decision.get('runtime_hold_reasons')
            and all(flag['status'] == 'resolved' for flag in decision['flag_resolutions'])
            and all(segment['decision'] in ['accept', 'correct'] for segment in decision['segments']))


def translation(raw, item):
    decision = item['decision']
    return {'id': raw['id'], 'traditional': raw['traditional'], 'simplified': raw['simplified'],
            'pinyin': raw['pinyin'], 'english_segments': raw['english_segments'],
            'ukrainian_segments': [segment['final_ukrainian'] for segment in decision['segments']],
            'source_record_sha256': decision['source_record_sha256'],
            'source_review_sha256': item['sourceReviewSHA256'], 'reviewer_model': item['model'],
            'source_flag_resolutions': decision['flag_resolutions']}


def validate(directory, source_path, allow_incomplete=False):
    source_bytes = source_path.read_bytes()
    need(digest(source_bytes) == SOURCE, 'Wrong frozen source bytes')
    source_rows = json.loads(source_bytes)
    source = {row['id']: row for row in source_rows}
    need(len(source) == len(source_rows) == 125264, 'Source IDs/count differ')
    need(sum(len(row['english_segments']) for row in source_rows) == 199737, 'Source segment count differs')
    manifest = load(directory / 'manifest.json')
    need(manifest['sourceDictionarySHA256'] == SOURCE and manifest['humanValidation'] is False
         and manifest['linguisticAccuracyCertified'] is False and manifest['runtimeApproval'] is False,
         'Source or approval claims differ')
    need(manifest['completeSourceReview'] or allow_incomplete, 'Incomplete overlay is not a complete public release')
    files = manifest['files']
    need(set(files) == {'review-evidence.json.gz', 'translations.json.gz', 'held-records.json.gz', 'validate.py'},
         'Unexpected public package inventory')
    for name, pin in files.items():
        data = (directory / name).read_bytes()
        need(digest(data) == pin['sha256'] and len(data) == pin['bytes'], 'Package bytes differ: ' + name)
    proof = load(directory / 'review-evidence.json.gz')
    overlay = load(directory / 'translations.json.gz')
    held = load(directory / 'held-records.json.gz')
    ids, expected_overlay, expected_held = set(), [], []
    record_counts, segment_counts, models = collections.Counter(), collections.Counter(), set()
    corrected = reviewed_segments = 0
    for item in proof:
        model, decision = item['model'], item['decision']
        rid = decision['entry_id']
        need(rid not in ids and rid in source and model in MODELS, 'Duplicate, foreign or unknown model record')
        need(len(item['sourceReviewSHA256']) == 64 and all(c in '0123456789abcdef' for c in item['sourceReviewSHA256']),
             'Malformed original review binding')
        ids.add(rid)
        models.add(model)
        raw = source[rid]
        need(canonical(raw) == decision['source_record_sha256'], 'Original source record differs')
        need(all(raw[key] == decision[key] for key in ['traditional', 'simplified', 'pinyin']), 'Headword differs')
        need(raw['uncertainty_flags'] == decision['original_uncertainty_flags']
             and raw['uncertainty_notes'] == decision['original_uncertainty_notes'], 'Original flags/notes differ')
        need(len(decision['segments']) == len(raw['english_segments']) == len(raw['ukrainian_segments']),
             'A source segment was omitted or invented')
        need(decision['record_disposition'] in ['accept', 'correct', 'quarantine'], 'Unknown record disposition')
        for index, segment in enumerate(decision['segments']):
            en, uk = raw['english_segments'][index], raw['ukrainian_segments'][index]
            expected_hash = canonical({'entry_id': rid, 'segment_index': index, 'english': en, 'ukrainian': uk})
            need(segment['segment_id'] == rid + ':' + str(index) and segment['segment_index'] == index
                 and segment['source_segment_sha256'] == expected_hash and segment['original_ukrainian'] == uk,
                 'Source segment binding differs')
            need(segment.get('english', en) == en and segment['decision'] in ['accept', 'correct', 'quarantine'],
                 'English source or segment decision differs')
            need(isinstance(segment['final_ukrainian'], str) and segment['final_ukrainian'].strip()
                 and segment['rationale'].strip(), 'Empty final text or rationale')
            need((segment['final_ukrainian'] != uk) == (segment['decision'] == 'correct'), 'Correction invariant differs')
            segment_counts[segment['decision']] += 1
            reviewed_segments += 1
        record_counts[decision['record_disposition']] += 1
        if eligible(decision):
            need({flag['flag'] for flag in decision['flag_resolutions']} == set(raw['uncertainty_flags']),
                 'Missing original flag resolution')
            expected_overlay.append(translation(raw, item))
            corrected += sum(segment['decision'] == 'correct' for segment in decision['segments'])
        else:
            expected_held.append({'id': rid, 'recordDisposition': decision['record_disposition'],
                                  'sourceReviewSHA256': item['sourceReviewSHA256']})
    need(overlay == sorted(expected_overlay, key=lambda row: row['id']), 'Overlay text differs from authored eligible decisions')
    need(held == sorted(expected_held, key=lambda row: row['id']), 'Held records were altered or included')
    need(len(ids) == len(overlay) + len(held) == manifest['reviewedRecords'], 'Reviewed/eligible/held accounting differs')
    if manifest['completeSourceReview']:
        need(ids == set(source) and reviewed_segments == 199737, 'Complete source coverage is missing')
    need(manifest['reviewedSegments'] == reviewed_segments and manifest['eligibleRecords'] == len(overlay)
         and manifest['eligibleSegments'] == sum(len(row['ukrainian_segments']) for row in overlay)
         and manifest['excludedWholeRecords'] == len(held) and manifest['appliedEligibleCorrections'] == corrected,
         'Manifest totals differ')
    need(manifest['recordDispositions'] == dict(record_counts) and manifest['segmentDecisions'] == dict(segment_counts)
         and set(manifest['reviewerModels']) == models, 'Review counts/model attribution differ')
    return {'status': 'PUBLIC_OVERLAY_REPLAY_PASS', 'completeSourceReview': manifest['completeSourceReview'],
            'reviewedRecords': len(ids), 'reviewedSegments': reviewed_segments, 'eligibleRecords': len(overlay),
            'excludedWholeRecords': len(held), 'appliedEligibleCorrections': corrected,
            'humanValidation': False, 'linguisticAccuracyCertified': False, 'runtimeApproval': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--allow-incomplete', action='store_true')
    args = parser.parse_args()
    print(json.dumps(validate(args.directory, args.source, args.allow_incomplete), indent=2))
