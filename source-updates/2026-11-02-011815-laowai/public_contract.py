#!/usr/bin/env python3
"""Public source/whole-record projection rules; no application or ledger IDs."""
import hashlib,json
from collections import Counter

def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def require(value,message):
 if not value:raise ValueError(message)
def text_sha(parts):return sha('\n'.join(parts).encode())
def check_source(s):
 require(set(s)=={'id','identitySHA256','traditional','simplified','pinyin','english_segments','sourceTextSHA256'},'Unexpected public source fields')
 ident=sha('\t'.join(s[k] for k in ('traditional','simplified','pinyin')).encode())
 require(s['identitySHA256']==ident and s['id']==ident[:16] and s['sourceTextSHA256']==text_sha(s['english_segments']) and bool(s['english_segments']),'Source identity or meaning mismatch')
def matches(old,s):
 return all(old.get(k)==s[k] for k in ('id','traditional','simplified','pinyin')) and old.get('source_english_segments')==s['english_segments']
def same_identity(old,s):
 return all(old.get(k)==s[k] for k in ('id','traditional','simplified','pinyin'))
def reviewed_record(s,review,review_sha):
 for k in ('id','identitySHA256','traditional','simplified','pinyin','english_segments','sourceTextSHA256'):require(review[k]==s[k],'Review source mismatch')
 require(review['sourceRecordSHA256']==sha(canonical(s)),'Review source-record hash mismatch')
 target=review['finalTarget'];require(isinstance(target,str) and target.strip() and review['finalTargetSHA256']==sha(target.encode()) and target=='\n'.join(review['translationSegments']),'Review target mismatch')
 require(review['decision'] in ('accepted','corrected') and review['humanValidation'] is False and review['approvedForApplication'] is False,'Review is not eligible')
 result={'id':s['id'],'traditional':s['traditional'],'simplified':s['simplified'],'pinyin':s['pinyin'],'source_english_segments':s['english_segments'],
  'source_english_sha256':s['sourceTextSHA256'],'translation':target,'translation_alignment':'whole_record','origin':'CC-CEDICT translation',
  'source_license':'CC BY-SA 4.0','source_url':'https://www.mdbg.net/chinese/dictionary?page=cc-cedict','license':'CC-BY-SA-4.0',
  'review':{'kind':'independent_ai_review','model':'gpt-6.1-terra (self-reported), xhigh','human_validation':False,'runtime_approved':False,
            'decision':review['decision'],'source_text_sha256':s['sourceTextSHA256'],'target_sha256':sha(target.encode()),'original_review_sha256':[review_sha],
            'reason':'Different-agent AI review compared the complete source and target; the exact review artifact digest is recorded.'}}
 notes=review.get('sourceUncertaintyNotes',[]);disposition=review.get('sourceIssueDisposition')
 if notes or disposition not in (None,'none'):
  reason=review.get('sourceIssueReason') or review.get('reason');qualification=review.get('sourceQualification')
  require(disposition in ('resolved-no-defect','qualified') and isinstance(reason,str) and reason.strip(),'Unresolved source uncertainty')
  require(disposition!='qualified' or isinstance(qualification,str) and qualification.strip() and qualification in target,'Missing visible source qualification')
  result['review']['source_issue_disposition']=disposition;result['review']['source_issue_reason']=reason
  result['review']['source_qualification']=qualification;result['review']['uncertainty_notes_sha256']=review['uncertaintyNotesSHA256']
 return result
def project(prior,sources,reviews,review_sha,expected):
 old={r['id']:r for r in prior};cur={r['id']:r for r in sources};peer={r['id']:r for r in reviews}
 require(len(old)==len(prior) and len(cur)==len(sources) and len(peer)==len(reviews),'Duplicate identity')
 for s in sources:check_source(s)
 require(all(same_identity(old[k],cur[k]) for k in set(old)&set(cur)),'Public identity collision or rebind')
 added=set(cur)-set(old);retired=set(old)-set(cur);changed={k for k in set(old)&set(cur) if not matches(old[k],cur[k])}
 require(len(added)==expected['added'] and len(retired)==expected['retired'] and len(changed)==expected['changed'],'Unexpected source delta')
 require(set(peer)==added|changed,'Reviewed delta does not exactly cover new and changed records')
 rows=[];delta=[]
 for s in sources:
  k=s['id']
  if k in peer:
   r=reviewed_record(s,peer[k],review_sha);delta.append(r)
  else:
   require(k in old and matches(old[k],s),'Missing preserved source');r=old[k]
  rows.append(r)
 require(len(rows)==len(sources) and len(delta)==len(peer),'Incomplete projection')
 return rows,delta,{'sourceRecords':len(sources),'publicRecords':len(rows),'retained':len(old)-len(retired)-len(changed),
                    'added':len(added),'changed':len(changed),'retired':len(retired),'reviewedDelta':len(delta),
                    'reviewKindCounts':dict(sorted(Counter(r['review']['kind'] for r in rows).items()))},sorted(retired)
