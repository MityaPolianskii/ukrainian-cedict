#!/usr/bin/env python3
"""Read-only independent audit of final applied/held proposal decisions and preserved first-checkpoint deferrals."""
import argparse, collections, hashlib, json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parent
FINAL=ROOT/'candidate-checkpoint-009'

def read(path):
 return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()

def audit():
 checks=[]; protected={}; held=[]
 def check(name,test):
  checks.append({'name':name,'passed':bool(test)})
  if not test:raise ValueError(name)
 def protect(path):protected[str(path.relative_to(ROOT))]=sha(path)
 result={'scope':'Exact applied/held decisions, cumulative deferred evidence and conservative note activation. No linguistic certification or human validation.'}
 try:
  summary=read(FINAL/'REPAIR_SUMMARY.json');overlay=read(FINAL/'REPAIR_OVERLAY.json')
  protect(FINAL/'REPAIR_SUMMARY.json')
  for name,expected in summary['artifacts'].items():
   protect(FINAL/name);check('final_artifact_'+name,sha(FINAL/name)==expected)
  emap={(e['id'],e['note_index']):e for e in overlay['note_review_events']}
  pmap={(p['id'],p['segment_index']):p for p in overlay['applied_translation_patches']}
  proposals={(p['id'],p['segment_index']):p for p in read(FINAL/'ALL_CORRECTION_PROPOSALS.json')}
  reviewmap={q['id']:q for q in overlay['model_review_records']}
  initial_summary=read(ROOT/'corrected-candidate/REPAIR_SUMMARY.json')
  initial_overlay=read(ROOT/'corrected-candidate/REPAIR_OVERLAY.json')
  protect(ROOT/'corrected-candidate/REPAIR_SUMMARY.json');protect(ROOT/'corrected-candidate/REPAIR_OVERLAY.json')
  check('initial_overlay_verified_hash',sha(ROOT/'corrected-candidate/REPAIR_OVERLAY.json')==initial_summary['artifacts']['REPAIR_OVERLAY.json'])
  expected_deferred=list(initial_overlay['deferred_decisions'])
  all_inputs={}; all_entries={}; decision_counts=collections.Counter()
  for number in range(1,10):
   cp=ROOT/f'checkpoint-{number:03}'; entries={}; ids=[]
   for shard in range(1,4):
    ip=cp/f'input_{shard:03}.json';rp=cp/f'review_{shard:03}.json'
    protect(ip);protect(rp);rows=read(ip);review=read(rp)
    check(f'{number}_{shard}_exact_order',[r['id'] for r in rows]==review['reviewed_ids']==[e['id'] for e in review['entries']])
    for row,e in zip(rows,review['entries']):all_inputs[row['id']]=row;entries[e['id']]=e;all_entries[e['id']]=e;ids.append(e['id'])
   if number==1:continue
   dp=cp/'application_decisions.json';protect(dp);decision_file=read(dp)
   decisions=decision_file['decisions'];dm={(d['kind'],d['id'],d['index']):d for d in decisions}
   check(f'{number}_decisions_unique',len(dm)==len(decisions))
   for shard in range(1,4):check(f'{number}_{shard}_decisions_bound',decision_file['review_file_sha256'][f'review_{shard:03}.json']==sha(cp/f'review_{shard:03}.json'))
   used=set()
   for identifier in ids:
    row,e=all_inputs[identifier],entries[identifier];applied=[];has_hold=False
    note_proposals={row['uncertainty_notes'].index(p['before']):p for p in e['note_corrections']}
    for index,note in enumerate(row['uncertainty_notes']):
     event=emap.get((identifier,index));proposal=note_proposals.get(index)
     if proposal is None:
      check('unchanged_reviewed_note_'+identifier,event is not None and event['disposition']=='retain_reviewed');continue
     key=('note',identifier,index);d=dm[key];used.add(key);decision_counts['note_'+d['decision']]+=1
     check('note_decision_valid_'+identifier,d['decision'] in {'apply','hold'} and isinstance(d['reason'],str) and bool(d['reason'].strip()))
     if d['decision']=='apply':
      disposition='quarantine_rejected' if proposal['after'] is None else 'replace_reviewed'
      check('applied_note_exact_'+identifier,proposal['confidence']=='high' and event is not None and event['disposition']==disposition and event['replacement']==proposal['after'] and event['reason']==proposal['reason']+' Application review: '+d['reason'])
     else:
      has_hold=True
      expected_deferred.append({'id':identifier,'type':'note_proposal_deferred','proposal':proposal,'reason':d['reason'],'checkpoint':number})
      if d.get('original_attachment_approved') is True:
       check('held_note_explicit_original_approval_'+identifier,event is not None and event['disposition']=='retain_reviewed')
      else:check('held_note_safely_inactive_'+identifier,event is None)
      held.append({'kind':'note','id':identifier,'index':index,'checkpoint':number,'original_attachment_approved':d.get('original_attachment_approved') is True})
    for correction in e['segment_corrections']:
     index=correction['segment_index'];key=('segment',identifier,index);d=dm[key];used.add(key);decision_counts['segment_'+d['decision']]+=1
     proposal=proposals[(identifier,index)]
     check('segment_exact_proposal_'+str(key),all(proposal[k]==v for k,v in correction.items()) and correction['before']==row['ukrainian_segments'][index])
     check('segment_decision_valid_'+str(key),d['decision'] in {'apply','hold'} and isinstance(d['reason'],str) and bool(d['reason'].strip()))
     if d['decision']=='apply':
      check('applied_segment_exact_'+str(key),correction['confidence']=='high' and pmap[(identifier,index)]==proposal and proposal['application_status']=='applied_high_confidence' and proposal['application_review_reason']==d['reason']);applied.append(correction)
     else:
      has_hold=True
      check('held_segment_unapplied_'+str(key),(identifier,index) not in pmap and proposal['application_status']=='proposed_only' and proposal['application_hold_reason']==d['reason'])
      expected_deferred.append({'id':identifier,'type':'segment_proposal_deferred','proposal':proposal,'reason':d['reason'],'checkpoint':number})
      held.append({'kind':'segment','id':identifier,'index':index,'checkpoint':number})
    rating='unresolved' if e['outcome']=='deferred' or has_hold else ('minor' if e['outcome']=='correction_proposed' else 'pass')
    if rating=='minor' and any(p.get('issue_type') in {'mistranslation','wrong_sense','unsupported_intensification','argument_structure','missing_semantic_restriction'} for p in applied):rating='major'
    check('review_rating_matches_decisions_'+identifier,reviewmap[identifier]['rating']==rating)
   check(f'{number}_all_decisions_used_exactly_once',used==set(dm))
  check('exact_cumulative_deferred_ledger',overlay['deferred_decisions']==expected_deferred)
  current={r['id']:r for r in read(FINAL/'dictionary.json')}
  for item in expected_deferred:
   identifier=item['id'];proposal=item['proposal'];row=all_inputs[identifier]
   if item['type']=='segment_proposal_deferred':
    index=proposal['segment_index'];check('all_held_glosses_original_'+str((identifier,index)),current[identifier]['ukrainian_segments'][index]==row['ukrainian_segments'][index])
   else:
    index=row['uncertainty_notes'].index(proposal['before'])
    check('held_note_replacement_not_activated_'+identifier,proposal['after'] not in current[identifier]['uncertainty_notes'])
  inactive=[e['id'] for e in read(FINAL/'NOTE_QUARANTINE.json')['notes'] if e['disposition']=='quarantine_unreviewed']
  check('four_withheld_note_attachments',len(inactive)==4 and set(inactive)=={h['id'] for h in held if h['kind']=='note' and not h['original_attachment_approved']})
  protect(pathlib.Path(__file__))
  check('protected_evidence_unchanged',all(sha(ROOT/key)==value for key,value in protected.items()))
  result.update(status='pass',decision_counts_checkpoints_002_009=dict(decision_counts),cumulative_deferred_items=len(expected_deferred),cumulative_deferred_counts=dict(collections.Counter(d['type'] for d in expected_deferred)),four_inactive_note_ids=inactive,final_dictionary_sha256=summary['corrected_dictionary_sha256'])
 except Exception as exc:result.update(status='fail',error=type(exc).__name__+': '+str(exc))
 result.update(checks_passed=sum(c['passed'] for c in checks),checks_run=len(checks),checks=checks,protected_evidence_sha256=protected)
 return result

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=pathlib.Path,required=True);args=parser.parse_args();result=audit()
 with args.report.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('checks','protected_evidence_sha256')},ensure_ascii=False,indent=2));sys.exit(0 if result['status']=='pass' else 1)
