#!/usr/bin/env python3
"""Standalone structural verifier; private AI-review replay remains separate."""
import argparse,csv,gzip,hashlib,io,json,xml.etree.ElementTree as ET
from pathlib import Path
import public_contract as c
SOURCE_SHA='237c0e6dab5c5b61f22b9c8e016aaeacb522359184b1b9c93b1da76b38518a69'
PRIOR_SHA={'fr':'b8ec76393f7d70c666a736585b20b18d23e437727f8dee3dabd5890e584c10cd','uk':'83ba415b0cc1314e22b35a3996788ffd891bdae165de3e6d9d3075c94f44898e'}
REVIEW_SHA={'fr':'710c14f6573094d603fa42c97342c59c221a10bd1ce0c81e5f46ac16b67e7785','uk':'52175ce2d53dceefdfaf8f92bc9e0110bfe6f5fa39513a7bdf8f576365b1288f'}
CURRENT=125330;DIFF={'added':12,'changed':16,'retired':6}
FORBIDDEN={'entryID','entry_id','appRowID','appID','baselineEntryID','popularity','HSK','userData','sourceFilePath'}
def file_sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def load(p):
 with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)
def no_private(v):
 if isinstance(v,dict):
  c.require(not set(v)&FORBIDDEN,'Private application field in public data')
  for x in v.values():no_private(x)
 elif isinstance(v,list):
  for x in v:no_private(x)
 elif isinstance(v,str):c.require(not any(s in v for s in ('/Users/','data/DictionaryUpdates/','runtime-identities/')),'Private path in public data')
def package_check(root):
 p=root/'PACKAGE-MANIFEST.json';c.require(p.is_file() and not p.is_symlink(),'Missing package manifest');m=json.loads(p.read_text())
 allowed={'ATTRIBUTION.md','README.md','source-records.json.gz','summary.json','public_contract.py','validate_public_advance.py'}
 allowed|={f'{lang}/{name}' for lang in ('fr','uk') for name in ('manifest.json','dictionary.json.gz','dictionary.csv.gz','delta-reviewed.json.gz','delta-reviewed.xml.gz')}
 c.require(m['schemaVersion']==1 and m['status']=='local-draft-awaiting-independent-review' and set(m['files'])==allowed,'Unexpected public package manifest')
 actual={}
 for f in root.rglob('*'):
  c.require(not f.is_symlink(),'Unexpected symlink in package');rel=f.relative_to(root).as_posix()
  if f.is_dir():c.require(rel in ('fr','uk'),'Unexpected package directory')
  elif f!=p:c.require(f.is_file(),'Unexpected package file');actual[rel]={'bytes':f.stat().st_size,'sha256':file_sha(f)}
 c.require(actual==m['files'],'Changed package files')
def branch_check(root,lang):
 # Public repos carry one locale per source-update directory, with source and
 # the standalone validator alongside it. The commit binds the whole layout;
 # the per-locale manifest and the pinned source/prior hashes bind its data.
 c.require(lang in ('fr','uk') and root.is_dir() and not root.is_symlink(),'Invalid branch layout')
 expected={'ATTRIBUTION.md','README.md','source-records.json.gz','public_contract.py','validate_public_advance.py'}
 expected|={f'{lang}/{name}' for name in ('manifest.json','dictionary.json.gz','dictionary.csv.gz','delta-reviewed.json.gz','delta-reviewed.xml.gz')}
 actual=set()
 for f in root.rglob('*'):
  c.require(not f.is_symlink(),'Unexpected branch symlink');name=f.relative_to(root).as_posix()
  if f.is_dir():c.require(name==lang,'Unexpected branch directory')
  else:c.require(f.is_file(),'Unexpected branch file');actual.add(name)
 c.require(actual==expected,'Unexpected branch layout')
def validate(folder,sourcefile,priorfile,check_package=True):
 folder,sourcefile,priorfile=map(Path,(folder,sourcefile,priorfile));m=json.loads((folder/'manifest.json').read_text());lang=m['language']
 c.require(lang in PRIOR_SHA and file_sha(sourcefile)==SOURCE_SHA and file_sha(priorfile)==PRIOR_SHA[lang],'Source or prior pin differs')
 if check_package:
  if (folder.parent/'PACKAGE-MANIFEST.json').exists():package_check(folder.parent)
  else:branch_check(folder.parent,lang)
 c.require(m['status']=='local-draft-awaiting-independent-review' and m['human_validation'] is False and m['runtime_approved'] is False and m['published'] is False and m['source_snapshot_sha256']==SOURCE_SHA and m['review_sha256']==REVIEW_SHA[lang],'Misleading manifest status or source')
 expectedfiles={'dictionary.json.gz','dictionary.csv.gz','delta-reviewed.json.gz','delta-reviewed.xml.gz'};c.require(set(m['files'])==expectedfiles,'Unexpected locale files')
 for name,info in m['files'].items():
  f=folder/name;c.require(f.is_file() and not f.is_symlink() and f.stat().st_size==info['bytes'] and file_sha(f)==info['sha256'],'Locale file changed')
 source=load(sourcefile);prior=load(priorfile);rows=load(folder/'dictionary.json.gz');delta=load(folder/'delta-reviewed.json.gz')
 src={r['id']:r for r in source};old={r['id']:r for r in prior};current={r['id']:r for r in rows};changes={r['id']:r for r in delta}
 c.require(len(src)==len(source)==len(current)==len(rows)==CURRENT and len(old)==len(prior) and len(changes)==len(delta)==DIFF['added']+DIFF['changed'],'Identity/count mismatch')
 for s in source:c.check_source(s)
 c.require(all(c.same_identity(old[k],src[k]) for k in set(old)&set(src)),'Public identity collision or rebind')
 added=set(src)-set(old);retired=set(old)-set(src);changed={k for k in set(old)&set(src) if not c.matches(old[k],src[k])}
 c.require((len(added),len(changed),len(retired))==(DIFF['added'],DIFF['changed'],DIFF['retired']) and set(changes)==added|changed,'Unexpected source delta')
 c.require([r['id'] for r in rows]==[s['id'] for s in source] and [r['id'] for r in delta]==[s['id'] for s in source if s['id'] in changes],'Output order changed')
 for s in source:
  k=s['id'];row=current[k];no_private(row)
  if k not in changes:c.require(row==old[k] and c.matches(row,s),'Prior source/target changed')
  else:
   c.require(row==changes[k] and c.matches(row,s) and row['source_english_sha256']==s['sourceTextSHA256'] and row['translation_alignment']=='whole_record' and isinstance(row['translation'],str) and row['translation'].strip(),'Changed source/target row')
   r=row['review'];c.require(r['kind']=='independent_ai_review' and r['original_review_sha256']==[REVIEW_SHA[lang]] and r['source_text_sha256']==s['sourceTextSHA256'] and r['target_sha256']==c.sha(row['translation'].encode()) and r['human_validation'] is False and r['runtime_approved'] is False and r['decision'] in ('accepted','corrected'),'New review binding mismatch')
 c.require(m['public_records']==CURRENT and m['source_identity_holds']==0 and m['delta_counts']==DIFF and m['reviewed_delta_records']==len(delta),'Manifest count mismatch')
 table=list(csv.reader(io.StringIO(gzip.decompress((folder/'dictionary.csv.gz').read_bytes()).decode())))
 c.require(len(table)==len(rows)+1,'CSV count mismatch')
 for cells,r in zip(table[1:],rows):c.require(cells==[r[k] for k in ('traditional','simplified','pinyin','translation')]+[r['review']['kind'],r['source_url'],r['source_license']],'CSV differs')
 xml=ET.fromstring(gzip.decompress((folder/'delta-reviewed.xml.gz').read_bytes()));c.require(len(xml)==len(delta),'XML count mismatch')
 for node,r in zip(xml,delta):c.require(all(node.findtext(tag)==r[key] for tag,key in [('candidate_id','id'),('trad','traditional'),('simp','simplified'),('py','pinyin')]) and node.find('trans')[0].text==r['translation'],'XML differs')
 return {'status':'public-structural-and-source-check-passed; private-review-replay-and-independent-projection-review-separate','locale':lang,'records':len(rows),'directNewSourceReviews':len(delta),'runtimeApproved':False,'published':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--source',type=Path,required=True);p.add_argument('--prior',type=Path,required=True);a=p.parse_args();print(json.dumps(validate(a.folder,a.source,a.prior),ensure_ascii=False,sort_keys=True))
