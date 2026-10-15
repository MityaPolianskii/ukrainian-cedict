#!/usr/bin/env python3
"""Append a bounded reviewed checkpoint to an immutable, versioned candidate.
No frozen inputs or prior candidates are modified. Every proposed change needs
an explicit application decision whose file hashes bind it to its review.
"""
import argparse,collections,copy,hashlib,json,pathlib
from note_gate import digest,source_hash,note_event,apply_gate,GateValidationError
ROOT=pathlib.Path(__file__).resolve().parent
BASELINE=ROOT.parent/'ukrainian-cedict-expansion12-9668/publish-public/dictionary.json'
BASE_SHA='cdf73918ba4417090f8cdcc8d284ff3d47d65416e58de0efe7dcb610675fb465'
def require(test,message):
 if not test:raise GateValidationError(message)
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def put(path,value):
 raw=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
 if path.exists():require(path.read_text()==raw,'Refusing differing overwrite: '+str(path))
 else:
  with path.open('x') as f:f.write(raw)
def build(checkpoint):
 require(type(checkpoint)is int and 2<=checkpoint<=9,'checkpoint must be 2..9')
 cp=ROOT/f'checkpoint-{checkpoint:03}';prev=ROOT/('corrected-candidate' if checkpoint==2 else f'candidate-checkpoint-{checkpoint-1:03}');dest=ROOT/f'candidate-checkpoint-{checkpoint:03}'
 require(sha(BASELINE)==BASE_SHA,'Frozen baseline mismatch');base=read(BASELINE);by={r['id']:r for r in base}
 ps=read(prev/'REPAIR_SUMMARY.json');require(ps.get('checkpoint',1)==checkpoint-1,'Wrong predecessor checkpoint');require(sha(prev/'dictionary.json')==ps['corrected_dictionary_sha256'],'Prior candidate hash mismatch')
 for name,h in ps['artifacts'].items():require(sha(prev/name)==h,'Prior artifact hash mismatch: '+name)
 old=read(prev/'dictionary.json');overlay=read(prev/'REPAIR_OVERLAY.json');events=copy.deepcopy(overlay['note_review_events']);patches=copy.deepcopy(overlay['applied_translation_patches']);review_records=copy.deepcopy(overlay['model_review_records']);deferred=copy.deepcopy(overlay['deferred_decisions']);proposals=read(prev/'ALL_CORRECTION_PROPOSALS.json');audits=copy.deepcopy(ps['review_audits']);prior_ids={q['id'] for q in review_records}
 require(len(prior_ids)==300*(checkpoint-1),'Prior cumulative review count mismatch')
 # Replay inherited bound state before extending it; do not trust a prior label alone.
 replay,_,_,_=apply_gate(base,events,patches,review_records);require(replay==old,'Inherited candidate does not match its bound overlay')
 manifest=read(cp/'manifest.json');require(manifest['selected_count']==(134 if checkpoint==9 else 300),'Unexpected checkpoint size');queue=read(ROOT/'remaining_flagged_review_queue.json');require(queue['baseline_dictionary_sha256']==BASE_SHA,'Queue baseline mismatch');planned=queue['entries'][(checkpoint-2)*300:(checkpoint-1)*300];require(manifest['selected_ids']==[r['id'] for r in planned],'Checkpoint differs from approved remaining queue');require(all(r==by[r['id']] for r in planned),'Queue record differs from frozen source');decisions=read(cp/'application_decisions.json');require(decisions.get('application_review_completed') is True,'Missing explicit application review');dm={}
 for d in decisions['decisions']:
  require(type(d.get('id')) is str and d['id'].strip() and type(d.get('index')) is int and d['index']>=0,'Invalid decision identity/index')
  require(d['kind'] in {'segment','note'} and d['decision'] in {'apply','hold'},'Invalid decision')
  key=(d['kind'],d['id'],d['index']);require(key not in dm,'Duplicate application decision');require(type(d.get('reason'))is str and d['reason'].strip(),'Decision reason required');dm[key]=d
 new_ids=[];new_entries=[];used_decisions=set();new_patches=[];new_note_events=[]
 for shard in range(1,4):
  ip=cp/f'input_{shard:03}.json';rp=cp/f'review_{shard:03}.json';inputs=read(ip);review=read(rp);expected=[r['id'] for r in inputs];require(review['human_validation'] is False,'Unsupported human validation');require(review['reviewed_ids']==expected and [r['id'] for r in review['entries']]==expected,'Missing/duplicate/out-of-order reviewed entries');require(decisions['review_file_sha256'].get(rp.name)==sha(rp),'Application decisions do not bind current review bytes')
  audits.append({'input':str(ip.relative_to(ROOT)),'input_sha256':sha(ip),'review':str(rp.relative_to(ROOT)),'review_sha256':sha(rp),'reviewer_model_requested':review.get('reviewer_model_requested'),'human_validation':False})
  for original,e in zip(inputs,review['entries']):
   r=by[e['id']];require(r==original,'Review input not frozen source record');require(e['id'] not in prior_ids,'Checkpoint overlaps prior review');require(all(e[k]==r[k] for k in ['id','source_line','traditional','simplified','pinyin']),'Entry identity mismatch');require(e['outcome'] in {'acceptable','correction_proposed','deferred'},'Invalid review outcome');new_ids.append(e['id']);new_entries.append(e);nc={};held=False;applied=[]
   for n in e['note_corrections']:
    require(n['before'] in r['uncertainty_notes'],'Note before mismatch');i=r['uncertainty_notes'].index(n['before']);require(i not in nc,'Duplicate note proposal');key=('note',r['id'],i);require(key in dm,'Note proposal lacks application decision');d=dm[key];used_decisions.add(key);require(not(d['decision']=='apply' and n['confidence']!='high'),'Only high-confidence note proposal may apply');nc[i]=(n,d)
   for i,original_note in enumerate(r['uncertainty_notes']):
    if i in nc:
     n,d=nc[i]
     if d['decision']=='apply':disposition='quarantine_rejected' if n['after'] is None else 'replace_reviewed';replacement=n['after'];reason=n['reason']+' Application review: '+d['reason']
     else:
      deferred.append({'id':r['id'],'type':'note_proposal_deferred','proposal':n,'reason':d['reason'],'checkpoint':checkpoint});held=True
      if d.get('original_attachment_approved') is not True:
       continue
      disposition='retain_reviewed';replacement=None;reason='Original note explicitly approved for exact-ID attachment; proposed wording change held. '+d['reason']
    else:disposition='retain_reviewed';replacement=None;reason='All source fields, English/Ukrainian glosses and note individually inspected for this exact ID; note is attached to the correct topic. Source facts or nomenclature may remain unresolved.'
    event=note_event(r,i,disposition,replacement,reason,str(rp.relative_to(ROOT)));events.append(event);new_note_events.append(event)
   for c in e['segment_corrections']:
    require(not({'id','source_sha256','baseline_record_sha256','review_source'}&set(c)),'Correction payload overrides bound identity');j=c['segment_index'];require(type(j)is int and 0<=j<len(r['ukrainian_segments']),'Invalid segment index');require(c['before']==r['ukrainian_segments'][j],'Segment before mismatch');key=('segment',r['id'],j);require(key in dm,'Segment proposal lacks application decision');d=dm[key];require(key not in used_decisions,'Duplicate segment proposal');used_decisions.add(key);require(not(d['decision']=='apply' and c['confidence']!='high'),'Only high-confidence segment proposals apply');p={'id':r['id'],'source_sha256':source_hash(r),'baseline_record_sha256':digest(r),**c,'review_source':str(rp.relative_to(ROOT)),'checkpoint':checkpoint}
    if d['decision']=='apply':p['application_status']='applied_high_confidence';p['application_review_reason']=d['reason'];patches.append(p);new_patches.append(p);applied.append(c)
    else:p['application_status']='proposed_only';p['application_hold_reason']=d['reason'];deferred.append({'id':r['id'],'type':'segment_proposal_deferred','proposal':p,'reason':d['reason'],'checkpoint':checkpoint});held=True
    proposals.append(p)
   rating='unresolved' if e['outcome']=='deferred' or held else ('minor' if e['outcome']=='correction_proposed' else 'pass')
   if rating=='minor' and any(c.get('issue_type') in {'mistranslation','wrong_sense','unsupported_intensification','argument_structure','missing_semantic_restriction'} for c in applied):rating='major'
   review_records.append({'id':r['id'],'source_sha256':source_hash(r),'baseline_record_sha256':digest(r),'rating':rating,'outcome':e['outcome'],'review_source':str(rp.relative_to(ROOT)),'human_validation':False,'checkpoint':checkpoint})
 require(used_decisions==set(dm),'Unused or spurious application decision');require(new_ids==manifest['selected_ids'] and len(new_ids)==len(set(new_ids))==manifest['selected_count'],'Checkpoint selection/count mismatch');require(all(by[id_]['has_known_uncertainty'] for id_ in new_ids),'Checkpoint contains nonflagged entry')
 out,quarantine,ledger,stats=apply_gate(base,events,patches,review_records);newset=set(new_ids);require(all(a==b for a,b in zip(old,out) if a['id'] not in newset),'Prior/unselected record modified');require(len(review_records)==len(prior_ids)+len(new_ids),'Cumulative review count mismatch')
 diag=read(ROOT/'note-provenance-diagnosis.json');known_ids={f['id'] for f in diag['confirmed_findings']};outby={r['id']:r for r in out}
 for id_ in known_ids:
  for n in by[id_]['uncertainty_notes']:require(n not in outby[id_]['uncertainty_notes'],'Known contaminated original restored: '+id_)
 require(sha(BASELINE)==BASE_SHA and sha(prev/'dictionary.json')==ps['corrected_dictionary_sha256'],'Input changed during build')
 dest.mkdir(exist_ok=True);put(dest/'dictionary.json',out);put(dest/'NOTE_QUARANTINE.json',{'schema_version':1,'baseline_dictionary_sha256':BASE_SHA,'meaning':'Original notes retained as evidence but not active annotations; not every quarantined note is false. Original uncertainty flags remain.','notes':quarantine});put(dest/'NOTE_REVIEW_LEDGER.json',{'schema_version':1,'baseline_dictionary_sha256':BASE_SHA,'notes':ledger});put(dest/'REPAIR_OVERLAY.json',{'schema_version':1,'baseline_dictionary_sha256':BASE_SHA,'source_hash_fields':['id','traditional','simplified','pinyin','english_segments','raw_source','source_line'],'note_review_events':events,'applied_translation_patches':patches,'model_review_records':review_records,'deferred_decisions':deferred});put(dest/'ALL_CORRECTION_PROPOSALS.json',proposals)
 counts={'records':len(out),'aligned_segments':sum(len(r['english_segments']) for r in out),'model_reviewed_records':sum(r['model_reviewed'] for r in out),'corrected_segments':sum(r['correction_count'] for r in out),'records_with_corrections':sum(r['correction_count']>0 for r in out),'known_flagged_records':sum(r['has_known_uncertainty'] for r in out),'human_validated_records':0}
 summary={'schema_version':1,'checkpoint':checkpoint,'status':'private_versioned_review_candidate_pending_independent_verification','baseline_dictionary_sha256':BASE_SHA,'previous_candidate_directory':str(prev),'previous_dictionary_sha256':ps['corrected_dictionary_sha256'],'corrected_dictionary_sha256':sha(dest/'dictionary.json'),'baseline_immutable_verified':True,'previous_candidate_immutable_verified':True,'all_source_fields_records_order_preserved':True,'all_uncertainty_flags_preserved':True,'known_contaminated_note_ids_inactive':sorted(known_ids),'human_validation':False,'public_writes':False,'runtime_approved':False,'stats':stats,'counts':counts,'current_checkpoint_reviewed_records':len(new_ids),'current_checkpoint_reviewed_segments':sum(len(by[i]['english_segments']) for i in new_ids),'current_checkpoint_applied_segment_corrections':len(new_patches),'current_checkpoint_review_outcomes':dict(collections.Counter(e['outcome'] for e in new_entries)),'cumulative_reviewed_records':len(review_records),'cumulative_reviewed_segments':sum(len(by[q['id']]['english_segments']) for q in review_records),'remaining_flagged_entries_unreviewed':2534-len(review_records),'review_audits':audits,'application_decisions':str((cp/'application_decisions.json').relative_to(ROOT)),'application_decisions_sha256':sha(cp/'application_decisions.json'),'limits':['Model review, not human validation or corpus-wide accuracy estimate.','Unresolved Chinese/English source contradictions and specialist nomenclature remain flagged.','Default-quarantined notes can include reviewed entries whose note activation was withheld for unresolved evidence; entry review counts are tracked independently.','No publication or runtime approval.'],'artifacts':{f.name:sha(f) for f in sorted(dest.glob('*.json')) if f.name not in {'REPAIR_SUMMARY.json','INDEPENDENT_VERIFICATION.json'}}}
 put(dest/'REPAIR_SUMMARY.json',summary);return summary
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--checkpoint',type=int,required=True);args=p.parse_args();print(json.dumps(build(args.checkpoint),ensure_ascii=False,indent=2))
