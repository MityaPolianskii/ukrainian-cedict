#!/usr/bin/env python3
"""Build an independent private candidate; never write to frozen inputs."""
import json,pathlib,hashlib,datetime,collections,copy
from note_gate import digest,source_hash,note_event,apply_gate,GateValidationError
ROOT=pathlib.Path(__file__).resolve().parent
CHECK=ROOT/'checkpoint-001'
EXPECTED='cdf73918ba4417090f8cdcc8d284ff3d47d65416e58de0efe7dcb610675fb465'
def require(ok,msg):
 if not ok:raise GateValidationError(msg)
def read(p):return json.loads(p.read_text())
def filehash(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,obj):
 text=json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
 if p.exists():require(p.read_text()==text,'Refusing to overwrite differing output: '+str(p))
 else:
  with p.open('x') as f:f.write(text)
def build():
 manifest=read(CHECK/'manifest.json');basepath=pathlib.Path(manifest['baseline_path']);require(filehash(basepath)==EXPECTED,'Frozen baseline hash mismatch');rows=read(basepath);by={r['id']:r for r in rows};events=[];patches=[];proposals=[];reviews=[];read_ids=[];review_audits=[];decision_audit=[]
 # Source-conflict changes must not automatically reverse Chinese-grounded wording.
 hold_segments={('72e6fe640783945b',1):'English cleanser is broader than Chinese 面膜; do not turn an explicitly flagged source conflict into an asserted broader Chinese dictionary sense.',('72e6fe640783945b',3):'English facial treatment is broader than Chinese 面膜; preserve existing Chinese-grounded wording pending source-editor decision.'}
 for shard in range(1,4):
  ip=CHECK/f'input_{shard:03}.json';rp=CHECK/f'review_{shard:03}.json';inputs=read(ip);rev=read(rp);require(rev['human_validation'] is False,'Unsupported human-validation claim');expected=[r['id'] for r in inputs];require(rev['reviewed_ids']==expected,'Review list/order mismatch');require([r['id'] for r in rev['entries']]==expected,'Review evidence list/order mismatch');review_audits.append({'input':str(ip.relative_to(ROOT)),'input_sha256':filehash(ip),'review':str(rp.relative_to(ROOT)),'review_sha256':filehash(rp),'reviewer_model_requested':rev.get('reviewer_model_requested'),'human_validation':False})
  for original,e in zip(inputs,rev['entries']):
   r=by[e['id']];require(original==r,'Review input differs from frozen record');require(all(e[k]==r[k] for k in ['id','source_line','traditional','simplified','pinyin']),'Review source identity mismatch');read_ids.append(r['id']);note_changes={}
   for n in e['note_corrections']:
    require(n['before'] in r['uncertainty_notes'],'Note correction before not present');i=r['uncertainty_notes'].index(n['before']);require(i not in note_changes,'Duplicate note correction');note_changes[i]=n
   for i,n in enumerate(r['uncertainty_notes']):
    c=note_changes.get(i)
    if c and c['confidence']=='high':
     disp='quarantine_rejected' if c['after'] is None else 'replace_reviewed';reason=c['reason'];replacement=c['after']
    else:
     disp='retain_reviewed';reason='All source fields, English/Ukrainian glosses and note inspected for this exact ID; the note is attached to the correct topic. Source facts and terminology may remain unresolved.';replacement=None
     if c:decision_audit.append({'id':r['id'],'type':'note_proposal_deferred','proposal':c,'reason':'Medium/low confidence note change is retained only as a proposal; original on-topic note remains flagged.'})
    events.append(note_event(r,i,disp,replacement,reason,str(rp.relative_to(ROOT))))
   accepted=[];held=[]
   for c in e['segment_corrections']:
    j=c['segment_index'];require(type(j)is int and 0<=j<len(r['ukrainian_segments']),'Invalid proposal segment');require(c['before']==r['ukrainian_segments'][j],'Proposal before mismatch');require(not ({'id','source_sha256','baseline_record_sha256','review_source'} & set(c)),'Correction payload may not override bound identity fields');proposal={'id':r['id'],'source_sha256':source_hash(r),'baseline_record_sha256':digest(r),**c,'review_source':str(rp.relative_to(ROOT))};reason=hold_segments.get((r['id'],j))
    if c['confidence']=='high' and reason is None:patches.append(proposal);accepted.append(c);proposal['application_status']='applied_high_confidence'
    else:proposal['application_status']='proposed_only';proposal['application_hold_reason']=reason or 'Not high confidence.';held.append(proposal);decision_audit.append({'id':r['id'],'type':'segment_proposal_deferred','proposal':proposal,'reason':proposal['application_hold_reason']})
    proposals.append(proposal)
   rating='unresolved' if e['outcome']=='deferred' or held else ('minor' if e['outcome']=='correction_proposed' else 'pass')
   if rating=='minor' and any(c.get('issue_type') in {'mistranslation','wrong_sense','unsupported_intensification','argument_structure','missing_semantic_restriction'} for c in accepted):rating='major'
   reviews.append({'id':r['id'],'source_sha256':source_hash(r),'baseline_record_sha256':digest(r),'rating':rating,'outcome':e['outcome'],'review_source':str(rp.relative_to(ROOT)),'human_validation':False})
 require(len(read_ids)==len(set(read_ids))==300,'Expected 300 distinct reviewed records');require(read_ids==manifest['selected_ids'],'Selected checkpoint differs from actual review')
 out,quarantine,ledger,stats=apply_gate(rows,events,patches,reviews)
 # Confirm every original note has exactly one disposition, including all known bad attachments.
 diag=read(ROOT/'note-provenance-diagnosis.json');confirmed=diag['confirmed_findings'];known_ids={f['id'] for f in confirmed};active_by={r['id']:r for r in out};legacy_known=[]
 for id_ in known_ids:
  require(active_by[id_]['uncertainty_flags']==by[id_]['uncertainty_flags'],'Confirmed defect lost flag')
  for n in by[id_]['uncertainty_notes']:require(n not in active_by[id_]['uncertainty_notes'],'Known contaminated note still active: '+id_)
  legacy_known.append(id_)
 require(filehash(basepath)==EXPECTED,'Baseline changed during build')
 dest=ROOT/'corrected-candidate';dest.mkdir(exist_ok=True)
 put(dest/'dictionary.json',out);put(dest/'NOTE_QUARANTINE.json',{'schema_version':1,'baseline_dictionary_sha256':EXPECTED,'meaning':'Original notes retained as evidence but not active dictionary annotations; this is not a claim that every quarantined note is false. Original uncertainty flags are preserved.','notes':quarantine});put(dest/'NOTE_REVIEW_LEDGER.json',{'schema_version':1,'baseline_dictionary_sha256':EXPECTED,'notes':ledger});put(dest/'REPAIR_OVERLAY.json',{'schema_version':1,'baseline_dictionary_sha256':EXPECTED,'source_hash_fields':['id','traditional','simplified','pinyin','english_segments','raw_source','source_line'],'note_review_events':events,'applied_translation_patches':patches,'model_review_records':reviews,'deferred_decisions':decision_audit});put(dest/'ALL_CORRECTION_PROPOSALS.json',proposals)
 counts={'records':len(out),'aligned_segments':sum(len(r['english_segments']) for r in out),'model_reviewed_records':sum(r['model_reviewed'] for r in out),'corrected_segments':sum(r['correction_count'] for r in out),'records_with_corrections':sum(r['correction_count']>0 for r in out),'known_flagged_records':sum(r['has_known_uncertainty'] for r in out),'human_validated_records':0}
 summary={'schema_version':1,'status':'private_corrected_candidate_pending_package_verification','baseline_path':str(basepath),'baseline_dictionary_sha256':EXPECTED,'corrected_dictionary_sha256':filehash(dest/'dictionary.json'),'baseline_immutable_verified':True,'all_source_fields_records_order_preserved':True,'all_uncertainty_flags_preserved':True,'known_contaminated_note_ids_inactive':sorted(legacy_known),'human_validation':False,'public_writes':False,'runtime_approved':False,'stats':stats,'counts':counts,'checkpoint_selected_records':300,'checkpoint_reviewed_records':300,'checkpoint_reviewed_segments':sum(len(by[i]['english_segments']) for i in read_ids),'newly_model_reviewed_records':sum(not by[i]['model_reviewed'] for i in read_ids),'review_outcomes':dict(collections.Counter(read(CHECK/f'review_{i:03}.json')['entries'][j]['outcome'] for i in range(1,4) for j in range(100))),'proposal_count':len(proposals),'deferred_proposals':sum(p['application_status']=='proposed_only' for p in proposals),'review_audits':review_audits,'limits':['Model review, not human validation or a corpus-wide accuracy estimate.','Unreviewed legacy notes are quarantined by default; flags remain to signal unresolved uncertainty.','Structural provenance audit does not certify all Ukrainian glosses semantically.','Only 300 of 2534 flagged entries received this full independent Chinese/English/Ukrainian checkpoint review.','Medium-confidence and disputed source-interpretation changes remain proposals only.'],'artifacts':{f.name:filehash(f) for f in sorted(dest.glob('*.json')) if f.name!='REPAIR_SUMMARY.json'}}
 put(dest/'REPAIR_SUMMARY.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
 return summary
if __name__=='__main__':build()
