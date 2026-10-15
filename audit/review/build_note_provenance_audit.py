"""Read-only corpus diagnosis. Writes only audit artifacts beside this script."""
import json,hashlib,datetime,collections,pathlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=pathlib.Path(__file__).resolve().parent
FROZEN=ROOT/'ukrainian-cedict-expansion12-9668/publish-public/dictionary.json'
BASELINE=ROOT/'ukrainian-cedict-expansion8-10000/publish-public/dictionary.json'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(ROOT))
def write(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
freeze_hash_before=sha(FROZEN);base_hash_before=sha(BASELINE)
final=read(FROZEN);fm={x['id']:x for x in final};base=read(BASELINE);bm={x['id']:x for x in base}
cohorts=[ROOT/'ukrainian-cedict-next10000']+[ROOT/f'ukrainian-cedict-expansion{i}-{9668 if i==12 else 10000}' for i in range(2,13)]
provenance={};stats=[];batch_audits=[];script_inventory=[];effective_notes=[]
for b in cohorts:
 stat={'cohort':b.name,'input_entries':0,'raw_entries':0,'raw_note_records':0,'effective_note_records':0,'effective_id_order_mismatches':[],'raw_id_order_mismatches':[],'raw_missing_ids':[],'raw_unknown_ids':[],'raw_duplicate_ids':[],'raw_hash_checkpoint_mismatches':[],'effective_segment_count_mismatches':[],'effective_source_field_mismatches':[],'effective_notes_differ_frozen':[],'effective_glosses_differ_frozen':[],'notes_changed_in_corrections':[]}
 for sp in sorted((b/'input').glob('batch_*.json')):
  rp=b/'raw'/sp.name;cp=b/'corrections'/sp.name;ep=cp if cp.exists() else rp
  src=read(sp);raw=read(rp);eff=read(ep);rm={x['id']:x for x in raw};em={x['id']:x for x in eff};sm={x['id']:x for x in src}
  si=[x['id'] for x in src];ri=[x['id'] for x in raw];ei=[x['id'] for x in eff]
  stat['input_entries']+=len(src);stat['raw_entries']+=len(raw);stat['raw_note_records']+=sum(bool(x.get('uncertainty_notes')) for x in raw);stat['effective_note_records']+=sum(bool(x.get('uncertainty_notes')) for x in eff)
  if si!=ri:stat['raw_id_order_mismatches'].append(sp.name)
  if si!=ei:stat['effective_id_order_mismatches'].append(sp.name)
  stat['raw_missing_ids']+=sorted(set(si)-set(ri));stat['raw_unknown_ids']+=sorted(set(ri)-set(si));stat['raw_duplicate_ids'] += [k for k,v in collections.Counter(ri).items() if v>1]
  vp=b/'validation'/sp.name;valid=read(vp) if vp.exists() else {}
  rawhash=sha(rp)
  if valid.get('raw_sha256') and valid['raw_sha256']!=rawhash:stat['raw_hash_checkpoint_mismatches'].append(sp.name)
  batch_audits.append({'cohort':b.name,'batch':sp.name,'input_sha256':sha(sp),'raw_sha256':rawhash,'effective_sha256':sha(ep),'effective_path':rel(ep),'validation_raw_sha256':valid.get('raw_sha256'),'source_ids_equal_raw_ids':si==ri,'source_ids_equal_effective_ids':si==ei})
  for i,s in enumerate(src):
   ident=s['id'];e=em[ident];r=rm.get(ident)
   if len(e['ukrainian_segments'])!=len(s['english_segments']):stat['effective_segment_count_mismatches'].append(ident)
   if any(fm[ident].get(k)!=v for k,v in s.items()):stat['effective_source_field_mismatches'].append(ident)
   if e['uncertainty_notes']!=fm[ident]['uncertainty_notes']:stat['effective_notes_differ_frozen'].append(ident)
   if e['ukrainian_segments']!=fm[ident]['ukrainian_segments']:stat['effective_glosses_differ_frozen'].append(ident)
   if e['uncertainty_notes']!=(r or {}).get('uncertainty_notes',[]):stat['notes_changed_in_corrections'].append(ident)
   pr={'cohort':b.name,'batch':sp.name,'zero_based_batch_index':i,'raw_path':rel(rp),'effective_path':rel(ep),'raw_record':r,'effective_record':e,'input_source':s,'raw_sha256':rawhash}
   provenance[ident]=pr
   if b==cohorts[0] and e['uncertainty_notes']:effective_notes.append(pr)
 stats.append(stat)
for p in sorted(ROOT.glob('ukrainian-cedict-*/*.py')):
 if OUT in p.parents:continue
 text=p.read_text();hits=[]
 for n,line in enumerate(text.splitlines(),1):
  if any(k in line for k in ['notes.get(i','uncertainty_notes=notes','for s,o in zip','IDs/order','Raw/effective IDs','type(notes)==list','Invalid notes:']):hits.append({'line':n,'code':line.strip()})
 script_inventory.append({'path':rel(p),'sha256':sha(p),'relevant_lines':hits})
# Candidate targets are evidence for origin, NOT authorized remapping operations.
DEFS=[
('b0679e8983a2fb13',['be3a2fe8cfa7e9b6'],'Shitizen note concerns P民, not PU/paternity uncertainty.','unique_topic_candidate'),
('d592d648f09d9428',['0c3e59873d7edb8f'],'House note belongs to the topic of 一木難支, same position in previous batch; current source is a bowl of water. Note also wrongly says house is implicit.','candidate_needs_rewrite'),
('0168943755f632b1',['6349e1851c8bde7b'],'Unitarianism belongs to adjacent 一神論, an original-baseline record, not this monotheistic-religion entry.','unique_topic_candidate'),
('92b953c247ece388',['2d13c8f31391138f'],'Formula One belongs to batch007 index69; note attached to batch008 index69, along the way.','unique_topic_candidate'),
('3ee7e352b216472a',['3c99603c3c95afda'],'Orthography and examples belong to 一致字 at index99 in preceding batch; current source is one after another.','unique_topic_candidate'),
('c78cae2d3e5f1fb9',['9e2cb1969663823d'],'Three duties note is unrelated to the Third. Previous-batch index29 is seven duties; the changed number means even candidate source cannot be accepted verbatim.','ambiguous_or_hallucinated'),
('87e972dbb1b47cc9',['f2442d9584e52f5e'],'DINK belongs to 丁克; same note also references the current Womens Day holiday. It is blended, not a wholly movable note.','blended_note_do_not_move'),
('4355846ebc6874c8',['f1175f2b0361e97e'],'Buddhist-phrase note unrelated to county cross-reference. Previous-batch index98 concerns Daoist souls, not Buddhism; no defensible exact target.','ambiguous_or_hallucinated'),
('fed846504a2bb8b4',['52abc628ac1b7e37'],'Explicit 丱 and guan4 identify batch036 index86, not 串串 index88.','unique_topic_candidate'),
('410ff3a4d8eff115',['0ea7d852a518051c'],'Explicit 乑 and standing side by side identify index97, not 乍看 index87.','unique_topic_candidate'),
('b8ac45eaf5cef49a',['c0733b2d2f7a1b62','cfe4b8d84d6fd893'],'CH3COO and source phrase acetyl radical belong to indices92/93, not acetyl index88.','two_plausible_targets'),
('97a15e73b89ed7e4',['c0733b2d2f7a1b62','cfe4b8d84d6fd893'],'Identical acetyl/acetate note is unrelated to piracetam C6H10N2O2 index89; two possible sources at92/93.','two_plausible_targets'),
('203349f934e0f706',['46481879f3cc6776'],'Explicit pastry name 乳酪餅 belongs to index61; current index59 is cheese.','unique_topic_candidate'),
('cdf351e19875f62b',['3064590281324b11'],'Explicit 亂咕攘 and disturb belong to index65; current index70 is chaotic situation.','unique_topic_candidate'),
('9350153f3da653f2',['0130f4925875d75b'],'Ethnic group and Bo2 identify 僰 in previous batch096 index7; current batch097 index7 is Confucianism.','unique_topic_candidate'),
]
findings=[]
for ident,targets,why,status in DEFS:
 p=provenance[ident];f=fm[ident]
 cand=[]
 for tid in targets:
  t=fm[tid];tp=provenance.get(tid);delta=None
  if tp and tp['cohort']==p['cohort']:delta=(int(tp['batch'][6:9])-int(p['batch'][6:9]))*100+tp['zero_based_batch_index']-p['zero_based_batch_index']
  cand.append({'id':tid,'traditional':t['traditional'],'pinyin':t['pinyin'],'english_segments':t['english_segments'],'ukrainian_segments':t['ukrainian_segments'],'current_notes':t['uncertainty_notes'],'cohort':tp['cohort'] if tp else 'original_5596_baseline','batch':tp['batch'] if tp else None,'zero_based_batch_index':tp['zero_based_batch_index'] if tp else None,'selected_row_delta_target_minus_current':delta})
 findings.append({'id':ident,'traditional':f['traditional'],'pinyin':f['pinyin'],'source_line':f['source_line'],'english_segments':f['english_segments'],'ukrainian_segments':f['ukrainian_segments'],'uncertainty_notes':f['uncertainty_notes'],'classification':'confirmed_misattached_or_contaminated_note','reason':why,'target_status':status,'candidate_targets':cand,'first_available_artifact':p['raw_path'],'raw_sha256':p['raw_sha256'],'batch':p['batch'],'zero_based_batch_index':p['zero_based_batch_index'],'raw_notes_equal_frozen':p['raw_record']['uncertainty_notes']==f['uncertainty_notes'],'baseline_85596_record_equal_frozen':bm.get(ident)==f,'gloss_alignment_review':'Ukrainian senses follow this records English topic rather than the misplaced notes topic; not a claim of ideal wording or full semantic verification.'})
claims={
 '581e2b5796811c30':('contradicted_by_source','Note excludes the soft-drink brand, although source and translation explicitly include 7 Up and Hedy.'),
 '07a02959a82031a5':('contradicted_by_source','Note says source lacks a Latin name although Carpodacus dubius appears in both source and translation.'),
 '4afe4f4b2b9cce70':('contradicted_by_translation','Note claims Latin spelling Samuel C. C. Ting is retained in Ukrainian translation, which uses Cyrillic Семюел Ч. Ч. Тін.'),
 '7d1f51478fa398b0':('ambiguous_preservation_claim','Note claims official English name is retained; Ukrainian text translates name and retains only abbreviation BRI.'),
 '56ae793ce4055f31':('ambiguous_preservation_claim','Note calls title transliterated, but the title is translated into Ukrainian rather than transcribed from Chinese.'),
 'e73ca5509f99f801':('ambiguous_preservation_claim','Note says Latin form Nariaki retained in source etymon; Latin exists in source but is not reproduced in Ukrainian text. Clarify if intended to describe output.')
}
claim_findings=[]
for ident,(kind,why) in claims.items():
 f=fm[ident];p=provenance[ident]
 claim_findings.append({'id':ident,'traditional':f['traditional'],'english_segments':f['english_segments'],'ukrainian_segments':f['ukrainian_segments'],'uncertainty_notes':f['uncertainty_notes'],'classification':kind,'reason':why,'first_available_artifact':p['raw_path'],'raw_notes_equal_frozen':p['raw_record']['uncertainty_notes']==f['uncertainty_notes']})
byfind={x['id']:x for x in findings};byclaim={x['id']:x for x in claim_findings}
review=[]
for p in effective_notes:
 ident=p['effective_record']['id'];f=fm[ident]
 review.append({'id':ident,'traditional':f['traditional'],'batch':p['batch'],'zero_based_batch_index':p['zero_based_batch_index'],'source':f['raw_source'],'translation':f['ukrainian_segments'],'notes':f['uncertainty_notes'],'review_result':byfind[ident]['classification'] if ident in byfind else byclaim[ident]['classification'] if ident in byclaim else 'topic_alignment_checked_no_clear_attachment_error_found','scope':'Model review of note association only; factual correctness of every claim and full gloss correctness are not certified.'})
write('note-provenance-first-cohort-review.json',review)
write('note-provenance-batch-manifest.json',batch_audits)
write('note-provenance-script-inventory.json',script_inventory)
anchors=read(OUT/'note-anchor-candidates.json') if (OUT/'note-anchor-candidates.json').exists() else []
rootcause={
 'proven':'Misassociated/contaminated metadata is already inside initial raw output records. Effective-output assembly preserves those fields under the correct source IDs. Frozen final assembly is not where these notes moved.',
 'strong_inference':'Several wrong notes correspond to exactly the same zero-based position in the preceding batch; others have varied local offsets, refer to a baseline record omitted from the selection, or mix subjects. This supports stale/index-addressed note composition during generation, rather than a global record/ID shift.',
 'not_proven':'The first-cohort per-batch generation commands/model-invocation transcripts are not retained in the inspected working directory or its audit ZIP. A shared translation prompt survives but does not reveal the construction of the faulty per-record note assignments. Therefore no exact code line causing the original misattachments can be identified; generation hallucination versus manually reused index keys cannot be separated conclusively.',
 'saved_helper_evidence':'Later retained write helpers zip positional Ukrainian rows with input records and independently attach notes.get(i,[]), automatically assigning id=s[id]. They validate counts and Chinese-reference preservation in glosses, but do not bind notes to source identity. Their local notes initialization resets each call, so this is not evidence of automatic Python state leakage.',
 'global_offset_repair_rejected':True,
 'record_id_or_gloss_shift':'No assembly-time ID/gloss shift found in effective-to-frozen comparisons across all 119668 expansion entries. The 15 cases were directly compared semantically and their gloss topics are their own. Raw ID problems do exist separately in four early batches and were corrected in correction files; none is a reported note-mismatch batch.',
 'unknown_bound':'Confirmed attachment contamination is in next10000, as late as batch097. A non-exhaustive later-cohort anchor screen cannot prove later notes clean, and later positional helpers retain the same class of risk.'
}
recommendations=[
 {'id':'R1','target':'write_batch.py and writer_050_074.py equivalents','change':'Require rows and notes keyed by stable source ID, with asserted headword, pinyin and source hash at creation. Reject ordinal-only notes dictionaries and unknown IDs. Never silently attach notes to s[id] by position.'},
 {'id':'R2','target':'check_progress.py and expansion12 verify_package.py','change':'Add note-identity records: note_id, record_id, source_sha256, source_anchor, kind, review_status. Check source anchors where asserted. Flag absent Chinese strings/proper names/formulas as review candidates, not automatic errors, because source-correction notes legitimately mention alternatives.'},
 {'id':'R3','target':'regression fixtures','change':'Add fixtures for all 15 misattachments, including same-index prior-batch reuse, variable offsets, mixed DINK/holiday content, a target outside selected input (一神論), and ambiguous double acetyl targets. Tests must reject cross-record association even when IDs, segment counts and reference tokens pass.'},
 {'id':'R4','target':'assembly and uncertainty flags','change':'Separate review state from note-text presence. Preserve existing has_known_uncertainty and uncertainty_flags by monotone union when notes are quarantined. Current bool(notes) recomputation would silently lose flags after clearing text.'},
 {'id':'R5','target':'correction/provenance pipeline','change':'Keep raw immutable. Apply any note repair through an ID-keyed reviewed patch containing before/after hashes, exact original text, disposition and reviewer rationale; regenerate a new candidate only. Preserve archived original notes and audit ZIPs.'},
 {'id':'R6','target':'semantic review selection','change':'Review every note for subject alignment and claim consistency, including notes without Chinese tokens. Require explicit note-review coverage, not complex-gloss samples or structural pass status, before asserting metadata is clean.'},
 {'id':'R7','target':'frozen/published baseline reconciliation','change':'Flag correction as affecting the already-published baseline too; all 85596 baseline records are inherited unchanged. Do not describe it as only a final expansion defect.'},
 {'id':'R8','target':'end-to-end tests','change':'Permute source/translation ordering and repartition batches while preserving IDs. ID-keyed notes must remain on their target. Assert deterministic rerun equality, no original uncertainty flag loss, preservation of raw hashes, and zero unsupported restored notes.'}
]
plan={
 'changes_made_to_frozen_corpus':False,
 'preferred_safe_plan':'Create a separate candidate with ID-keyed note dispositions. Quarantine every note without an explicit per-ID semantic review; leave the original note text and record snapshot in an immutable sidecar. Retain every original uncertainty flag and add note_alignment_pending. Restore only reviewed/reworded notes under their verified IDs.',
 'minimum_known_scope':'Quarantine the 15 confirmed misattachments and 3 direct false claims; review/rewrite 3 ambiguous preservation claims. This fixes known cases only and must not be presented as proving all remaining notes reliable.',
 'cohort_bounded_option':'A first-cohort remediation can cover all 167 effective notes with the accompanying full note-topic review, but its 146 no-clear-attachment-error outcomes do not validate every factual claim. It does not justify calling later cohorts clean.',
 'full_corpus_scope':'2534 current notes total. If a fully defensible public clean-note claim is required before full per-ID review finishes, quarantine all not-yet-reviewed note text, including later cohorts, with all original uncertainty flags retained. Sources/glosses and raw audit files remain unchanged.',
 'no_automatic_remapping':'Even unique-topic targets require rewrite/semantic acceptance: some notes themselves contain unsupported claims. Mixed/ambiguous cases are quarantined, never guessed or offset-shifted.',
 'sidecar_fields':['record_id','source_hash','original_note','original_flags','original_has_known_uncertainty','original_raw_path','raw_hash','disposition','reason','candidate_target_ids','reviewer','review_time','replacement_note_if_reviewed'],
 'new_candidate_checks':['Original frozen files and archives hashes unchanged','All original uncertainty_flags retained per ID','No original has_known_uncertainty true becomes false','Quarantined texts absent from presented verified note field','Every restored note has explicit reviewed target ID and source hash','All raw audits retained','Coverage described as note-association review, not complete dictionary semantics']
}
report={
 'audit_version':1,'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'read_only_corpus_audit':True,
 'frozen_dictionary':{'path':rel(FROZEN),'sha256':freeze_hash_before,'records':len(final),'note_records':sum(bool(x['uncertainty_notes']) for x in final)},
 'baseline_85596':{'path':rel(BASELINE),'sha256':base_hash_before,'records':len(base),'note_records':sum(bool(x['uncertainty_notes']) for x in base),'exact_record_matches_in_frozen':sum(x==fm.get(x['id']) for x in base),'confirmed_note_defects_present':sum(x['id'] in bm for x in findings)},
 'scope':{'expansion_entries_audited_structurally':sum(x['input_entries'] for x in stats),'batches_audited':len(batch_audits),'first_cohort_raw_note_records':stats[0]['raw_note_records'],'first_cohort_effective_notes_topic_reviewed':len(review),'confirmed_misattached_or_contaminated_notes':len(findings),'direct_false_note_claims':sum(x['classification']!='ambiguous_preservation_claim' for x in claim_findings),'ambiguous_preservation_claims':sum(x['classification']=='ambiguous_preservation_claim' for x in claim_findings),'later_note_semantic_review':'Not exhaustive; 38 whole-corpus absent-Chinese-anchor candidates inspected, four early misattachments confirmed and remaining candidates principally legitimate alternative/source-error comparisons. Does not prove later notes correct.','no_full_corpus_semantics_claim':True},
 'root_cause':rootcause,'cohort_stats':stats,'confirmed_findings':findings,'other_note_claim_findings':claim_findings,'repair_or_quarantine_proposal':plan,'regression_recommendations':recommendations,
 'artifacts':{'batch_hashes':'note-provenance-batch-manifest.json','script_inventory':'note-provenance-script-inventory.json','all_167_first_cohort_note_reviews':'note-provenance-first-cohort-review.json','existing_chinese_anchor_candidates':'note-anchor-candidates.json'},
 'limits':['No public state or dictionary artifacts changed.','No surviving first-cohort generation script reproduces the initial error; exact trigger cannot be proven.','An ID/count/hash/reference-token pass is structural provenance only, not semantic quality.','On-topic notes can contain factual or wording errors.','Unique-topic association is not automatic approval to transplant note text.'],
 'immutability_check':{'frozen_sha256_after':sha(FROZEN),'baseline_sha256_after':sha(BASELINE)}
}
assert report['immutability_check']['frozen_sha256_after']==freeze_hash_before
assert report['immutability_check']['baseline_sha256_after']==base_hash_before
write('note-provenance-diagnosis.json',report)
print(json.dumps({'audit':str(OUT/'note-provenance-diagnosis.json'),'findings':len(findings),'first_cohort_reviewed':len(review),'cohort_stats':stats,'baseline_exact':report['baseline_85596']['exact_record_matches_in_frozen']},ensure_ascii=False,indent=2))
