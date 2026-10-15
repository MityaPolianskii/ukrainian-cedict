"""Fail-closed, ID- and source-hash-bound note gate. No network or in-place writes.
Generated legacy notes are quarantined until an explicit model/human attachment
review binds the exact note to the exact immutable source record. This is an
attachment/provenance gate, not proof that translations or source facts are true.
"""
import copy, hashlib, json, collections, re

class GateValidationError(ValueError):
    pass
SOURCE_FIELDS = ('id', 'traditional', 'simplified', 'pinyin', 'english_segments', 'raw_source', 'source_line')
HAN = '[\\u3400-\\u4dbf\\u4e00-\\u9fff\\uf900-\\ufaff\\U00020000-\\U000323af]+'
REFERENCES = re.compile(HAN + '(?:\\|' + HAN + ')?(?:\\[[^\\]\\n]+\\])?|\\[[^\\]\\n]+\\]')

def nonblank(value):
    return type(value) is str and bool(value.strip())

def validate_baseline(rows):
    if type(rows) is not list or not rows:
        raise GateValidationError('baseline must be a nonempty list')
    for r in rows:
        if type(r) is not dict:
            raise GateValidationError('baseline row must be an object')
        for k in ('id','traditional','simplified','pinyin','raw_source','translation_status','review_status'):
            if not nonblank(r.get(k)):
                raise GateValidationError('invalid baseline string: '+k)
        for k in ('english_segments','ukrainian_segments','uncertainty_notes','uncertainty_flags'):
            if type(r.get(k)) is not list or not all(nonblank(v) for v in r[k]):
                raise GateValidationError('invalid baseline string array: '+k)
        if not r['english_segments'] or len(r['english_segments']) != len(r['ukrainian_segments']):
            raise GateValidationError('baseline segment alignment mismatch')
        for k in ('human_validation','model_reviewed','has_known_uncertainty'):
            if type(r.get(k)) is not bool:
                raise GateValidationError('invalid baseline boolean: '+k)
        if type(r.get('correction_count')) is not int or r['correction_count']<0 or type(r.get('source_line')) is not int or r['source_line']<1:
            raise GateValidationError('invalid baseline integer')
        if r['has_known_uncertainty'] != bool(r['uncertainty_notes'] or r['uncertainty_flags']):
            raise GateValidationError('inconsistent baseline uncertainty marker')
        if r['uncertainty_notes'] and not r['uncertainty_flags']:
            raise GateValidationError('a note needs a persistent uncertainty flag before quarantine')

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def source_hash(row):
    return digest({k: row[k] for k in SOURCE_FIELDS})

def note_event(row, note_index, disposition, replacement=None, reason='', review_source=''):
    if not disposition in {'retain_reviewed', 'replace_reviewed', 'quarantine_rejected'}:
        raise GateValidationError('gate validation failed')
    original = row['uncertainty_notes'][note_index]
    if not (nonblank(reason) and nonblank(review_source)):
        raise GateValidationError('gate validation failed')
    if disposition == 'replace_reviewed':
        if not (isinstance(replacement, str) and replacement.strip()):
            raise GateValidationError('gate validation failed')
    return {'id': row['id'], 'source_sha256': source_hash(row), 'baseline_record_sha256': digest(row), 'note_index': note_index, 'original_note_sha256': digest(original), 'original_note': original, 'disposition': disposition, 'replacement': replacement, 'reason': reason, 'review_source': review_source, 'review_type': 'model', 'human_validation': False}

def apply_gate(rows, events, translation_patches=(), review_records=()):
    validate_baseline(rows)
    by = {r['id']: r for r in rows}
    if not len(by) == len(rows):
        raise GateValidationError('duplicate source IDs')
    ev = {}
    for e in events:
        if not e['id'] in by:
            raise GateValidationError('unknown event ID')
        r = by[e['id']]
        if not e['source_sha256'] == source_hash(r):
            raise GateValidationError('source-hash mismatch')
        if not e['baseline_record_sha256'] == digest(r):
            raise GateValidationError('stale baseline record')
        i = e['note_index']
        if not (type(i) is int and 0 <= i < len(r['uncertainty_notes'])):
            raise GateValidationError('invalid note index')
        if not e['original_note_sha256'] == digest(r['uncertainty_notes'][i]):
            raise GateValidationError('note-hash mismatch')
        if not e['original_note'] == r['uncertainty_notes'][i]:
            raise GateValidationError('original-note mismatch')
        if not (nonblank(e['reason']) and nonblank(e['review_source'])):
            raise GateValidationError('missing attachment-review evidence')
        if not e['disposition'] in {'retain_reviewed', 'replace_reviewed', 'quarantine_rejected'}:
            raise GateValidationError('unknown disposition')
        if e['disposition'] == 'replace_reviewed':
            if not (isinstance(e['replacement'], str) and e['replacement'].strip()):
                raise GateValidationError('empty replacement')
        k = (e['id'], i)
        if not k not in ev:
            raise GateValidationError('duplicate note approval')
        ev[k] = e
    patchmap = {}
    for p in translation_patches:
        if not p['id'] in by:
            raise GateValidationError('unknown patch ID')
        r = by[p['id']]
        if not p['source_sha256'] == source_hash(r):
            raise GateValidationError('patch source-hash mismatch')
        if not p['baseline_record_sha256'] == digest(r):
            raise GateValidationError('stale patch baseline')
        j = p['segment_index']
        if not (type(j) is int and 0 <= j < len(r['ukrainian_segments'])):
            raise GateValidationError('bad segment index')
        if not r['ukrainian_segments'][j] == p['before']:
            raise GateValidationError('patch before mismatch')
        if not (isinstance(p['after'], str) and p['after'].strip()):
            raise GateValidationError('empty translation')
        if p['after'] == p['before']:
            raise GateValidationError('no-op correction')
        if not p['confidence'] == 'high':
            raise GateValidationError('only high-confidence patches auto-applied')
        if not collections.Counter(REFERENCES.findall(r['english_segments'][j])) == collections.Counter(REFERENCES.findall(p['after'])):
            raise GateValidationError('reference preservation failure')
        k = (p['id'], j)
        if not k not in patchmap:
            raise GateValidationError('duplicate segment patch')
        patchmap[k] = p
    reviewmap = {}
    for q in review_records:
        if not (q['id'] in by and q['id'] not in reviewmap):
            raise GateValidationError('invalid/duplicate review ID')
        if not q['source_sha256'] == source_hash(by[q['id']]):
            raise GateValidationError('review source-hash mismatch')
        if not q['baseline_record_sha256'] == digest(by[q['id']]):
            raise GateValidationError('stale review baseline')
        if not q['rating'] in {'pass', 'minor', 'major', 'unresolved'}:
            raise GateValidationError('unknown rating')
        reviewmap[q['id']] = q
    out = copy.deepcopy(rows)
    quarantine = []
    ledger = []
    for r in out:
        original = by[r['id']]
        active = []
        for i, n in enumerate(original['uncertainty_notes']):
            e = ev.get((r['id'], i))
            d = e['disposition'] if e else 'quarantine_unreviewed'
            item = {'id': r['id'], 'source_sha256': source_hash(original), 'baseline_record_sha256': digest(original), 'note_index': i, 'original_note_sha256': digest(n), 'original_note': n, 'disposition': d, 'original_uncertainty_flags': copy.deepcopy(original['uncertainty_flags']), 'original_has_known_uncertainty': original['has_known_uncertainty'], 'review_source': e['review_source'] if e else None, 'reason': e['reason'] if e else 'No exact-ID/source/note-hash attachment review has been recorded.'}
            if d == 'retain_reviewed':
                active.append(n)
            elif d == 'replace_reviewed':
                active.append(e['replacement'])
                item['active_replacement'] = e['replacement']
                quarantine.append(item)
            else:
                quarantine.append(item)
            ledger.append(item)
        r['uncertainty_notes'] = active
        for j in range(len(r['ukrainian_segments'])):
            if (r['id'], j) in patchmap:
                r['ukrainian_segments'][j] = patchmap[r['id'], j]['after']
                r['correction_count'] += 1
        if r['id'] in reviewmap:
            r['model_reviewed'] = True
            r['review_status'] = 'model_reviewed'
            r['review_rating_before_corrections'] = reviewmap[r['id']]['rating']
        if not all((r[k] == original[k] for k in SOURCE_FIELDS)):
            raise GateValidationError('source mutation')
        if not r['uncertainty_flags'] == original['uncertainty_flags']:
            raise GateValidationError('uncertainty flag removed')
        if not r['has_known_uncertainty'] == original['has_known_uncertainty']:
            raise GateValidationError('uncertainty marker altered')
        if not len(r['english_segments']) == len(r['ukrainian_segments']):
            raise GateValidationError('alignment change')
        if not r['human_validation'] is False:
            raise GateValidationError('unsupported human validation')
    if not [r['id'] for r in rows] == [r['id'] for r in out]:
        raise GateValidationError('record/order loss')
    counts = collections.Counter((i['disposition'] for i in ledger))
    stats = {'baseline_records': len(rows), 'source_segments': sum((len(r['english_segments']) for r in rows)), 'notes_total': len(ledger), 'notes_by_disposition': dict(sorted(counts.items())), 'active_notes': sum((len(r['uncertainty_notes']) for r in out)), 'quarantined_original_notes': len(quarantine), 'preserved_flagged_records': sum((r['has_known_uncertainty'] for r in out)), 'checkpoint_reviewed_records': len(reviewmap), 'applied_segment_corrections': len(patchmap), 'human_validated_records': sum((r['human_validation'] for r in out))}
    return (out, quarantine, ledger, stats)
