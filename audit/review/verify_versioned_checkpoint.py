#!/usr/bin/env python3
"""Read-only, independent reconstruction of versioned review checkpoints 002–009.

Does not import or execute either compiler or note_gate. Outputs JSON to stdout.
--record updates only versioned_compiler_review.json beside this script. Never
writes a baseline, review input, compiler, candidate, or frozen 001 artifact.
"""
import argparse
import collections
import copy
import datetime
import gc
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
BASELINE = ROOT.parent / 'ukrainian-cedict-expansion12-9668/publish-public/dictionary.json'
BASE_SHA = 'cdf73918ba4417090f8cdcc8d284ff3d47d65416e58de0efe7dcb610675fb465'
SOURCE_FIELDS = ('id', 'traditional', 'simplified', 'pinyin', 'english_segments', 'raw_source', 'source_line')
HAN = r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323af]+'
REFERENCES = re.compile(HAN + r'(?:\|' + HAN + r')?(?:\[[^\]\n]+\])?|\[[^\]\n]+\]')
ARTIFACTS = {'dictionary.json', 'NOTE_QUARANTINE.json', 'NOTE_REVIEW_LEDGER.json', 'REPAIR_OVERLAY.json', 'ALL_CORRECTION_PROPOSALS.json'}
MAJOR_TYPES = {'mistranslation', 'wrong_sense', 'unsupported_intensification', 'argument_structure', 'missing_semantic_restriction'}


def read(path):
    return json.loads(pathlib.Path(path).read_text())


def file_sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def nonblank(value):
    return type(value) is str and bool(value.strip())


class VerificationFailure(ValueError):
    pass


class Audit:
    def __init__(self):
        self.checks = []

    def check(self, name, condition, detail=None):
        item = {'check': name, 'passed': bool(condition)}
        if detail is not None:
            item['detail'] = detail
        self.checks.append(item)
        if not condition:
            raise VerificationFailure(name)


def candidate_dir(checkpoint):
    return ROOT / ('corrected-candidate' if checkpoint == 1 else f'candidate-checkpoint-{checkpoint:03}')


def check_files(directory, summary, audit, prefix):
    audit.check(prefix + '_required_artifact_hashes_present', ARTIFACTS <= set(summary['artifacts']))
    audit.check(prefix + '_no_self_referential_manifest', 'REPAIR_SUMMARY.json' not in summary['artifacts'])
    for name, sha in summary['artifacts'].items():
        audit.check(prefix + '_artifact_name_' + name, pathlib.Path(name).name == name)
        audit.check(prefix + '_artifact_hash_' + name, file_sha(directory / name) == sha)
    audit.check(prefix + '_dictionary_hash', file_sha(directory / 'dictionary.json') == summary['corrected_dictionary_sha256'])
    audit.check(prefix + '_baseline_identity', summary['baseline_dictionary_sha256'] == BASE_SHA)
    audit.check(prefix + '_private_model_only', summary['human_validation'] is False and summary['public_writes'] is False and summary['runtime_approved'] is False)


def bound_maps(overlay, by, audit, prefix):
    audit.check(prefix + '_overlay_baseline', overlay['baseline_dictionary_sha256'] == BASE_SHA and tuple(overlay['source_hash_fields']) == SOURCE_FIELDS)
    source_cache, record_cache = {}, {}

    def bound(value):
        identifier = value['id']
        if identifier not in by:
            return False
        if identifier not in source_cache:
            source_cache[identifier] = digest({k: by[identifier][k] for k in SOURCE_FIELDS})
            record_cache[identifier] = digest(by[identifier])
        return value['source_sha256'] == source_cache[identifier] and value['baseline_record_sha256'] == record_cache[identifier]

    emap, pmap, rmap = {}, {}, {}
    for e in overlay['note_review_events']:
        i = e['note_index']
        audit.check(prefix + '_note_binding_' + str(e['id']) + '_' + str(i), bound(e))
        notes = by[e['id']]['uncertainty_notes']
        valid = type(i) is int and 0 <= i < len(notes)
        audit.check(prefix + '_note_index_' + str(e['id']), valid)
        audit.check(prefix + '_note_exact_' + str(e['id']) + '_' + str(i), e['original_note'] == notes[i] and e['original_note_sha256'] == digest(notes[i]))
        audit.check(prefix + '_note_evidence_' + str(e['id']) + '_' + str(i), nonblank(e['reason']) and nonblank(e['review_source']))
        audit.check(prefix + '_note_disposition_' + str(e['id']) + '_' + str(i), e['disposition'] in {'retain_reviewed', 'replace_reviewed', 'quarantine_rejected'})
        audit.check(prefix + '_replacement_' + str(e['id']) + '_' + str(i), e['disposition'] != 'replace_reviewed' or nonblank(e['replacement']))
        key = (e['id'], i)
        audit.check(prefix + '_unique_note_' + str(key), key not in emap)
        emap[key] = e
    for p in overlay['applied_translation_patches']:
        j = p['segment_index']
        audit.check(prefix + '_patch_binding_' + str(p['id']) + '_' + str(j), bound(p))
        before = by[p['id']]
        audit.check(prefix + '_patch_index_' + str(p['id']), type(j) is int and 0 <= j < len(before['ukrainian_segments']))
        valid = p['before'] == before['ukrainian_segments'][j] and nonblank(p['after']) and p['after'] != p['before'] and p['confidence'] == 'high'
        audit.check(prefix + '_patch_exact_high_' + str(p['id']) + '_' + str(j), valid)
        audit.check(prefix + '_patch_references_' + str(p['id']) + '_' + str(j), collections.Counter(REFERENCES.findall(before['english_segments'][j])) == collections.Counter(REFERENCES.findall(p['after'])))
        key = (p['id'], j)
        audit.check(prefix + '_unique_patch_' + str(key), key not in pmap)
        pmap[key] = p
    for r in overlay['model_review_records']:
        audit.check(prefix + '_review_binding_' + str(r['id']), bound(r))
        audit.check(prefix + '_review_rating_' + str(r['id']), r['rating'] in {'pass', 'minor', 'major', 'unresolved'} and r.get('human_validation') is False)
        audit.check(prefix + '_unique_review_' + str(r['id']), r['id'] not in rmap)
        rmap[r['id']] = r
    audit.check(prefix + '_note_and_patch_ids_are_reviewed', {i for i, _ in emap} <= set(rmap) and {i for i, _ in pmap} <= set(rmap))
    return emap, pmap, rmap


def expected_record(before, maps):
    emap, pmap, rmap = maps
    identifier = before['id']
    out = copy.deepcopy(before)
    out['uncertainty_notes'] = []
    for i, original in enumerate(before['uncertainty_notes']):
        event = emap.get((identifier, i))
        if event and event['disposition'] == 'retain_reviewed':
            out['uncertainty_notes'].append(original)
        elif event and event['disposition'] == 'replace_reviewed':
            out['uncertainty_notes'].append(event['replacement'])
    for j in range(len(before['ukrainian_segments'])):
        patch = pmap.get((identifier, j))
        if patch:
            out['ukrainian_segments'][j] = patch['after']
            out['correction_count'] += 1
    if identifier in rmap:
        out.update(model_reviewed=True, review_status='model_reviewed', review_rating_before_corrections=rmap[identifier]['rating'])
    return out


def verify(checkpoint):
    audit = Audit()
    result = {'checkpoint': checkpoint, 'verified_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'running', 'scope': 'Structural provenance and exact reconstruction; no corpus-wide linguistic accuracy or human-validation claim.', 'writes': 'No baseline, review, compiler, or candidate writes. --record may update only versioned_compiler_review.json.'}
    try:
        audit.check('checkpoint_range', type(checkpoint) is int and 2 <= checkpoint <= 9)
        cp, prev, dest = ROOT / f'checkpoint-{checkpoint:03}', candidate_dir(checkpoint - 1), candidate_dir(checkpoint)
        if not (dest / 'REPAIR_SUMMARY.json').exists():
            result.update(status='pending', reason='Candidate completion summary is not present.')
            return result
        baseline_hash = file_sha(BASELINE)
        audit.check('frozen_baseline_hash', baseline_hash == BASE_SHA)
        base = read(BASELINE)
        by = {r['id']: r for r in base}
        audit.check('baseline_count_and_unique_ids', len(base) == len(by) == 125264)
        audit.check('baseline_alignment_and_human_flags', all(len(r['english_segments']) == len(r['ukrainian_segments']) and r['human_validation'] is False for r in base))
        ps, summary = read(prev / 'REPAIR_SUMMARY.json'), read(dest / 'REPAIR_SUMMARY.json')
        check_files(prev, ps, audit, 'previous')
        check_files(dest, summary, audit, 'current')
        audit.check('predecessor_checkpoint', ps.get('checkpoint', 1) == checkpoint - 1 and summary['checkpoint'] == checkpoint)
        audit.check('predecessor_summary_binding', summary['previous_dictionary_sha256'] == ps['corrected_dictionary_sha256'] and pathlib.Path(summary['previous_candidate_directory']).resolve() == prev.resolve())
        prev_overlay, overlay = read(prev / 'REPAIR_OVERLAY.json'), read(dest / 'REPAIR_OVERLAY.json')
        prev_maps, maps = bound_maps(prev_overlay, by, audit, 'previous'), bound_maps(overlay, by, audit, 'current')
        for field in ('note_review_events', 'applied_translation_patches', 'model_review_records', 'deferred_decisions'):
            audit.check('inherited_overlay_prefix_' + field, overlay[field][:len(prev_overlay[field])] == prev_overlay[field])
        queue = read(ROOT / 'remaining_flagged_review_queue.json')
        first_manifest = read(ROOT / 'checkpoint-001/manifest.json')
        manifest = read(cp / 'manifest.json')
        planned = queue['entries'][(checkpoint - 2) * 300:(checkpoint - 1) * 300]
        new_ids = [r['id'] for r in planned]
        prior_ids = first_manifest['selected_ids'] + [r['id'] for r in queue['entries'][:(checkpoint - 2) * 300]]
        cumulative_ids = prior_ids + new_ids
        audit.check('remaining_queue_baseline_and_size', queue['baseline_dictionary_sha256'] == BASE_SHA and len(queue['entries']) == 2234)
        audit.check('checkpoint_planned_exact_inputs', all(r == by[r['id']] for r in planned))
        audit.check('checkpoint_manifest_identity', manifest['checkpoint'] == f'{checkpoint:03}' and manifest['baseline_dictionary_sha256'] == BASE_SHA)
        audit.check('checkpoint_exact_selection_and_size', manifest['selected_ids'] == new_ids and manifest['selected_count'] == len(new_ids) == (134 if checkpoint == 9 else 300))
        audit.check('prior_review_ids_exact', [r['id'] for r in prev_overlay['model_review_records']] == prior_ids)
        audit.check('current_review_ids_exact', [r['id'] for r in overlay['model_review_records']] == cumulative_ids and len(cumulative_ids) == len(set(cumulative_ids)))
        audit.check('only_flagged_records_reviewed', all(by[i]['has_known_uncertainty'] for i in cumulative_ids))
        audit.check('new_event_and_patch_scope', all(e['id'] in set(new_ids) for e in overlay['note_review_events'][len(prev_overlay['note_review_events']):]) and all(p['id'] in set(new_ids) for p in overlay['applied_translation_patches'][len(prev_overlay['applied_translation_patches']):]))
        audit.check('inherited_review_audits', summary['review_audits'][:-3] == ps['review_audits'] and len(summary['review_audits']) == checkpoint * 3)
        entries, source_for, inputs_by = {}, {}, {}
        current_read_ids = []
        for item in summary['review_audits']:
            ip, rp = ROOT / item['input'], ROOT / item['review']
            audit.check('audit_hash_' + item['input'], file_sha(ip) == item['input_sha256'])
            audit.check('audit_hash_' + item['review'], file_sha(rp) == item['review_sha256'])
            inputs, review = read(ip), read(rp)
            ids = [r['id'] for r in inputs]
            audit.check('audit_exact_review_list_' + item['review'], review['human_validation'] is False and review['reviewed_ids'] == ids == [e['id'] for e in review['entries']])
            audit.check('audit_frozen_input_' + item['input'], all(r == by[r['id']] for r in inputs))
            for original, e in zip(inputs, review['entries']):
                identifier = e['id']
                audit.check('review_identity_' + identifier, identifier not in entries and all(e[k] == original[k] for k in ('id', 'source_line', 'traditional', 'simplified', 'pinyin')))
                audit.check('review_outcome_' + identifier, e['outcome'] in {'acceptable', 'correction_proposed', 'deferred'})
                entries[identifier], source_for[identifier], inputs_by[identifier] = e, item['review'], original
                if rp.parent == cp:
                    current_read_ids.append(identifier)
        audit.check('review_audit_ids_exact', list(entries) == cumulative_ids and current_read_ids == new_ids)
        audit.check('event_sources_are_actual_exact_reviews', all(e['review_source'] == source_for[e['id']] for e in overlay['note_review_events']) and all(p['review_source'] == source_for[p['id']] for p in overlay['applied_translation_patches']))
        decisions_path = cp / 'application_decisions.json'
        decisions = read(decisions_path)
        audit.check('application_decisions_digest', summary['application_decisions'] == str(decisions_path.relative_to(ROOT)) and summary['application_decisions_sha256'] == file_sha(decisions_path))
        audit.check('explicit_application_review', decisions.get('application_review_completed') is True)
        for shard in range(1, 4):
            name = f'review_{shard:03}.json'
            audit.check('application_review_file_binding_' + name, decisions['review_file_sha256'].get(name) == file_sha(cp / name))
        dm = {}
        for d in decisions['decisions']:
            valid = d.get('kind') in {'segment', 'note'} and d.get('decision') in {'apply', 'hold'} and nonblank(d.get('id')) and type(d.get('index')) is int and d['index'] >= 0 and nonblank(d.get('reason'))
            audit.check('decision_schema_' + str(len(dm)), valid)
            key = (d['kind'], d['id'], d['index'])
            audit.check('decision_unique_' + str(key), key not in dm)
            dm[key] = d
        old_proposals, proposals = read(prev / 'ALL_CORRECTION_PROPOSALS.json'), read(dest / 'ALL_CORRECTION_PROPOSALS.json')
        audit.check('inherited_proposals_unchanged', proposals[:len(old_proposals)] == old_proposals)
        new_proposals = proposals[len(old_proposals):]
        proposal_map = {(p['id'], p['segment_index']): p for p in new_proposals}
        audit.check('new_proposals_unique', len(proposal_map) == len(new_proposals))
        used, expected_proposal_order = set(), []
        new_patch_count = 0
        for identifier in new_ids:
            e, row = entries[identifier], by[identifier]
            note_changes, held, accepted = {}, False, []
            for n in e['note_corrections']:
                audit.check('note_proposal_original_' + identifier, n['before'] in row['uncertainty_notes'])
                index = row['uncertainty_notes'].index(n['before'])
                key = ('note', identifier, index)
                audit.check('note_proposal_decision_' + str(key), key in dm and key not in used)
                used.add(key)
                note_changes[index] = (n, dm[key])
            for index, original in enumerate(row['uncertainty_notes']):
                event = maps[0].get((identifier, index))
                if index not in note_changes:
                    audit.check('reviewed_unchanged_note_' + identifier, event is not None and event['disposition'] == 'retain_reviewed')
                    continue
                n, d = note_changes[index]
                if d['decision'] == 'apply':
                    expected = 'quarantine_rejected' if n['after'] is None else 'replace_reviewed'
                    audit.check('applied_note_decision_' + identifier, n['confidence'] == 'high' and event is not None and event['disposition'] == expected and event.get('replacement') == n['after'])
                else:
                    held = True
                    if d.get('original_attachment_approved') is True:
                        audit.check('held_note_explicit_original_approval_' + identifier, event is not None and event['disposition'] == 'retain_reviewed')
                    else:
                        audit.check('held_note_default_quarantine_' + identifier, event is None)
            for c in e['segment_corrections']:
                index = c['segment_index']
                audit.check('segment_proposal_schema_' + identifier, type(index) is int and 0 <= index < len(row['ukrainian_segments']) and not ({'id', 'source_sha256', 'baseline_record_sha256', 'review_source'} & set(c)))
                key = ('segment', identifier, index)
                audit.check('segment_proposal_decision_' + str(key), key in dm and key not in used and c['before'] == row['ukrainian_segments'][index])
                used.add(key)
                d = dm[key]
                p = proposal_map.get((identifier, index))
                expected_proposal_order.append((identifier, index))
                audit.check('segment_proposal_exact_payload_' + str(key), p is not None and all(p[k] == v for k, v in c.items()) and p['id'] == identifier and p['checkpoint'] == checkpoint and p['review_source'] == source_for[identifier])
                patch = maps[1].get((identifier, index))
                if d['decision'] == 'apply':
                    audit.check('applied_segment_exact_decision_' + str(key), c['confidence'] == 'high' and patch == p and p['application_status'] == 'applied_high_confidence' and p['application_review_reason'] == d['reason'])
                    accepted.append(c)
                    new_patch_count += 1
                else:
                    audit.check('held_segment_not_applied_' + str(key), patch is None and p['application_status'] == 'proposed_only' and p['application_hold_reason'] == d['reason'])
                    held = True
            rating = 'unresolved' if e['outcome'] == 'deferred' or held else ('minor' if e['outcome'] == 'correction_proposed' else 'pass')
            if rating == 'minor' and any(c.get('issue_type') in MAJOR_TYPES for c in accepted):
                rating = 'major'
            r = maps[2][identifier]
            audit.check('new_review_metadata_' + identifier, r['rating'] == rating and r['outcome'] == e['outcome'] and r['review_source'] == source_for[identifier] and r['checkpoint'] == checkpoint)
        audit.check('every_decision_used_exactly_once', used == set(dm))
        audit.check('new_proposal_order_and_coverage', [(p['id'], p['segment_index']) for p in new_proposals] == expected_proposal_order)
        old = read(prev / 'dictionary.json')
        audit.check('previous_dictionary_record_order', [r['id'] for r in old] == [r['id'] for r in base])
        old_digests = {}
        previous_errors = []
        for before, actual in zip(base, old):
            if expected_record(before, prev_maps) != actual:
                previous_errors.append(before['id'])
            old_digests[actual['id']] = digest(actual)
        audit.check('previous_dictionary_independent_reconstruction', not previous_errors, previous_errors[:10])
        del old
        gc.collect()
        current = read(dest / 'dictionary.json')
        audit.check('current_dictionary_record_order', [r['id'] for r in current] == [r['id'] for r in base])
        mismatches, outside_changes, newset = [], [], set(new_ids)
        for before, actual in zip(base, current):
            if expected_record(before, maps) != actual:
                mismatches.append(before['id'])
            if before['id'] not in newset and digest(actual) != old_digests[before['id']]:
                outside_changes.append(before['id'])
        audit.check('current_dictionary_independent_reconstruction', not mismatches, mismatches[:10])
        audit.check('previous_candidate_unchanged_outside_checkpoint', not outside_changes, outside_changes[:10])
        ledger = read(dest / 'NOTE_REVIEW_LEDGER.json')
        quarantine = read(dest / 'NOTE_QUARANTINE.json')
        audit.check('note_evidence_baseline_hashes', ledger['baseline_dictionary_sha256'] == BASE_SHA and quarantine['baseline_dictionary_sha256'] == BASE_SHA)
        lmap = {(x['id'], x['note_index']): x for x in ledger['notes']}
        qmap = {(x['id'], x['note_index']): x for x in quarantine['notes']}
        audit.check('ledger_unique_and_complete', len(lmap) == len(ledger['notes']) == sum(len(r['uncertainty_notes']) for r in base))
        audit.check('quarantine_unique', len(qmap) == len(quarantine['notes']))
        note_errors, expected_quarantine, dispositions = [], set(), collections.Counter()
        for before in base:
            for i, original in enumerate(before['uncertainty_notes']):
                key = (before['id'], i)
                event = maps[0].get(key)
                disposition = event['disposition'] if event else 'quarantine_unreviewed'
                dispositions[disposition] += 1
                item = lmap.get(key)
                if item is None or item['original_note'] != original or item['original_note_sha256'] != digest(original) or item['source_sha256'] != digest({k: before[k] for k in SOURCE_FIELDS}) or item['baseline_record_sha256'] != digest(before) or item['disposition'] != disposition or item['original_uncertainty_flags'] != before['uncertainty_flags'] or item['original_has_known_uncertainty'] != before['has_known_uncertainty']:
                    note_errors.append(key)
                if event and (item['review_source'] != event['review_source'] or item['reason'] != event['reason']):
                    note_errors.append(key)
                if event and disposition == 'replace_reviewed' and item.get('active_replacement') != event['replacement']:
                    note_errors.append(key)
                if disposition != 'retain_reviewed':
                    expected_quarantine.add(key)
        audit.check('every_original_note_exact_evidence', not note_errors, note_errors[:10])
        audit.check('quarantine_exact_dispositions_and_evidence', set(qmap) == expected_quarantine and all(x == lmap[k] for k, x in qmap.items()))
        actual_by = {r['id']: r for r in current}
        known = {f['id'] for f in read(ROOT / 'note-provenance-diagnosis.json')['confirmed_findings']}
        audit.check('known_15_contaminated_originals_inactive', len(known) == 15 and all(n not in actual_by[i]['uncertainty_notes'] for i in known for n in by[i]['uncertainty_notes']))
        audit.check('known_contaminated_summary_ids', summary['known_contaminated_note_ids_inactive'] == sorted(known))
        counts = {'records': len(current), 'aligned_segments': sum(len(r['english_segments']) for r in current), 'model_reviewed_records': sum(r['model_reviewed'] for r in current), 'corrected_segments': sum(r['correction_count'] for r in current), 'records_with_corrections': sum(r['correction_count'] > 0 for r in current), 'known_flagged_records': sum(r['has_known_uncertainty'] for r in current), 'human_validated_records': sum(r['human_validation'] for r in current)}
        stats = {'baseline_records': len(base), 'source_segments': counts['aligned_segments'], 'notes_total': len(lmap), 'notes_by_disposition': dict(sorted(dispositions.items())), 'active_notes': sum(len(r['uncertainty_notes']) for r in current), 'quarantined_original_notes': len(qmap), 'preserved_flagged_records': counts['known_flagged_records'], 'checkpoint_reviewed_records': len(maps[2]), 'applied_segment_corrections': len(maps[1]), 'human_validated_records': counts['human_validated_records']}
        audit.check('summary_counts_exact', counts == summary['counts'], counts)
        audit.check('summary_stats_exact', stats == summary['stats'], stats)
        expected_summary = {'current_checkpoint_reviewed_records': len(new_ids), 'current_checkpoint_reviewed_segments': sum(len(by[i]['english_segments']) for i in new_ids), 'current_checkpoint_applied_segment_corrections': new_patch_count, 'current_checkpoint_review_outcomes': dict(collections.Counter(entries[i]['outcome'] for i in new_ids)), 'cumulative_reviewed_records': len(cumulative_ids), 'cumulative_reviewed_segments': sum(len(by[i]['english_segments']) for i in cumulative_ids), 'remaining_flagged_entries_unreviewed': 2534 - len(cumulative_ids)}
        audit.check('summary_checkpoint_counters_exact', all(summary[k] == v for k, v in expected_summary.items()), expected_summary)
        audit.check('baseline_still_immutable', file_sha(BASELINE) == baseline_hash)
        check_files(prev, ps, audit, 'previous_after_verification')
        check_files(dest, summary, audit, 'current_after_verification')
        result.update(status='pass', candidate_dictionary_sha256=summary['corrected_dictionary_sha256'], counts=counts, stats=stats, checkpoint_counters=expected_summary, outside_checkpoint_changes=0)
    except FileNotFoundError as exc:
        result.update(status='blocked', error='Required file is missing: ' + str(exc.filename))
    except (VerificationFailure, KeyError, TypeError, ValueError, IndexError) as exc:
        result.update(status='fail', error=type(exc).__name__ + ': ' + str(exc))
    finally:
        result['checks_run'] = len(audit.checks)
        result['checks_passed'] = sum(item['passed'] for item in audit.checks)
        result['failed_checks'] = [item for item in audit.checks if not item['passed']]
        result['aggregate_checks'] = [item for item in audit.checks if item.get('detail') is not None]
        result['verifier_sha256'] = file_sha(__file__)
        result['compiler_sha256'] = file_sha(ROOT / 'compile_review_checkpoint.py')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=int, required=True)
    parser.add_argument('--record', action='store_true', help='Update only versioned_compiler_review.json; never candidate files.')
    args = parser.parse_args()
    result = verify(args.checkpoint)
    if args.record:
        path = ROOT / 'versioned_compiler_review.json'
        report = read(path) if path.exists() else {'scope': 'Versioned compiler architecture and independent artifact verification.'}
        report.setdefault('checkpoint_verifications', {})[f'{args.checkpoint:03}'] = result
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'pass' else (2 if result['status'] == 'pending' else 1)


if __name__ == '__main__':
    sys.exit(main())
