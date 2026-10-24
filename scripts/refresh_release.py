#!/usr/bin/env python3
"""Build and replay the dated source refresh; never modify frozen release data.

Review inputs contain authored candidates and exact-hash independent verdicts.
An accepted local source correction is published separately from the exact
upstream corpus. It does not silently change CC-CEDICT's source record.
"""
import argparse
import gzip
import hashlib
import json
import re
import shutil
from pathlib import Path

OLD_SOURCE_SHA='166a286a68f278b73c3307284dbee879451c262608b1cbe0f8e9d6eca2d4474b'
OLD_MANIFEST_SHA='1380bd6db28226931d5f1425586f45e66bf2965b5e6f9a79b228623e81dcc01a'
UPSTREAM_SHA='e6e14c761ebc1e66ae2ad7b08fc4c577d6927472bb059d70db6111f0c06abee9'
OLD_OVERLAY='review-overlays/2026-10-18-sol-resolved'
FIELDS=('traditional','simplified','pinyin','english_segments')
HUMAN_TEXT_HASHES={
    '88460eaa009e3b08':'d3d8dbddf05edda513973b151546e036aae09f413aa86cafccff203cbdf9b22d',
    '0ec5685dabd46cdb':'ee5b4269673aab0d29a9c56b436f8c389fd5b1ee6a64bf4d34e0a4e9ffce81b9',
    '0e1760cc4cbdc5f1':'6ee6e439cb976ce8320851ba5fb762a0bb3df0e1893c2d3df9245f3207855226'}
HUMAN_FIELDS={'entry_id','source','ukrainian_segments','displayed_translation_sha256','decision','scope',
              'chinese_language_validation','reviewer','reviewed_on','evidence'}
BUNDLE_FIELDS={'schema_version','upstream_admissions','upstream_revision_history','held_judgments',
               'revision_candidates','revision_reviews','revision_history','superseded_revision_candidates',
               'superseded_review_verdicts','verdict_revision_history','human_reviews','review_scope'}
REVIEW_SCOPE='Separate model agents, not human or independently attested backend identities.'
MANIFEST_METADATA=dict(schema_version=1,date='2026-10-25',upstream_release='2026-10-23T23:15:44Z',
    source_dictionary_sha256=OLD_SOURCE_SHA,prior_overlay_manifest_sha256=OLD_MANIFEST_SHA,upstream_gzip_sha256=UPSTREAM_SHA,
    human_validation_scope='three gloss approvals; no Chinese validation',linguistic_accuracy_certified=False,
    runtime_approved=False,license='CC-BY-SA-4.0',
    attribution='CC-CEDICT contributors, MDBG and CEDICT founder Paul Andrew Denisowski; Ukrainian adaptations by project contributors.')
RELEASE_FILES={'upstream.txt.gz','review-bundle.json.gz','source-records.json.gz','source-diff.json',
               'translations.json.gz','held-records.json.gz','qualified-revisions.json.gz',
               'held-resolution-outcomes.json.gz','revision-identity-groups.json','human-validation.json'}

def require(ok,message):
    if not ok:raise ValueError(message)
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def digest(x):return hashlib.sha256(canonical(x)).hexdigest()
def filehash(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()
def read(p):
    if p.suffix=='.gz':
        with gzip.open(p,'rt',encoding='utf-8') as f:return json.load(f)
    return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):
    data=canonical(x)+b'\n'
    if p.suffix=='.gz':data=gzip.compress(data,compresslevel=9,mtime=0)
    p.write_bytes(data)
def semantic(x):return {k:x[k] for k in FIELDS}
def identity(x):return hashlib.sha256('\t'.join(x[k] for k in FIELDS[:3]).encode()).hexdigest()[:16]
def references(text):
    # Version1 contains two legacy references with spaced "lu : 4". Treat
    # colon whitespace as formatting only; retain exact graphs and tone digits.
    return [re.sub(r'\s*:\s*',':',x) for x in re.findall(r'[〇\u3400-\u9fff\U00020000-\U000323af]+(?:\|[〇\u3400-\u9fff\U00020000-\U000323af]+)?\[[^\]]+\]',text)]

def parse_source(path):
    require(filehash(path)==UPSTREAM_SHA,'Unrecognized upstream source bytes')
    records=[];header={}
    with gzip.open(path,'rt',encoding='utf-8-sig') as f:
        for n,line in enumerate(f,1):
            line=line.rstrip('\r\n')
            if line.startswith('#! '):
                k,_,v=line[3:].partition('=');header[k]=v
            if not line or line.startswith('#'):continue
            m=re.fullmatch(r'(\S+) (\S+) \[([^\]]+)\] /(.*)/',line)
            require(m is not None,'Malformed source line '+str(n))
            t,s,p,en=m.groups();x=dict(traditional=t,simplified=s,pinyin=p,english_segments=en.split('/'),raw_source=line,source_line=n)
            x['id']=identity(x);records.append(x)
    require(len(records)==125314==int(header['entries']),'Upstream entry count differs')
    require(header['date']=='2026-10-23T23:15:44Z','Upstream date differs')
    require(len({x['id'] for x in records})==len(records),'Duplicate source identity')
    return records,header

def source_diff(old,new):
    a={x['id']:x for x in old};b={x['id']:x for x in new}
    added=sorted(b.keys()-a.keys());removed=sorted(a.keys()-b.keys())
    changed=sorted(k for k in a.keys()&b.keys() if a[k]['english_segments']!=b[k]['english_segments'])
    unchanged=sorted(k for k in a.keys()&b.keys() if a[k]['english_segments']==b[k]['english_segments'])
    return dict(old_records=len(a),new_records=len(b),added=added,removed=removed,
                changed_english=changed,unchanged_english=unchanged)

def translation_check(source,uk):
    require(isinstance(uk,list) and len(uk)==len(source['english_segments']),'Unaligned Ukrainian segments')
    for en,u in zip(source['english_segments'],uk):
        require(isinstance(u,str) and bool(u.strip()),'Empty Ukrainian segment')
        require(set(references(en))<=set(references(u)),'Lost or changed Chinese/pinyin reference')

def candidate_check(c,review):
    author=c.get('author_key',c.get('reviewer_key'))
    require(isinstance(author,str) and bool(author.strip()),'Missing candidate author identity')
    require(isinstance(review.get('reviewer_key'),str) and bool(review['reviewer_key'].strip()),'Missing independent reviewer identity')
    require(review['candidate_sha256']==digest(c),'Verdict is not bound to exact candidate')
    require(review['decision']=='accept','Unaccepted candidate admission')
    require(review['reviewer_key']!=author,'Self-reviewed candidate admission')
    require(c['human_validation'] is False and c['runtime_approved'] is False,'Unsupported candidate approval claim')
    require(review['human_validation'] is False,'Model verdict labelled human')
    require(review.get('runtime_approved',False) is False,'Model verdict claims runtime approval')
    require(bool(review.get('rationale') or review.get('segment_assessments')),'Empty independent assessment')

def human_check(humans,source,qualified):
    ids=set()
    for h in humans:
        require(set(h)==HUMAN_FIELDS,'Unexpected human review fields')
        k=h['entry_id'];require(k in HUMAN_TEXT_HASHES and k in qualified and k not in ids,'Invalid human review identity');ids.add(k)
        require(h['scope']=='english_source_to_ukrainian_gloss' and h['chinese_language_validation'] is False,'Human scope differs')
        require(h['decision']=='approved' and h['source']==semantic(source[k]) and h['ukrainian_segments']==qualified[k]['ukrainian_segments'],'Human reviewed text changed')
        require(h['displayed_translation_sha256']==HUMAN_TEXT_HASHES[k]
                ==digest(dict(source=h['source'],ukrainian_segments=h['ukrainian_segments'])),'Human text hash differs')
        require(h['reviewer']=='project maintainer feedback' and h['reviewed_on']=='2026-10-25'
                and h['evidence']=='Explicit positive response to the displayed three-entry English-to-Ukrainian gloss review batch.',
                'Human evidence metadata differs')
    require(ids==set(HUMAN_TEXT_HASHES),'Human review batch is incomplete')
    return ids

def manifest_check(m):
    require(set(m)==set(MANIFEST_METADATA)|{'counts','files'},'Unexpected manifest fields')
    for key,value in MANIFEST_METADATA.items():
        require(type(m[key]) is type(value) and m[key]==value,'Manifest metadata differs: '+key)
    require(set(m['files'])==RELEASE_FILES,'Manifest artifact inventory differs')

def history_check(bundle,current_hashes):
    historical={digest(c):c for c in bundle['superseded_revision_candidates']}
    for item in bundle['revision_history']:
        h=digest(item['candidate']);historical[h]=item['candidate']
        require(item['independent_review']['candidate_sha256']==h,'Historical verdict binding differs')
        require(item['superseded_by'] in current_hashes,'Historical successor is not current')
    require(not current_hashes.intersection(historical),'Current candidate is also superseded')
    for r in bundle['superseded_review_verdicts']:
        require(r['candidate_sha256'] in historical,'Superseded verdict lacks exact candidate body')
        require(r['candidate_sha256'] not in current_hashes,'Current verdict is labelled superseded')
    verdict_hashes={digest(r):r for r in bundle['revision_reviews']+bundle['superseded_review_verdicts']
                    +[i['independent_review'] for i in bundle['revision_history']]}
    for item in bundle.get('verdict_revision_history',[]):
        h=item['candidate_sha256'];old=item['superseded_verdict'];successor=verdict_hashes.get(item['successor_verdict_sha256'])
        require(h in current_hashes or h in historical,'Revised verdict lacks candidate body')
        require(old['candidate_sha256']==h and successor is not None and successor['candidate_sha256']==h,
                'Revised verdict successor binding differs')

def compile_release(inputs,upstream_path,bundle):
    require(set(bundle)==BUNDLE_FIELDS and bundle['schema_version']==1,'Unexpected publication bundle fields')
    require(bundle['review_scope']==REVIEW_SCOPE,'Unsupported publication review scope')
    original=inputs/'dictionary.json';overlay=inputs/OLD_OVERLAY
    require(filehash(original)==OLD_SOURCE_SHA,'Original source binding differs')
    require(filehash(overlay/'manifest.json')==OLD_MANIFEST_SHA,'Prior overlay binding differs')
    manifest=read(overlay/'manifest.json')
    for name in ['corpus/translations.json.gz','corpus/held-records.json.gz','baseline-held-records.json.gz','baseline-source-records.json.gz']:
        require(filehash(overlay/name)==manifest['files'][name]['sha256'],'Prior overlay file differs: '+name)
    old=read(original);new,header=parse_source(upstream_path)
    a={x['id']:x for x in old};b={x['id']:x for x in new};delta=source_diff(old,new)
    old_qualified={x['id']:x for x in read(overlay/'corpus/translations.json.gz')}
    qualified={}
    for k in delta['unchanged_english']:
        if k not in old_qualified:continue
        x=old_qualified[k];require(semantic(a[k])==semantic(b[k]),'Carry-forward source differs')
        translation_check(b[k],x['ukrainian_segments'])
        qualified[k]=dict(semantic(b[k]),id=k,source_record_sha256=digest(b[k]),
                          ukrainian_segments=x['ukrainian_segments'],qualification='carried_forward_exact_source',
                          prior_source_review_sha256=x['source_review_sha256'],human_validation=False,runtime_approved=False)
    new_ids=set(delta['added']+delta['changed_english']);seen=set()
    for admission in bundle['upstream_admissions']:
        c=admission['candidate'];r=admission['independent_review'];candidate_check(c,r)
        k=c['entry_id'];require(k in new_ids and k not in seen,'Unexpected/duplicate new-source admission')
        require(c['source_record_sha256']==digest(b[k]),'New-source candidate binding differs')
        uk=c['final_ukrainian_segments'];translation_check(b[k],uk);seen.add(k)
        require(c['record_disposition']=='qualified' and not c['unresolved_reasons'],'Held upstream admission')
        qualified[k]=dict(semantic(b[k]),id=k,source_record_sha256=digest(b[k]),ukrainian_segments=uk,
                          qualification='new_independent_model_review',candidate_sha256=digest(c),
                          independent_review_sha256=digest(r),human_validation=False,runtime_approved=False)
    require(seen==new_ids,'New or changed upstream records are missing review')
    previous_holds={('original_corpus',x['id']):x for x in read(overlay/'corpus/held-records.json.gz')}
    previous_holds.update({('app_baseline',x['id']):x for x in read(overlay/'baseline-held-records.json.gz')})
    held_old=set(previous_holds)
    baseline_source={x['id']:x for x in read(overlay/'baseline-source-records.json.gz')}
    judgments={}
    for j in bundle['held_judgments']:
        key=(j['source_universe'],j['entry_id']);require(key in held_old and key not in judgments,'Unexpected held-review record')
        require(j['human_validation'] is False and j['runtime_approved'] is False,'Unsupported judgment claim')
        require(j['record_disposition'] in ('held','qualified'),'Invalid judgment disposition')
        require(bool(j['prior_hold_assessment']),'Missing hold assessment')
        require(j['prior_review_sha256']==previous_holds[key]['sourceReviewSHA256'],'Prior held review binding differs')
        source=a[key[1]] if key[0]=='original_corpus' else baseline_source[key[1]]
        require(j['source_record_sha256']==digest(source),'Held source binding differs')
        require(len(j['final_ukrainian_segments'])==len(source['english_segments']),'Held segment count differs')
        require([s['segment_index'] for s in j['segment_assessments']]==list(range(len(source['english_segments']))),'Incomplete segment assessment')
        require(all(bool(s['rationale']) for s in j['segment_assessments']),'Empty segment assessment')
        if j['record_disposition']=='qualified':
            require(not j['unresolved_reasons'] and all(s['disposition']!='hold' for s in j['segment_assessments'])
                    and not j.get('source_correction_proposal'),'Unsupported qualified judgment: '+j['entry_id'])
        else:require(bool(j['unresolved_reasons']),'Held judgment lacks reason')
        judgments[key]=j
    require(set(judgments)==held_old,'Held review does not cover all3326 records')
    reviews={x['candidate_sha256']:x for x in bundle['revision_reviews']}
    require(len(reviews)==len(bundle['revision_reviews']),'Duplicate current revision verdict')
    revisions=[];resolved=set();candidate_hashes=set()
    for c in bundle['revision_candidates']:
        ch=digest(c);require(ch not in candidate_hashes,'Duplicate revision candidate');candidate_hashes.add(ch)
        key=(c['parent_source_universe'],c['parent_entry_id']);require(key in held_old,'Revision parent is not held')
        require(c['parent_source_record_sha256']==judgments[key]['source_record_sha256'],'Revision parent binding differs')
        require(c['prior_review_sha256']==previous_holds[key]['sourceReviewSHA256'],'Revision prior review binding differs')
        if c.get('originating_judgment_sha256'):
            require(c['originating_judgment_sha256']==digest(judgments[key]),'Revision judgment binding differs')
        require(c['source_record_sha256']==digest(c['source']),'Revision source binding differs')
        require(c['revision_kind'] in ('frozen_source','upstream_replacement','source_correction'),'Unknown revision kind')
        parent_source=a[key[1]] if key[0]=='original_corpus' else baseline_source[key[1]]
        if c['revision_kind']=='upstream_replacement':
            require(c['source'].get('id') in b and c['source']==b[c['source']['id']],'Upstream replacement is not an exact imported record')
        elif c['revision_kind']=='frozen_source':
            require(semantic(c['source'])==semantic(parent_source),'Frozen-source candidate changed the source')
        elif c['revision_kind']=='source_correction':
            require(semantic(c['source'])!=semantic(parent_source),'Source correction changes no source field')
        translation_check(c['source'],c['ukrainian_segments'])
        r=reviews.get(ch)
        if not r or r['decision']!='accept':continue
        candidate_check(c,r)
        if c['revision_kind']=='source_correction':require(bool(c['evidence']),'Source correction lacks evidence')
        revisions.append(dict(candidate=c,independent_review=r));resolved.add(key)
        if key[0]=='original_corpus' and key[1] in b and semantic(c['source'])==semantic(b[key[1]]):
            k=key[1];qualified[k]=dict(semantic(b[k]),id=k,source_record_sha256=digest(b[k]),
                                     ukrainian_segments=c['ukrainian_segments'],qualification='resolved_held_record',
                                     candidate_sha256=ch,independent_review_sha256=digest(r),
                                     human_validation=False,runtime_approved=False)
    require(set(reviews)==candidate_hashes,'Missing or stale independent revision verdicts')
    history_check(bundle,candidate_hashes)
    identity_groups={}
    for item in revisions:
        c=item['candidate'];target=identity(c['source'])
        identity_groups.setdefault(target,[]).append(dict(candidate_sha256=digest(c),parent_entry_id=c['parent_entry_id'],
            parent_source_universe=c['parent_source_universe'],source_record_sha256=c['source_record_sha256']))
    groups=[dict(target_identity=k,candidates=v,multiple_candidates=len(v)>1,
                 policy='Separate proposals; no automatic alias, merge, overwrite or runtime admission.')
            for k,v in sorted(identity_groups.items())]
    outcomes=[]
    for key,j in sorted(judgments.items()):
        state='unresolved';by=[]
        if key in resolved:state='resolved_with_independently_reviewed_candidate'
        elif key[0]=='original_corpus' and key[1] in new_ids and key[1] in qualified:state='replaced_by_reviewed_upstream_revision'
        elif key[0]=='original_corpus' and key[1] not in b:state='retired_from_current_upstream'
        by=[digest(x['candidate']) for x in revisions if (x['candidate']['parent_source_universe'],x['candidate']['parent_entry_id'])==key]
        outcomes.append(dict(source_universe=key[0],entry_id=key[1],state=state,judgment_sha256=digest(j),candidate_sha256=by))
    held=[]
    for k in sorted(b.keys()-qualified.keys()):
        j=judgments.get(('original_corpus',k))
        reasons=list(j['unresolved_reasons']) if j else []
        reasons += [r.get('rationale','Independent review did not accept the proposed candidate')
                    for c in bundle['revision_candidates'] if c['parent_source_universe']=='original_corpus' and c['parent_entry_id']==k
                    for r in [reviews[digest(c)]] if r['decision']!='accept']
        if not reasons:reasons=['No accepted translation matching the exact current upstream source. Local source corrections are published separately.']
        held.append(dict(id=k,source_record_sha256=digest(b[k]),reason=reasons,
                         correction_candidate_available=('original_corpus',k) in resolved))
    humans=bundle['human_reviews'];human_ids=human_check(humans,b,qualified)
    counts=dict(upstream_records=len(b),upstream_segments=sum(len(x['english_segments']) for x in new),
                added_records=len(delta['added']),retired_records=len(delta['removed']),changed_english_records=len(delta['changed_english']),
                unchanged_english_records=len(delta['unchanged_english']),qualified_exact_upstream_records=len(qualified),
                held_exact_upstream_records=len(held),reviewed_new_or_changed_records=len(seen),
                held_original_records_reaudited=sum(k[0]=='original_corpus' for k in judgments),
                held_baseline_records_reaudited=sum(k[0]=='app_baseline' for k in judgments),
                qualified_revision_candidates=len(revisions),
                revision_target_identities=len(groups),overlapping_revision_target_identities=sum(x['multiple_candidates'] for x in groups),
                resolved_original_parents=sum(x['source_universe']=='original_corpus' and x['state']!='unresolved' for x in outcomes),
                retired_original_parents=sum(x['source_universe']=='original_corpus' and x['state']=='retired_from_current_upstream' for x in outcomes),
                upstream_replaced_original_parents=sum(x['source_universe']=='original_corpus' and x['state']=='replaced_by_reviewed_upstream_revision' for x in outcomes),
                unresolved_original_parents=sum(x['source_universe']=='original_corpus' and x['state']=='unresolved' for x in outcomes),
                resolved_baseline_parents=sum(x['source_universe']=='app_baseline' and x['state']!='unresolved' for x in outcomes),
                unresolved_baseline_parents=sum(x['source_universe']=='app_baseline' and x['state']=='unresolved' for x in outcomes),
                human_gloss_approved_records=len(human_ids),human_chinese_validated_records=0)
    return {'source-records.json.gz':new,'source-diff.json':delta,
            'translations.json.gz':[qualified[k] for k in sorted(qualified)],'held-records.json.gz':held,
            'qualified-revisions.json.gz':revisions,'held-resolution-outcomes.json.gz':outcomes,
            'revision-identity-groups.json':groups,
            'human-validation.json':humans},counts

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['build','validate']);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--release',type=Path);p.add_argument('--inputs',type=Path);p.add_argument('--bundle',type=Path);p.add_argument('--upstream',type=Path);args=p.parse_args()
    root=args.root.resolve();release=(args.release or root/'source-updates/2026-10-25').resolve();inputs=(args.inputs or root).resolve()
    if args.mode=='build':
        require(args.bundle is not None and args.upstream is not None,'Build needs bundle and upstream')
        bundle=read(args.bundle);products,counts=compile_release(inputs,args.upstream,bundle)
        release.mkdir(parents=True,exist_ok=True);shutil.copyfile(args.upstream,release/'upstream.txt.gz');write(release/'review-bundle.json.gz',bundle)
        for name,data in products.items():write(release/name,data)
        files={name:{'sha256':filehash(release/name),'bytes':(release/name).stat().st_size} for name in sorted(['upstream.txt.gz','review-bundle.json.gz']+list(products))}
        write(release/'manifest.json',dict(MANIFEST_METADATA,counts=counts,files=files))
    else:
        m=read(release/'manifest.json')
        manifest_check(m)
        for name,meta in m['files'].items():
            require(Path(name).name==name,'Unsafe manifest path');require(filehash(release/name)==meta['sha256'] and (release/name).stat().st_size==meta['bytes'],'Release file differs: '+name)
        products,counts=compile_release(inputs,release/'upstream.txt.gz',read(release/'review-bundle.json.gz'))
        require(counts==m['counts'],'Manifest counts differ')
        for name,data in products.items():require(read(release/name)==data,'Derived artifact differs: '+name)
    print(json.dumps({'status':'passed','mode':args.mode,'counts':counts},ensure_ascii=False))

if __name__=='__main__':main()
