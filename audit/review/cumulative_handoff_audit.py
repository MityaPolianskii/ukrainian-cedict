#!/usr/bin/env python3
"""Independent replay-helper regression audit. Only writes new audit output/temporary fixtures.

Usage: python cumulative_handoff_audit.py --checkpoint 6 --report cumulative_handoff_audit.006.json
Frozen dictionaries, review files and implementation scripts are never changed.
"""
import argparse
import copy
import datetime
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent
BASELINE = ROOT.parent / 'ukrainian-cedict-expansion12-9668/publish-public/dictionary.json'
BASE_SHA = 'cdf73918ba4417090f8cdcc8d284ff3d47d65416e58de0efe7dcb610675fb465'
ARTIFACTS = ('dictionary.json', 'REPAIR_OVERLAY.json', 'NOTE_QUARANTINE.json', 'NOTE_REVIEW_LEDGER.json', 'ALL_CORRECTION_PROPOSALS.json')
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
import note_gate


def sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))


def write(path, value):
    pathlib.Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run(baseline, candidate, optimized=False, output=None, helper=None, restrict_json_to=None):
    command = [sys.executable]
    if optimized:
        command.append('-O')
    script = str(helper or ROOT / 'replay_cumulative_overlay.py')
    if restrict_json_to is not None:
        harness = "import sys,pathlib,runpy\nallowed=pathlib.Path(sys.argv.pop(1)).resolve()\nscript=sys.argv[1]\ndef audit(event,args):\n if event=='open' and isinstance(args[0],str) and args[0].endswith('.json') and not pathlib.Path(args[0]).resolve().is_relative_to(allowed):\n  raise PermissionError('JSON read outside portable tree: '+args[0])\nsys.addaudithook(audit)\nsys.argv=sys.argv[1:]\nrunpy.run_path(script,run_name='__main__')\n"
        command += ['-B', '-c', harness, str(restrict_json_to), script]
    else:
        command += ['-B', script]
    command += ['--baseline', str(baseline), '--candidate-dir', str(candidate)]
    if output is not None:
        command += ['--output-json', str(output)]
    start = time.monotonic()
    result = subprocess.run(command, cwd=candidate.parent, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, text=True, capture_output=True)
    return {'returncode': result.returncode, 'stdout': result.stdout, 'stderr_tail': result.stderr[-1800:], 'elapsed_seconds': round(time.monotonic() - start, 3)}


def make_fixture(path):
    path.mkdir()
    baseline = path / 'baseline.json'
    candidate = path / 'candidate'
    candidate.mkdir()
    row = {'id': 'audit-fixture', 'traditional': '門', 'simplified': '门', 'pinyin': 'men2', 'english_segments': ['door'], 'ukrainian_segments': ['брама'], 'raw_source': '門 门 [men2] /door/', 'source_line': 1, 'uncertainty_notes': ['Fixture note'], 'uncertainty_flags': ['fixture_uncertainty'], 'translation_status': 'translated', 'review_status': 'unreviewed', 'human_validation': False, 'model_reviewed': False, 'has_known_uncertainty': True, 'correction_count': 0}
    rows = [row]
    write(baseline, rows)
    event = note_gate.note_event(row, 0, 'replace_reviewed', replacement='Reviewed fixture note', reason='Fixture attachment review', review_source='checkpoint-001/review_001.json')
    patch = {'id': row['id'], 'source_sha256': note_gate.source_hash(row), 'baseline_record_sha256': note_gate.digest(row), 'segment_index': 0, 'before': 'брама', 'after': 'двері', 'confidence': 'high', 'review_source': 'checkpoint-001/review_001.json'}
    review = {'id': row['id'], 'source_sha256': note_gate.source_hash(row), 'baseline_record_sha256': note_gate.digest(row), 'rating': 'minor', 'review_source': 'checkpoint-001/review_001.json', 'human_validation': False}
    overlay = {'schema_version': 1, 'baseline_dictionary_sha256': sha(baseline), 'source_hash_fields': list(note_gate.SOURCE_FIELDS), 'note_review_events': [event], 'applied_translation_patches': [patch], 'model_review_records': [review], 'deferred_decisions': []}
    out, quarantine, ledger, stats = note_gate.apply_gate(rows, [event], [patch], [review])
    write(candidate / 'dictionary.json', out)
    write(candidate / 'REPAIR_OVERLAY.json', overlay)
    write(candidate / 'NOTE_QUARANTINE.json', {'schema_version': 1, 'baseline_dictionary_sha256': sha(baseline), 'notes': quarantine})
    write(candidate / 'NOTE_REVIEW_LEDGER.json', {'schema_version': 1, 'baseline_dictionary_sha256': sha(baseline), 'notes': ledger})
    write(candidate / 'ALL_CORRECTION_PROPOSALS.json', [patch])
    counts = {'records': len(out), 'aligned_segments': sum(len(r['english_segments']) for r in out), 'model_reviewed_records': sum(r['model_reviewed'] for r in out), 'corrected_segments': sum(r['correction_count'] for r in out), 'records_with_corrections': sum(r['correction_count'] > 0 for r in out), 'known_flagged_records': sum(r['has_known_uncertainty'] for r in out), 'human_validated_records': 0}
    summary = {'schema_version': 1, 'checkpoint': 1, 'baseline_dictionary_sha256': sha(baseline), 'corrected_dictionary_sha256': sha(candidate / 'dictionary.json'), 'human_validation': False, 'public_writes': False, 'runtime_approved': False, 'stats': stats, 'counts': counts, 'artifacts': {name: sha(candidate / name) for name in ARTIFACTS}}
    write(candidate / 'REPAIR_SUMMARY.json', summary)
    return baseline, candidate


def mutate_file(candidate, name, callback, refresh=True):
    value = read(candidate / name)
    callback(value)
    write(candidate / name, value)
    if refresh:
        summary = read(candidate / 'REPAIR_SUMMARY.json')
        summary['artifacts'][name] = sha(candidate / name)
        if name == 'dictionary.json':
            summary['corrected_dictionary_sha256'] = sha(candidate / name)
        write(candidate / 'REPAIR_SUMMARY.json', summary)


def audit(checkpoint):
    candidate = ROOT / f'candidate-checkpoint-{checkpoint:03}'
    protected = [BASELINE, ROOT / 'note_gate.py', ROOT / 'replay_cumulative_overlay.py', ROOT / 'verify_versioned_checkpoint.py', *candidate.iterdir()]
    protected = [p for p in protected if p.is_file()]
    before = {str(p): sha(p) for p in protected}
    results = {'audit_scope': 'Independent replay-helper mechanics, integrity rejection, optimization safety and isolated cumulative reconstruction. No linguistic certification or human validation.', 'audited_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'checkpoint': checkpoint, 'implementation_sha256': {p.name: sha(p) for p in protected if p.suffix == '.py'}, 'baseline_sha256': sha(BASELINE), 'baseline_known_identity_passed': sha(BASELINE) == BASE_SHA, 'tests': [], 'observed_gaps': []}

    def record(name, observed, expected_accept, optimized, category='tests', extra=None):
        accept = observed['returncode'] == 0
        item = {'name': name, 'python_optimized': optimized, 'accepted': accept, 'expectation_met': accept == expected_accept, 'expected_accept': expected_accept, **observed}
        if extra:
            item.update(extra)
        results[category].append(item)

    with tempfile.TemporaryDirectory(prefix='cumulative_handoff_audit.') as temporary:
        temp = pathlib.Path(temporary)
        for optimized in (False, True):
            counter = 0

            def fixture():
                nonlocal counter
                counter += 1
                return make_fixture(temp / f'{"optimized" if optimized else "normal"}-{counter}')

            baseline, c = fixture()
            record('valid_synthetic_replay', run(baseline, c, optimized), True, optimized)
            baseline, c = fixture()
            with baseline.open('a') as f:
                f.write(' ')
            output = c.parent / 'should-not-exist.json'
            r = run(baseline, c, optimized, output)
            record('baseline_hash_mismatch_rejected_before_write', r, False, optimized, extra={'output_absent': not output.exists()})
            baseline, c = fixture()
            mutate_file(c, 'REPAIR_OVERLAY.json', lambda x: x['note_review_events'][0].update(source_sha256='0' * 64), refresh=False)
            record('artifact_hash_mismatch_rejected', run(baseline, c, optimized), False, optimized)
            for name, filename, callback in [
                ('stale_note_binding', 'REPAIR_OVERLAY.json', lambda x: x['note_review_events'][0].update(source_sha256='0' * 64)),
                ('stale_patch_binding', 'REPAIR_OVERLAY.json', lambda x: x['applied_translation_patches'][0].update(baseline_record_sha256='0' * 64)),
                ('duplicate_note_event', 'REPAIR_OVERLAY.json', lambda x: x['note_review_events'].append(copy.deepcopy(x['note_review_events'][0]))),
                ('duplicate_review_record', 'REPAIR_OVERLAY.json', lambda x: x['model_review_records'].append(copy.deepcopy(x['model_review_records'][0]))),
                ('dictionary_content_mismatch', 'dictionary.json', lambda x: x[0]['ukrainian_segments'].__setitem__(0, 'змінено')),
                ('quarantine_content_mismatch', 'NOTE_QUARANTINE.json', lambda x: x['notes'][0].update(original_note='changed')),
                ('ledger_content_mismatch', 'NOTE_REVIEW_LEDGER.json', lambda x: x['notes'][0].update(original_note='changed')),
            ]:
                baseline, c = fixture()
                mutate_file(c, filename, callback)
                record(name + '_rejected_with_refreshed_artifact_hash', run(baseline, c, optimized), False, optimized)
            baseline, c = fixture()
            summary = read(c / 'REPAIR_SUMMARY.json')
            summary['stats']['active_notes'] += 1
            write(c / 'REPAIR_SUMMARY.json', summary)
            record('statistics_mismatch_rejected', run(baseline, c, optimized), False, optimized)
            baseline, c = fixture()
            output = c.parent / 'new-output.json'
            record('new_output_exact', run(baseline, c, optimized, output), True, optimized, extra=None)
            results['tests'][-1]['output_hash_matches'] = output.exists() and sha(output) == sha(c / 'dictionary.json')
            output.write_bytes(b'existing sentinel')
            record('existing_output_preserved', run(baseline, c, optimized, output), False, optimized, extra={'output_contents_preserved': output.read_bytes() == b'existing sentinel'})
            record('baseline_as_output_preserved', run(baseline, c, optimized, baseline), False, optimized, extra={'baseline_contents_preserved': sha(baseline) == read(c / 'REPAIR_SUMMARY.json')['baseline_dictionary_sha256']})
            link = c.parent / 'dangling-output-link.json'
            target = c.parent / 'must-not-be-created.json'
            link.symlink_to(target)
            record('dangling_symlink_output_rejected', run(baseline, c, optimized, link), False, optimized, extra={'symlink_target_absent': not target.exists()})
            baseline, c = fixture()
            summary = read(c / 'REPAIR_SUMMARY.json')
            summary['artifacts']['../baseline.json'] = sha(baseline)
            write(c / 'REPAIR_SUMMARY.json', summary)
            record('artifact_traversal_rejected', run(baseline, c, optimized), False, optimized)
            baseline, c = fixture()
            summary = read(c / 'REPAIR_SUMMARY.json')
            summary['artifacts'].pop('ALL_CORRECTION_PROPOSALS.json')
            write(c / 'REPAIR_SUMMARY.json', summary)
            (c / 'ALL_CORRECTION_PROPOSALS.json').unlink()
            record('missing_required_proposals_inventory', run(baseline, c, optimized), False, optimized, 'observed_gaps')
            baseline, c = fixture()
            summary = read(c / 'REPAIR_SUMMARY.json')
            summary.update(human_validation=True, public_writes=True, runtime_approved=True)
            write(c / 'REPAIR_SUMMARY.json', summary)
            record('unsafe_summary_private_status_metadata', run(baseline, c, optimized), False, optimized, 'observed_gaps')
            for name, filename, callback in [
                ('quarantine_wrapper_baseline_mismatch', 'NOTE_QUARANTINE.json', lambda x: x.update(baseline_dictionary_sha256='0' * 64)),
                ('ledger_wrapper_baseline_mismatch', 'NOTE_REVIEW_LEDGER.json', lambda x: x.update(baseline_dictionary_sha256='0' * 64)),
                ('overlay_source_field_metadata_mismatch', 'REPAIR_OVERLAY.json', lambda x: x.update(source_hash_fields=['id'])),
                ('review_record_false_human_validation_claim', 'REPAIR_OVERLAY.json', lambda x: x['model_review_records'][0].update(human_validation=True)),
            ]:
                baseline, c = fixture()
                mutate_file(c, filename, callback)
                record(name, run(baseline, c, optimized), False, optimized, 'observed_gaps')

        # A portable directory holds only the baseline, final candidate, and two replay scripts.
        # No checkpoint directories, review shards, or predecessor dictionaries are present.
        isolated = temp / 'portable'
        isolated.mkdir()
        portable_base = isolated / 'baseline.json'
        shutil.copyfile(BASELINE, portable_base)
        portable_candidate = isolated / 'candidate'
        shutil.copytree(candidate, portable_candidate)
        for name in ('replay_cumulative_overlay.py', 'note_gate.py'):
            shutil.copyfile(ROOT / name, isolated / name)
        for optimized in (False, True):
            output = isolated / ('rebuilt-optimized.json' if optimized else 'rebuilt-normal.json')
            r = run(portable_base, portable_candidate, optimized, output, isolated / 'replay_cumulative_overlay.py', restrict_json_to=isolated)
            record('real_checkpoint_isolated_exact_replay', r, True, optimized, extra={'no_intermediate_dictionaries_in_portable_tree': True, 'all_json_access_outside_portable_tree_denied_by_python_audit_hook': True, 'dictionary_sha256': sha(candidate / 'dictionary.json'), 'output_sha256': sha(output) if output.exists() else None})
            results['tests'][-1]['output_hash_matches'] = output.exists() and sha(output) == sha(candidate / 'dictionary.json')
    after = {str(p): sha(p) for p in protected}
    results['protected_files_before'] = before
    results['protected_files_unchanged'] = before == after
    results['passed_expected_mechanics_tests'] = all(t['expectation_met'] and all(t.get(k, True) for k in ('output_absent', 'output_hash_matches', 'output_contents_preserved', 'baseline_contents_preserved', 'symlink_target_absent')) for t in results['tests'])
    results['observed_gap_count'] = sum(not t['expectation_met'] for t in results['observed_gaps'])
    results['status'] = ('pass_with_hardening_gaps' if results['observed_gap_count'] else 'pass') if results['passed_expected_mechanics_tests'] and results['protected_files_unchanged'] and results['baseline_known_identity_passed'] else 'fail'
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=int, required=True)
    parser.add_argument('--report', type=pathlib.Path, required=True)
    args = parser.parse_args()
    result = audit(args.checkpoint)
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'mechanics_tests': len(result['tests']), 'observed_gaps': result['observed_gap_count'], 'protected_files_unchanged': result['protected_files_unchanged'], 'report': str(args.report)}, indent=2))
    sys.exit(0 if result['status'].startswith('pass') else 1)
