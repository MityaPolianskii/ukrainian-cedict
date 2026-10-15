#!/usr/bin/env python3
import pathlib,json,csv,hashlib,argparse,subprocess,sys
sys.dont_write_bytecode=True
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[1]);B=p.parse_args().root.resolve()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
E=B/'audit/review';H=read(E/'FINAL_VERIFIED_HANDOFF.json');require(sha(E/'FINAL_VERIFIED_HANDOFF.json')=='2a96fe27668fd684eb64daac37784961645c9354edd55d8695989fc41fcc37ed','Handoff hash');require(sha(B/'dictionary.json')==H['dictionary_sha256']=='166a286a68f278b73c3307284dbee879451c262608b1cbe0f8e9d6eca2d4474b','Dictionary hash');require((B/'dictionary.json').read_bytes()==(E/'candidate-checkpoint-009/dictionary.json').read_bytes(),'Active versus replay copy differs')
inv=read(B/'PACKAGED_EVIDENCE_INVENTORY.json');require(len(inv['files'])==154,'Evidence count');require(sha(E/'FINAL_ARTIFACT_INVENTORY.json')==inv['source_inventory_sha256'],'Source inventory hash')
for x in inv['files']:
 q=B/x['package_path'];require(q.stat().st_size==x['bytes'] and sha(q)==x['sha256'],'Evidence mismatch '+x['package_path'])
for optimized in [False,True]:
 cmd=[sys.executable,'-B']+(['-O'] if optimized else [])+[str(E/'replay_cumulative_overlay.py'),'--baseline',str(B/'history/frozen-original/dictionary.json'),'--candidate-dir',str(E/'candidate-checkpoint-009')];subprocess.run(cmd,check=True)
 subprocess.run([sys.executable,'-B']+(['-O'] if optimized else [])+['-m','unittest','test_note_gate','-q'],cwd=E,check=True)
rows=read(B/'dictionary.json');require(len(rows)==len({r['id'] for r in rows})==125264,'Count or IDs');require(sum(len(r['english_segments']) for r in rows)==199737,'Segments');counts={'records':len(rows),'aligned_segments':sum(len(r['english_segments']) for r in rows),'model_reviewed_records':sum(r['model_reviewed'] for r in rows),'corrected_segments':sum(r['correction_count'] for r in rows),'records_with_corrections':sum(r['correction_count']>0 for r in rows),'known_flagged_records':sum(r['has_known_uncertainty'] for r in rows),'human_validated_records':sum(r['human_validation'] for r in rows)}
prog=read(B/'progress.json');require(counts==prog['counts']==H['dictionary_cumulative_counts'],'Counts differ');require(prog['notes']==H['notes'] and prog['new_review']==H['new_review'],'Note/review totals');require(sum(len(r['uncertainty_notes']) for r in rows)==2512,'Active notes');require(sum(r['has_known_uncertainty'] and not r['uncertainty_notes'] for r in rows)==22,'Empty flagged entries');require(read(B/'CURRENT_REVIEW_QUEUE.json')==[r for r in rows if r['has_known_uncertainty']],'Current flags queue')
editorial=read(B/'CURRENT_EDITORIAL_FOLLOWUP.json')['records'];wanted={r['id'] for r in read(E/'EDITORIAL_FOLLOWUP_QUEUE.json')['priority_entries']};require(len(wanted)==882 and editorial==[r for r in rows if r['id'] in wanted],'Editorial derived data')
with (B/'dictionary.csv').open(encoding='utf-8-sig',newline='') as f:
 cs=list(csv.DictReader(f))
require(len(cs)==len(rows),'CSV count')
for r,c in zip(rows,cs):require(c=={k:json.dumps(v,ensure_ascii=False) if isinstance(v,list) else '' if v is None else str(v).lower() if isinstance(v,bool) else str(v) for k,v in r.items()},'CSV row mismatch')
for name,digest in prog['data_sha256'].items():require(sha(B/name)==digest,'Active data hash differs')
require(not (B/'NOTE_QUARANTINE.json').exists(),'Quarantined originals at active root');require(not list(B.glob('EXPANSION*_REVIEW_QUEUE.json')),'Legacy root queues');require(sha(B/'NOTE_REVIEW_LEDGER.json')==sha(E/'candidate-checkpoint-009/NOTE_REVIEW_LEDGER.json'),'Ledger differs');require(prog['human_validation'] is False and prog['runtime_approved'] is False,'Approval claims')
if (B/'SHA256SUMS.txt').exists():
 names=set()
 for line in (B/'SHA256SUMS.txt').read_text().splitlines():
  digest,name=line.split('  ',1);require(name not in names and '..' not in pathlib.Path(name).parts,'Checksum path');names.add(name);require(sha(B/name)==digest,'Package checksum '+name)
 require(names=={q.relative_to(B).as_posix() for q in B.rglob('*') if q.is_file() and q!=B/'SHA256SUMS.txt' and '__pycache__' not in q.parts},'Package inventory')
print(json.dumps({'status':'passed','counts':counts,'evidence_files':154,'portable_replay_normal_and_optimized':True,'gate_tests_normal':20,'gate_tests_optimized':20,'active_notes':2512,'preserved_flags':2534,'flagged_without_active_note':22,'csv_and_current_queues_exact':True,'human_validation':False,'runtime_approved':False}))
