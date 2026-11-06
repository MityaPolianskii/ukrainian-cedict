#!/usr/bin/env python3
"""Standalone structural/source validator; does not certify private AI evidence."""
import argparse,csv,gzip,hashlib,io,json,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

SOURCE_SHA='2b2b3813f0918a9b7b35f58cbefec244662cefec291d89de86a0b5ef6aa1cb90'
PRIOR_SHA={'fr':'0dcfca0d27c0d71cb9586af4f3c891291218533c36676ea63cdf7b3c172ed71b',
           'uk':'338276895ae2557062dac519545516d073fd36db77b0f64217b0a32f7d8f8f54'}
UK_SHA='0d5b24e314b3061c86f58e20e75ba7bd3402d7468a0f4eabf979e52eeb503107'
SOURCE_COUNT=125324
PROPOSAL_COUNT=1773
HELD_REVIEW={'fr':(23,'67d9a7b929739ea1253149a5e658e07fd6fd3e5195924148847776c55e954f60'),
             'uk':(2,'4fe0103f21712db4759571b7f974375fd062bcbba9b30732a22b62e786c4f513')}
FORBIDDEN={'entryID','entry_id','appRowID','appID','baselineEntryID','popularity','HSK','userData','sourceFilePath'}
def require(value,message):
    if not value:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def check_package_if_present(root):
    path=root/'PACKAGE-MANIFEST.json'
    if not path.exists():return
    require(path.is_file() and not path.is_symlink(),'Invalid package manifest')
    manifest=json.loads(path.read_text())
    require(manifest['schemaVersion']==1 and manifest['status']=='local-draft-awaiting-independent-projection-review','Invalid package status')
    allowed={'ATTRIBUTION.md','README.md','source-records.json.gz','summary.json','validate_public_projection.py'}
    allowed|={f'{lang}/{name}' for lang in ('fr','uk') for name in ('manifest.json','dictionary.json.gz','dictionary.csv.gz','reviewed-additions.json.gz','current-source-proposals.json.gz','current-source-proposals.xml.gz')}
    require(set(manifest['files'])==allowed,'Unexpected public package contents')
    actual={}
    for item in sorted(root.rglob('*')):
        require(not item.is_symlink(),'Unexpected package symlink')
        if item.is_dir():require(item.relative_to(root).as_posix() in ('fr','uk'),'Unexpected package directory')
        if item.is_file() and item!=path:
            actual[item.relative_to(root).as_posix()]={'bytes':item.stat().st_size,'sha256':file_sha(item)}
    require(actual==manifest['files'],'Package files changed')
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')
def load(path):
    with gzip.open(path,'rt',encoding='utf8') as f:return json.load(f)
def no_private(value):
    if isinstance(value,dict):
        require(not (set(value)&FORBIDDEN),'Private application field in public output')
        for item in value.values():no_private(item)
    elif isinstance(value,list):
        for item in value:no_private(item)
def check_source(row,source):
    require(all(row[k]==source[k] for k in ('id','traditional','simplified','pinyin')),'Changed public identity')
    require(sha('\t'.join(source[k] for k in ('traditional','simplified','pinyin')).encode())[:16]==source['id'],'Invalid identity hash')
    require(row['source_english_segments']==source['english_segments'],'Changed English segments')
    require(row['translation_alignment']=='whole_record' and isinstance(row['translation'],str) and row['translation'].strip(),'Missing whole-record target')
    require(row['license']=='CC-BY-SA-4.0' and row['source_url'].startswith('https://'),'Missing attribution')
    review=row['review'];require(review['human_validation'] is False and review['runtime_approved'] is False and
        review['target_sha256']==sha(row['translation'].encode()),'Target or review claim mismatch')
    if review['kind']=='independent_ai_review':
        require(review['decision'] in ('accepted','corrected','neutral') and
                row['source_english_sha256']==review['source_text_sha256']==sha('\n'.join(source['english_segments']).encode()) and
                review['original_review_sha256'] and all(isinstance(x,str) and len(x)==64 for x in review['original_review_sha256']),
                'Independent review source/target binding mismatch')
    elif review['kind']=='retained_cfdict_source':
        require(review['fresh_ai_review'] is False,'CFDICT falsely relabelled')
    else:
        require(review['kind']=='retained_ukrainian_public_source' and review['fresh_ai_review'] is False,'Unknown retained source')
    no_private(row)

def validate(folder,source_file,prior_file,uk_qualified=None):
    folder,source_file,prior_file=map(Path,(folder,source_file,prior_file));manifest=json.loads((folder/'manifest.json').read_text())
    check_package_if_present(folder.parent)
    lang=manifest['language'];require(lang in PRIOR_SHA and file_sha(source_file)==SOURCE_SHA and
        file_sha(prior_file)==PRIOR_SHA[lang] and manifest['source_snapshot_sha256']==SOURCE_SHA,'Wrong pinned source or previous projection')
    require(manifest['status']=='draft-awaiting-independent-projection-review' and manifest['human_validation'] is False and
        manifest['runtime_approved'] is False and manifest['published'] is False,'Incorrect status')
    expected_files={'dictionary.json.gz','dictionary.csv.gz','reviewed-additions.json.gz','current-source-proposals.json.gz','current-source-proposals.xml.gz'}
    require(set(manifest['files'])==expected_files,'Unexpected projection files')
    for name,info in manifest['files'].items():
        path=folder/name;require(Path(name).name==name and path.is_file() and not path.is_symlink() and
            path.stat().st_size==info['bytes'] and file_sha(path)==info['sha256'],'Changed file '+name)
    source_list=load(source_file);sources={r['id']:r for r in source_list}
    require(len(source_list)==len(sources)==SOURCE_COUNT,'Wrong source count')
    prior_rows=load(prior_file);prior={r['id']:r for r in prior_rows};require(len(prior)==len(prior_rows),'Duplicate previous identity')
    qualified={}
    if lang=='uk':
        require(uk_qualified is not None and file_sha(uk_qualified)==UK_SHA,'Wrong UK qualified source')
        old=load(uk_qualified);qualified={r['id']:r for r in old};require(len(old)==len(qualified)==122291,'Wrong UK qualified count')
    rows=load(folder/'dictionary.json.gz');proposals=load(folder/'current-source-proposals.json.gz');direct={r['id']:r for r in proposals}
    extra,review_sha=HELD_REVIEW[lang]
    require(manifest.get('additional_held_source_reviews')==extra and manifest.get('held_review_sha256')==review_sha,
            'Held review binding mismatch')
    require(len(rows)==manifest['public_records'] and len(proposals)==len(direct)==PROPOSAL_COUNT+extra,'Wrong row/proposal count')
    require(sum(review_sha in r['review'].get('original_review_sha256',[]) for r in proposals)==extra,
            'Wrong number of held-source review proposals')
    seen=set();counts=Counter();ai=[]
    for row in rows:
        key=row['id'];require(key not in seen and key in sources,'Duplicate/unknown projection identity');seen.add(key);source=sources[key];check_source(row,source)
        kind=row['review']['kind'];counts[kind]+=1
        if kind=='independent_ai_review':ai.append(row)
        if key in prior and row==prior[key]:continue
        if kind=='retained_ukrainian_public_source':
            old=qualified.get(key);require(old is not None and all(old.get(k)==source[k] for k in ('id','traditional','simplified','pinyin','english_segments')),
                'Unmatched old UK identity/source')
            require(row['translation']=='\n'.join(old['ukrainian_segments']) and row['review']['prior_record_sha256']==sha(canonical(old)) and
                row['review']['qualification']==old['qualification'] and row['review']['prior_source_review_sha256']==old.get('prior_source_review_sha256') and
                row['review']['independent_review_sha256']==old.get('independent_review_sha256') and row['review']['candidate_sha256']==old.get('candidate_sha256'),
                'Changed retained UK target/evidence')
            continue
        candidate=direct.get(key);require(candidate is not None,'New projection row lacks direct current-source review')
        trimmed={k:v for k,v in candidate.items() if k not in ('proposal_kind','prior_target_sha256')}
        require(row==trimmed,'New projection target differs from reviewed proposal')
    require(dict(sorted(counts.items()))==manifest['review_kind_counts'] and len(rows)+manifest['source_identity_holds']==len(sources),'Coverage/count mismatch')
    require(ai==load(folder/'reviewed-additions.json.gz'),'Reviewed additions differ')
    for r in proposals:
        require(r['id'] in sources and r['proposal_kind'] in ('new_or_source_updated','already_identical','alternative_to_preserved_public_target'),'Invalid current proposal')
        check_source(r,sources[r['id']]);require(r['review']['kind']=='independent_ai_review','Proposal lacks independent review')
    table=list(csv.reader(io.StringIO(gzip.decompress((folder/'dictionary.csv.gz').read_bytes()).decode())))
    require(len(table)==len(rows)+1,'CSV count mismatch')
    for cells,r in zip(table[1:],rows):
        require(cells==[r[k] for k in ('traditional','simplified','pinyin','translation')]+[r['review']['kind'],r['source_url'],r['source_license']],'CSV differs')
    xml=ET.fromstring(gzip.decompress((folder/'current-source-proposals.xml.gz').read_bytes()));require(len(xml)==len(proposals),'XML count mismatch')
    for node,r in zip(xml,proposals):
        require(all(node.findtext(tag)==r[key] for tag,key in [('candidate_id','id'),('trad','traditional'),('simp','simplified'),('py','pinyin')]) and
                node.find('trans')[0].text==r['translation'],'XML differs')
    return {'status':'structural-and-public-source-validation-passed; private review replay and independent projection review remain separate',
            'language':lang,'records':len(rows),'proposals':len(proposals),'held':manifest['source_identity_holds'],'human_validation':False,'published':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--source',required=True,type=Path);p.add_argument('--prior',required=True,type=Path);p.add_argument('--uk-qualified',type=Path);a=p.parse_args()
    print(json.dumps(validate(a.folder,a.source,a.prior,a.uk_qualified),ensure_ascii=False,sort_keys=True))
