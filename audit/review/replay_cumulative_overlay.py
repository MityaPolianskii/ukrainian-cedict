#!/usr/bin/env python3
"""Replay the cumulative overlay without intermediate dictionaries.
Read-only by default. --output-json writes a new file exclusively after checks.
This verifies reconstruction/provenance, not linguistic truth or human review.
"""
import argparse, hashlib, json, pathlib
from note_gate import apply_gate, GateValidationError, SOURCE_FIELDS

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text())

def require(test, message):
    if not test:
        raise GateValidationError(message)

def replay(baseline, candidate, output=None):
    summary = read(candidate / 'REPAIR_SUMMARY.json')
    overlay = read(candidate / 'REPAIR_OVERLAY.json')
    require(sha(baseline) == summary['baseline_dictionary_sha256'] == overlay['baseline_dictionary_sha256'], 'Baseline hash mismatch')
    required_artifacts = {'dictionary.json', 'NOTE_QUARANTINE.json', 'NOTE_REVIEW_LEDGER.json', 'REPAIR_OVERLAY.json', 'ALL_CORRECTION_PROPOSALS.json'}
    require(type(summary.get('artifacts')) is dict and set(summary['artifacts']) == required_artifacts, 'Artifact inventory must contain exactly the five expected artifacts')
    require(summary.get('schema_version') == 1 and overlay.get('schema_version') == 1, 'Unsupported schema version')
    for key in ('human_validation', 'public_writes', 'runtime_approved'):
        require(summary.get(key) is False, 'Invalid private/model-only metadata: ' + key)
    require(overlay.get('source_hash_fields') == list(SOURCE_FIELDS), 'Invalid source hash fields')
    for key in ('note_review_events', 'model_review_records'):
        require(type(overlay.get(key)) is list and all(item.get('human_validation') is False for item in overlay[key]), 'Invalid human validation assertion in ' + key)
    require(all(item.get('review_type') == 'model' for item in overlay['note_review_events']), 'Unexpected note review type')
    for name in ('NOTE_QUARANTINE.json', 'NOTE_REVIEW_LEDGER.json'):
        wrapper = read(candidate / name)
        require(wrapper.get('schema_version') == 1 and wrapper.get('baseline_dictionary_sha256') == summary['baseline_dictionary_sha256'], 'Invalid note provenance wrapper: ' + name)
    for name, expected in summary['artifacts'].items():
        require(pathlib.Path(name).name == name, 'Artifact name must be a basename')
        require(sha(candidate / name) == expected, 'Candidate artifact hash mismatch: ' + name)
    require(sha(candidate / 'dictionary.json') == summary['corrected_dictionary_sha256'], 'Candidate dictionary hash mismatch')
    rebuilt, quarantine, ledger, stats = apply_gate(read(baseline), overlay['note_review_events'], overlay['applied_translation_patches'], overlay['model_review_records'])
    require(rebuilt == read(candidate / 'dictionary.json'), 'Dictionary does not reconstruct exactly')
    require(quarantine == read(candidate / 'NOTE_QUARANTINE.json')['notes'], 'Quarantine does not reconstruct exactly')
    require(ledger == read(candidate / 'NOTE_REVIEW_LEDGER.json')['notes'], 'Ledger does not reconstruct exactly')
    require(stats == summary['stats'], 'Summary statistics do not reconstruct exactly')
    require(stats['human_validated_records'] == 0, 'Human validation count is not zero')
    require(summary.get('cumulative_reviewed_records', stats['checkpoint_reviewed_records']) == stats['checkpoint_reviewed_records'], 'Cumulative review count mismatch')
    counts = {'records': len(rebuilt), 'aligned_segments': sum(len(row['english_segments']) for row in rebuilt), 'model_reviewed_records': sum(row['model_reviewed'] for row in rebuilt), 'corrected_segments': sum(row['correction_count'] for row in rebuilt), 'records_with_corrections': sum(row['correction_count'] > 0 for row in rebuilt), 'known_flagged_records': sum(row['has_known_uncertainty'] for row in rebuilt), 'human_validated_records': 0}
    require(summary.get('counts') == counts, 'Dictionary summary counts do not reconstruct exactly')
    serialized = (json.dumps(rebuilt, ensure_ascii=False, indent=2) + '\n').encode()
    rebuilt_sha = hashlib.sha256(serialized).hexdigest()
    require(rebuilt_sha == summary['corrected_dictionary_sha256'], 'Serialized dictionary hash mismatch')
    if output is not None:
        with output.open('xb') as stream:
            stream.write(serialized)
    return {'status': 'pass', 'checkpoint': summary.get('checkpoint', 1), 'baseline_sha256': sha(baseline), 'reconstructed_dictionary_sha256': rebuilt_sha, 'exact_dictionary_quarantine_ledger_stats_reconstruction': True, 'model_reviewed_in_this_pass': len(overlay['model_review_records']), 'applied_segment_corrections': len(overlay['applied_translation_patches']), 'human_validation': False, 'linguistic_accuracy_certified': False, 'output_file_created': str(output) if output is not None else None}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=pathlib.Path, required=True)
    parser.add_argument('--candidate-dir', type=pathlib.Path, required=True)
    parser.add_argument('--output-json', type=pathlib.Path)
    args = parser.parse_args()
    print(json.dumps(replay(args.baseline, args.candidate_dir, args.output_json), ensure_ascii=False, indent=2))
