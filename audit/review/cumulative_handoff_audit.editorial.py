#!/usr/bin/env python3
"""Independently verify the derived editorial priority/uncertainty inventories."""
import argparse,collections,hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parent
SOURCE_FIELDS=('id','traditional','simplified','pinyin','english_segments','raw_source','source_line')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def audit():
 checks=[];protected={}
 def check(n,v):
  checks.append({'name':n,'passed':bool(v)})
  if not v:raise ValueError(n)
 def protect(p):protected[str(p.relative_to(ROOT))]=sha(p)
 result={'scope':'Derived editorial queue and exact evidence bindings; editorial follow-up counts are not counts of distinct mistranslations.'}
 try:
  qp=ROOT/'EDITORIAL_FOLLOWUP_QUEUE.json';queue=read(qp);protect(qp)
  dest=ROOT/'candidate-checkpoint-009';summary=read(dest/'REPAIR_SUMMARY.json');overlay=read(dest/'REPAIR_OVERLAY.json');ledger=read(dest/'NOTE_REVIEW_LEDGER.json')['notes']
  for name in ('REPAIR_SUMMARY.json','REPAIR_OVERLAY.json','NOTE_REVIEW_LEDGER.json','dictionary.json'):protect(dest/name)
  check('queue_final_identity',queue['candidate_dictionary_sha256']==summary['corrected_dictionary_sha256']==sha(dest/'dictionary.json') and queue['baseline_dictionary_sha256']==summary['baseline_dictionary_sha256'])
  originals={};entries={};sources={}
  for audit in summary['review_audits']:
   ip,rp=ROOT/audit['input'],ROOT/audit['review'];protect(ip);protect(rp)
   check('bound_input_'+audit['input'],sha(ip)==audit['input_sha256']);check('bound_review_'+audit['review'],sha(rp)==audit['review_sha256'])
   for row,entry in zip(read(ip),read(rp)['entries']):originals[row['id']]=row;entries[entry['id']]=entry;sources[row['id']]=audit['review']
  check('complete_review_inputs',len(originals)==len(entries)==2534)
  current={r['id']:r for r in read(dest/'dictionary.json') if r['id'] in originals}
  held=collections.defaultdict(list);notes=collections.defaultdict(list)
  for item in overlay['deferred_decisions']:held[item['id']].append(item)
  for item in ledger:notes[item['id']].append({'note_index':item['note_index'],'disposition':item['disposition']})
  deferred={i for i,e in entries.items() if e['outcome']=='deferred'}
  inactive={n['id'] for n in ledger if n['disposition']=='quarantine_unreviewed'}
  expected_priority=deferred|set(held)|inactive
  actual_priority=[e['id'] for e in queue['priority_entries']]
  expected_uncertainty={i for i,e in entries.items() if e['remaining_uncertainty']}
  actual_uncertainty=[e['id'] for e in queue['reviewer_uncertainty_inventory']]
  check('exact_unique_priority_union',len(actual_priority)==len(set(actual_priority))==882 and set(actual_priority)==expected_priority)
  check('exact_unique_uncertainty_inventory',len(actual_uncertainty)==len(set(actual_uncertainty))==1978 and set(actual_uncertainty)==expected_uncertainty)
  def bound(item):
   i=item['id'];row=originals[i]
   return item['source_sha256']==digest({k:row[k] for k in SOURCE_FIELDS}) and item['baseline_record_sha256']==digest(row) and item['review_source']==sources[i] and item['review_source_sha256']==sha(ROOT/sources[i]) and all(item[k]==row[k] for k in ('source_line','traditional','simplified','pinyin'))
  for item in queue['priority_entries']:
   i=item['id'];e=entries[i];row=originals[i];actual=current[i]
   reasons=[]
   if i in deferred:reasons.append('reviewer_deferred_linguistic_or_source_issue')
   if i in held:reasons.append('application_proposal_held')
   if i in inactive:reasons.append('reviewed_note_activation_withheld')
   check('priority_binding_'+i,bound(item))
   check('priority_reasons_'+i,item['followup_reasons']==reasons)
   check('priority_verbatim_review_'+i,item['review_outcome']==e['outcome'] and item['review_confidence']==e['confidence'] and item['review_reason']==e['reason'] and item['remaining_uncertainty_verbatim']==e['remaining_uncertainty'])
   check('priority_actual_dictionary_'+i,item['english_segments']==row['english_segments'] and item['current_ukrainian_segments']==actual['ukrainian_segments'] and item['current_active_notes']==actual['uncertainty_notes'] and item['original_flags_preserved']==row['uncertainty_flags'] and item['human_validation'] is False)
   check('priority_exact_held_notes_'+i,item['held_proposals']==held.get(i,[]) and item['note_dispositions']==notes[i])
  for item in queue['reviewer_uncertainty_inventory']:
   i=item['id'];e=entries[i]
   check('uncertainty_binding_'+i,bound(item))
   check('uncertainty_verbatim_'+i,item['outcome']==e['outcome'] and item['remaining_uncertainty_verbatim']==e['remaining_uncertainty'])
  expected_counts={'review_outcomes':dict(collections.Counter(e['outcome'] for e in entries.values())),'priority_followup_entries':len(expected_priority),'held_proposal_operations':len(overlay['deferred_decisions']),'entries_with_held_proposals':len(held),'reviewer_uncertainty_inventory_entries':len(expected_uncertainty),'reviewed_notes_withheld_inactive':len(inactive)}
  check('queue_counts_exact',queue['counts']==expected_counts)
  check('queue_review_scope_exact',queue['review_scope']=={'original_flagged_entries_reviewed':2534,'unreviewed_original_flagged_entries':0,'source_segments_reviewed':3677,'unflagged_entries_not_in_this_pass':122730,'human_validated_records':0})
  unresolved={r['id'] for r in overlay['model_review_records'] if r['rating']=='unresolved'}
  extra=expected_priority-unresolved
  check('priority_vs_unresolved_explained',len(unresolved)==880 and unresolved<=expected_priority and extra=={'fe348ba4ce31d406','121478e440135ab6'} and all(entries[i]['outcome']=='correction_proposed' for i in extra))
  protect(pathlib.Path(__file__))
  check('protected_evidence_unchanged',all(sha(ROOT/k)==v for k,v in protected.items()))
  result.update(status='pass',queue_sha256=sha(qp),counts=expected_counts,compiled_unresolved_entries=len(unresolved),additional_priority_ids=sorted(extra),additional_priority_outcomes={i:entries[i]['outcome'] for i in sorted(extra)},human_validation=False,linguistic_accuracy_certified=False)
 except Exception as exc:result.update(status='fail',error=type(exc).__name__+': '+str(exc))
 result.update(checks_passed=sum(c['passed'] for c in checks),checks_run=len(checks),checks=checks,protected_evidence_sha256=protected)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=pathlib.Path,required=True);a=p.parse_args();r=audit()
 with a.report.open('x',encoding='utf-8') as f:json.dump(r,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in r.items() if k not in ('checks','protected_evidence_sha256')},ensure_ascii=False,indent=2));sys.exit(0 if r['status']=='pass' else 1)
