#!/usr/bin/env python3
"""Independent final cumulative audit, without compiler/gate imports or intermediate dictionaries.
Writes only a new explicitly named cumulative_handoff_audit.* JSON report.
"""
import argparse, collections, copy, datetime, hashlib, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
BASELINE = ROOT.parent / 'ukrainian-cedict-expansion12-9668/publish-public/dictionary.json'
BASE_SHA = 'cdf73918ba4417090f8cdcc8d284ff3d47d65416e58de0efe7dcb610675fb465'
HELPER_SHA = '28b324d03aa82b0a50a5a05a724df7532bf4a99c73072f3691d840d2563fc79a'
SOURCE_FIELDS = ('id', 'traditional', 'simplified', 'pinyin', 'english_segments', 'raw_source', 'source_line')
ARTIFACTS = {'dictionary.json', 'REPAIR_OVERLAY.json', 'NOTE_QUARANTINE.json', 'NOTE_REVIEW_LEDGER.json', 'ALL_CORRECTION_PROPOSALS.json'}
HAN = r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323af]+'
REFERENCES = re.compile(HAN + r'(?:\|' + HAN + r')?(?:\[[^\]\n]+\])?|\[[^\]\n]+\]')


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))


def sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def audit():
    checks, inventory = [], {}
    result = {'audited_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'scope': 'Independent exact cumulative reconstruction, all-flagged coverage and portable evidence inventory. No linguistic certification, human validation, public writes or runtime approval.', 'status': 'running'}

    def check(name, condition, detail=None):
        checks.append({'name': name, 'passed': bool(condition), **({'detail': detail} if detail is not None else {})})
        if not condition:
            raise ValueError(name)

    def file(path, role):
        path = pathlib.Path(path)
        key = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        inventory[key] = {'sha256': sha(path), 'bytes': path.stat().st_size, 'role': role}
        return inventory[key]['sha256']

    try:
        dest = ROOT / 'candidate-checkpoint-009'
        summary, overlay = read(dest / 'REPAIR_SUMMARY.json'), read(dest / 'REPAIR_OVERLAY.json')
        check('known_original_identity', file(BASELINE, 'immutable original; required for replay') == BASE_SHA)
        check('audited_frozen_replay_helper', sha(ROOT / 'replay_cumulative_overlay.py') == HELPER_SHA)
        base = read(BASELINE)
        by = {r['id']: r for r in base}
        flagged = {r['id'] for r in base if r['has_known_uncertainty']}
        check('baseline_counts', len(base) == len(by) == 125264 and len(flagged) == 2534 and sum(len(r['english_segments']) for r in base) == 199737)
        check('final_schema_scope', summary['checkpoint'] == 9 and summary['baseline_dictionary_sha256'] == BASE_SHA and overlay['baseline_dictionary_sha256'] == BASE_SHA and overlay['source_hash_fields'] == list(SOURCE_FIELDS))
        check('final_private_model_only', all(summary[k] is False for k in ('human_validation', 'public_writes', 'runtime_approved')))
        check('final_inventory_exact', set(summary['artifacts']) == ARTIFACTS)
        for name, expected in summary['artifacts'].items():
            check('final_artifact_' + name, file(dest / name, 'final cumulative candidate') == expected)
        summary_sha = file(dest / 'REPAIR_SUMMARY.json', 'final cumulative summary')
        check('final_dictionary_hash_binding', summary['corrected_dictionary_sha256'] == inventory['candidate-checkpoint-009/dictionary.json']['sha256'])
        selected, review_entries, sources, input_sources = [], {}, {}, {}
        review_audits = {}
        for number in range(1, 10):
            cp = ROOT / f'checkpoint-{number:03}'
            manifest = read(cp / 'manifest.json')
            file(cp / 'manifest.json', 'review cohort manifest')
            ids, entries_here = [], {}
            for shard in range(1, 4):
                ip, rp = cp / f'input_{shard:03}.json', cp / f'review_{shard:03}.json'
                inputs, review = read(ip), read(rp)
                expected_ids = [r['id'] for r in inputs]
                check(f'{number:03}_{shard:03}_exact_original_inputs', all(r == by[r['id']] for r in inputs))
                check(f'{number:03}_{shard:03}_exact_review_coverage', review['human_validation'] is False and review['reviewed_ids'] == expected_ids == [r['id'] for r in review['entries']])
                for original, entry in zip(inputs, review['entries']):
                    identifier = entry['id']
                    check('unique_review_' + identifier, identifier not in review_entries)
                    check('review_identity_' + identifier, all(entry[k] == original[k] for k in ('id', 'source_line', 'traditional', 'simplified', 'pinyin')))
                    review_entries[identifier] = entry
                    entries_here[identifier] = entry
                    sources[identifier], input_sources[identifier] = str(rp.relative_to(ROOT)), str(ip.relative_to(ROOT))
                ids += expected_ids
                ih = file(ip, 'exact original review input')
                rh = file(rp, 'individual model review')
                file(cp / f'input_{shard:03}.txt', 'readable review input companion')
                review_audits[str(rp.relative_to(ROOT))] = {'input': str(ip.relative_to(ROOT)), 'input_sha256': ih, 'review_sha256': rh}
            check(f'{number:03}_manifest_exact_cohort', manifest['selected_ids'] == ids and len(ids) == (134 if number == 9 else 300))
            selected += ids
            if number == 1:
                initial_handoff = read(ROOT / 'VERIFIED_HANDOFF.json')
                initial_summary = ROOT / 'corrected-candidate/REPAIR_SUMMARY.json'
                check('001_verified_summary_bound', file(initial_summary, 'frozen initial checkpoint summary; no intermediate dictionary needed') == initial_handoff['artifacts']['REPAIR_SUMMARY.json']['sha256'])
            if number > 1:
                decision_path = cp / 'application_decisions.json'
                decisions = read(decision_path)
                check(f'{number:03}_application_review_complete', decisions['application_review_completed'] is True)
                for shard in range(1, 4):
                    name = f'review_{shard:03}.json'
                    check(f'{number:03}_decision_review_hash_{shard}', decisions['review_file_sha256'][name] == sha(cp / name))
                actual_decisions = [(d['kind'], d['id'], d['index']) for d in decisions['decisions']]
                expected_decisions = []
                for identifier, entry in entries_here.items():
                    expected_decisions += [('segment', identifier, correction['segment_index']) for correction in entry['segment_corrections']]
                    expected_decisions += [('note', identifier, by[identifier]['uncertainty_notes'].index(correction['before'])) for correction in entry['note_corrections']]
                check(f'{number:03}_every_proposal_has_one_decision', len(actual_decisions) == len(set(actual_decisions)) and set(actual_decisions) == set(expected_decisions))
                file(decision_path, 'explicit per-proposal application decision')
                verified = read(cp / 'VERIFIED_CHECKPOINT.json')
                check(f'{number:03}_independent_verification_present', verified['checkpoint'] == number and verified['status'] == 'independently_verified_private' and verified['baseline_dictionary_sha256'] == BASE_SHA and all(verified[k] is False for k in ('human_validation', 'public_writes', 'runtime_approved')))
                file(cp / 'VERIFIED_CHECKPOINT.json', 'independent checkpoint attestation')
                checkpoint_summary = ROOT / f'candidate-checkpoint-{number:03}/REPAIR_SUMMARY.json'
                check(f'{number:03}_verified_summary_bound', file(checkpoint_summary, 'checkpoint evidence summary; no intermediate dictionary needed') == verified['candidate_summary_sha256'])
                check(f'{number:03}_verified_dictionary_digest_consistent', read(checkpoint_summary)['corrected_dictionary_sha256'] == verified['dictionary_sha256'])
                if number == 9:
                    check('final_verified_summary_and_dictionary', verified['candidate_summary_sha256'] == summary_sha and verified['dictionary_sha256'] == summary['corrected_dictionary_sha256'])
        check('all_2534_original_flagged_records_exactly_once', len(selected) == len(set(selected)) == 2534 and set(selected) == flagged)
        check('all_3677_flagged_source_segments_reviewed', sum(len(by[i]['english_segments']) for i in selected) == summary['cumulative_reviewed_segments'] == 3677)
        check('all_27_review_audit_bindings', len(summary['review_audits']) == 27 and {item['review'] for item in summary['review_audits']} == set(review_audits))
        for item in summary['review_audits']:
            expected = review_audits[item['review']]
            check('review_audit_' + item['review'], all(item[k] == expected[k] for k in ('input', 'input_sha256', 'review_sha256')) and item['human_validation'] is False)
        reviews = overlay['model_review_records']
        check('overlay_exact_complete_review_order', [r['id'] for r in reviews] == selected)
        emap, pmap, rmap = {}, {}, {}
        for kind, records, mapping in [('note', overlay['note_review_events'], emap), ('patch', overlay['applied_translation_patches'], pmap), ('review', reviews, rmap)]:
            for entry in records:
                identifier = entry['id']
                row = by[identifier]
                key = (identifier, entry['note_index']) if kind == 'note' else ((identifier, entry['segment_index']) if kind == 'patch' else identifier)
                check('bound_' + kind + '_' + str(key), identifier in flagged and entry['source_sha256'] == digest({k: row[k] for k in SOURCE_FIELDS}) and entry['baseline_record_sha256'] == digest(row) and entry['review_source'] == sources[identifier] and key not in mapping)
                if kind != 'patch':
                    check('model_only_' + kind + '_' + str(key), entry['human_validation'] is False)
                if kind == 'note':
                    check('valid_note_index_' + str(key), type(entry['note_index']) is int and 0 <= entry['note_index'] < len(row['uncertainty_notes']))
                if kind == 'patch':
                    index = entry['segment_index']
                    check('valid_patch_index_' + str(key), type(index) is int and 0 <= index < len(row['ukrainian_segments']))
                    check('preserved_patch_source_references_' + str(key), collections.Counter(REFERENCES.findall(entry['after'])) == collections.Counter(REFERENCES.findall(row['english_segments'][index])))
                mapping[key] = entry
        proposals = read(dest / 'ALL_CORRECTION_PROPOSALS.json')
        proposal_map = {(p['id'], p['segment_index']): p for p in proposals}
        review_proposals = {(identifier, p['segment_index']): p for identifier, entry in review_entries.items() for p in entry['segment_corrections']}
        check('all_segment_proposals_accounted_for', len(proposal_map) == len(proposals) == len(review_proposals) and set(proposal_map) == set(review_proposals))
        for key, proposal in proposal_map.items():
            check('exact_review_proposal_' + str(key), all(proposal[k] == value for k, value in review_proposals[key].items()) and proposal['review_source'] == sources[key[0]])
            check('proposal_application_status_' + str(key), (proposal['application_status'] == 'applied_high_confidence' and pmap.get(key) == proposal) or (proposal['application_status'] == 'proposed_only' and key not in pmap))
        current = read(dest / 'dictionary.json')
        check('all_original_ids_and_order_preserved', [r['id'] for r in current] == [r['id'] for r in base])
        expected_ledger, expected_quarantine, mismatches = [], [], []
        source_mutations, uncertainty_mutations = [], []
        for row, actual in zip(base, current):
            expected = copy.deepcopy(row)
            expected['uncertainty_notes'] = []
            for index, note in enumerate(row['uncertainty_notes']):
                event = emap.get((row['id'], index))
                disposition = event['disposition'] if event else 'quarantine_unreviewed'
                evidence = {'id': row['id'], 'source_sha256': digest({k: row[k] for k in SOURCE_FIELDS}), 'baseline_record_sha256': digest(row), 'note_index': index, 'original_note_sha256': digest(note), 'original_note': note, 'disposition': disposition, 'original_uncertainty_flags': row['uncertainty_flags'], 'original_has_known_uncertainty': row['has_known_uncertainty'], 'review_source': event['review_source'] if event else None, 'reason': event['reason'] if event else 'No exact-ID/source/note-hash attachment review has been recorded.'}
                if event:
                    check('exact_note_binding_' + row['id'], event['original_note'] == note and event['original_note_sha256'] == digest(note) and event['review_type'] == 'model')
                if disposition == 'retain_reviewed':
                    expected['uncertainty_notes'].append(note)
                elif disposition == 'replace_reviewed':
                    expected['uncertainty_notes'].append(event['replacement'])
                    evidence['active_replacement'] = event['replacement']
                if disposition != 'retain_reviewed':
                    expected_quarantine.append(evidence)
                expected_ledger.append(evidence)
            for index, original in enumerate(row['ukrainian_segments']):
                patch = pmap.get((row['id'], index))
                if patch:
                    check('exact_patch_' + str((row['id'], index)), patch['before'] == original and patch['after'] != original and patch['confidence'] == 'high')
                    expected['ukrainian_segments'][index] = patch['after']
                    expected['correction_count'] += 1
            if row['id'] in rmap:
                expected.update(model_reviewed=True, review_status='model_reviewed', review_rating_before_corrections=rmap[row['id']]['rating'])
            if expected != actual:
                mismatches.append(row['id'])
            if any(actual[k] != row[k] for k in SOURCE_FIELDS):
                source_mutations.append(row['id'])
            if any(actual[k] != row[k] for k in ('has_known_uncertainty', 'uncertainty_flags')):
                uncertainty_mutations.append(row['id'])
        check('independent_final_dictionary_reconstruction', not mismatches, mismatches[:10])
        check('immutable_source_fields_preserved', not source_mutations)
        check('all_original_uncertainty_flags_and_markers_preserved', not uncertainty_mutations)
        for name, expected in [('NOTE_REVIEW_LEDGER.json', expected_ledger), ('NOTE_QUARANTINE.json', expected_quarantine)]:
            wrapper = read(dest / name)
            check('independent_' + name, wrapper['baseline_dictionary_sha256'] == BASE_SHA and wrapper['notes'] == expected)
        counts = {'records': len(current), 'aligned_segments': sum(len(r['english_segments']) for r in current), 'model_reviewed_records': sum(r['model_reviewed'] for r in current), 'corrected_segments': sum(r['correction_count'] for r in current), 'records_with_corrections': sum(r['correction_count'] > 0 for r in current), 'known_flagged_records': sum(r['has_known_uncertainty'] for r in current), 'human_validated_records': sum(r['human_validation'] for r in current)}
        dispositions = dict(sorted(collections.Counter(e['disposition'] for e in expected_ledger).items()))
        stats = {'baseline_records': len(base), 'source_segments': counts['aligned_segments'], 'notes_total': len(expected_ledger), 'notes_by_disposition': dispositions, 'active_notes': sum(len(r['uncertainty_notes']) for r in current), 'quarantined_original_notes': len(expected_quarantine), 'preserved_flagged_records': counts['known_flagged_records'], 'checkpoint_reviewed_records': len(rmap), 'applied_segment_corrections': len(pmap), 'human_validated_records': counts['human_validated_records']}
        check('counts_and_stats_exact', summary['counts'] == counts and summary['stats'] == stats)
        check('all_reviewed_none_human_validated', counts['human_validated_records'] == 0 and all(r['human_validation'] is False for r in current) and summary['cumulative_reviewed_records'] == 2534 and summary['remaining_flagged_entries_unreviewed'] == 0)
        known = {f['id'] for f in read(ROOT / 'note-provenance-diagnosis.json')['confirmed_findings']}
        current_by = {r['id']: r for r in current}
        check('known_15_contaminated_original_notes_inactive', len(known) == 15 and all(n not in current_by[i]['uncertainty_notes'] for i in known for n in by[i]['uncertainty_notes']))
        for name in ('note_gate.py', 'replay_cumulative_overlay.py', 'verify_versioned_checkpoint.py', 'compile_review_checkpoint.py', 'compile_repair_candidate.py', 'test_note_gate.py', 'note-provenance-diagnosis.json', 'gate_independent_review.json', 'remaining_flagged_review_queue.json', 'VERIFIED_HANDOFF.json', 'cumulative_handoff_audit.py', 'cumulative_handoff_audit.final.py'):
            file(ROOT / name, 'reproducibility or supporting audit evidence')
        immutable = all(sha(ROOT / key if not pathlib.Path(key).is_absolute() else key) == item['sha256'] for key, item in inventory.items())
        check('all_inventoried_files_unchanged_during_audit', immutable)
        review_outcomes = dict(collections.Counter(e['outcome'] for e in review_entries.values()))
        review_ratings = dict(collections.Counter(e['rating'] for e in reviews))
        result.update(status='pass', counts=counts, stats=stats, model_review_outcomes=review_outcomes, cumulative_review_ratings=review_ratings, total_segment_proposals=len(proposals), held_segment_proposals=len(proposals)-len(pmap), reviewed_flagged_source_segments=3677, baseline_sha256=BASE_SHA, final_dictionary_sha256=summary['corrected_dictionary_sha256'], all_2534_flagged_reviewed_exactly_once=True, independent_dictionary_ledger_quarantine_reconstruction=True, intermediate_dictionaries_read=False, human_validation=False, linguistic_accuracy_certified=False)
    except Exception as exc:
        result.update(status='fail', error=type(exc).__name__ + ': ' + str(exc))
    result.update(checks=checks, checks_passed=sum(c['passed'] for c in checks), checks_run=len(checks), evidence_inventory=inventory, evidence_files=len(inventory))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=pathlib.Path, required=True)
    args = parser.parse_args()
    result = audit()
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('checks', 'evidence_inventory')}, ensure_ascii=False, indent=2))
    sys.exit(0 if result['status'] == 'pass' else 1)
