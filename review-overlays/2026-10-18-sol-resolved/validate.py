#!/usr/bin/env python3
"""Replay separate public corpus and app-baseline overlays without certifying accuracy."""
from pathlib import Path
import argparse, collections, gzip, hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True

SOURCE='166a286a68f278b73c3307284dbee879451c262608b1cbe0f8e9d6eca2d4474b'
BASE='45ea5427ba048b1377a59f7a1a069b6edcd14af253c453dc9f511218f795a0a5'


def need(value,reason):
    if not value: raise ValueError(reason)


def sha(data): return hashlib.sha256(data).hexdigest()
def canonical(value): return sha(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
def load(path):
    data=path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix=='.gz' else data)
def texts(record): return [s['final_ukrainian'] for s in record['segments']]


def check_reviewer_separation(kind, first, rounds):
    for index, item in enumerate(rounds):
        if kind == 'corpus':
            need(item['reviewerKey'] != first['reviewerKey'],
                'Corpus follow-up reused the original reviewer')
        previous = rounds[index - 1] if index else first
        if previous is not None and previous['model'] == 'gpt-6.1-sol':
            need(item['reviewerKey'] != previous['reviewerKey'],
                'Separate Sol validation reused the proposer')


def check_final_confirmation(kind, first, rounds, eligible):
    need(rounds, 'Missing final Sol rounds')
    final = rounds[-1]['decision']
    if eligible(final):
        if len(rounds) == 1:
            need(kind == 'corpus' and first is not None and eligible(first['decision'])
                and texts(first['decision']) == texts(final),
                'New or held-resolved final text lacks separate Sol validation')
        else:
            previous = rounds[-2]['decision']
            need(eligible(previous) and texts(previous) == texts(final),
                'Newly qualified or changed final text lacks subsequent unchanged qualified Sol validation')


def check_coverage(coverage):
    expected_fields={'totalAppBaselineEntries','originalCorpusRecords','qualifiedRuntimeEntries',
        'unmappedRuntimeEntries','unmappedRuntimeReasonCounts','unresolvedOriginalSourceRecords',
        'sourceWithoutStrictAppCounterpart','hskCatalogSHA256','hskWordListIndexSHA256','hskLevels',
        'commonHSKLists','hskCoverageScope','hskMembershipMetadataIncluded',
        'preferredReadingCoverageClaimed','privateIndependentCoverageAuditSHA256','scope'}
    need(set(coverage)==expected_fields,'Unknown public coverage metadata is not qualified')
    for key in ['totalAppBaselineEntries','originalCorpusRecords','qualifiedRuntimeEntries',
            'unmappedRuntimeEntries','unresolvedOriginalSourceRecords','sourceWithoutStrictAppCounterpart']:
        need(type(coverage[key]) is int and coverage[key]>=0,'Runtime coverage counts must be nonnegative integers')
    reasons=coverage['unmappedRuntimeReasonCounts']
    need(isinstance(reasons,dict) and all(isinstance(key,str) and key.strip()
        and type(value) is int and value>=0 for key,value in reasons.items())
        and sum(reasons.values())==coverage['unmappedRuntimeEntries'],
        'Unmapped runtime reason totals differ')
    need(coverage['totalAppBaselineEntries']==124725
        and coverage['qualifiedRuntimeEntries']+coverage['unmappedRuntimeEntries']==124725
        and coverage['originalCorpusRecords']==125264 and coverage['sourceWithoutStrictAppCounterpart']==2297,
        'Runtime and original-source universes were conflated')
    need(coverage['hskCoverageScope']=='aggregate_counts_only'
        and coverage['hskMembershipMetadataIncluded'] is False
        and coverage['preferredReadingCoverageClaimed'] is False,
        'Public HSK scope must exclude membership and preferred-reading claims')
    expected={'hsk-1':150,'hsk-2':149,'hsk-3':298,'hsk-4':600,'hsk-5':1299,'hsk-6':2500,
        'hsk30-1':506,'hsk30-2':770,'hsk30-3':970,'hsk30-4':995,'hsk30-5':1069,
        'hsk30-6':1139,'hsk30-7-9':5620}
    fields={'listID','uniqueTerms','termsWithAnyQualifiedReading',
        'termsWithAllMatchedReadingsQualified','termsWithoutBaselineEntry'}
    levels=coverage['hskLevels']
    need(len(levels)==13 and {row['listID'] for row in levels}==set(expected),
        'Missing bundled HSK level aggregate')
    for level in levels:
        need(set(level)==fields,'Per-term membership or unknown HSK metadata must stay outside the public projection')
        need(all(type(level[key]) is int and level[key]>=0 for key in fields-{'listID'}),
            'HSK aggregate counts must be nonnegative integers')
        need(level['uniqueTerms']==expected[level['listID']]
            and level['termsWithAllMatchedReadingsQualified']<=level['termsWithAnyQualifiedReading']
            <=level['uniqueTerms']-level['termsWithoutBaselineEntry'],
            'HSK aggregate coverage arithmetic differs')
    need(coverage['commonHSKLists']==['hsk-1','hsk-2','hsk-3','hsk30-1','hsk30-2','hsk30-3'],
        'Common HSK aggregate scope changed')
    for key in ['hskCatalogSHA256','hskWordListIndexSHA256','privateIndependentCoverageAuditSHA256']:
        pin=coverage[key]
        need(isinstance(pin,str) and len(pin)==64 and all(c in '0123456789abcdef' for c in pin),
            'Missing exact private coverage/catalog hash reference')


def check_decision(raw,decision):
    rid=raw['id']
    need(decision['entry_id']==rid and decision['source_record_sha256']==canonical(raw),'Source record binding differs')
    need(all(decision[k]==raw[k] for k in ['traditional','simplified','pinyin']),'Source identity differs')
    need(decision['original_uncertainty_flags']==raw['uncertainty_flags']
        and decision['original_uncertainty_notes']==raw['uncertainty_notes'],'Original source flags or notes differ')
    need(decision['record_disposition'] in ['accept','correct','quarantine'],'Unknown disposition')
    need(len(decision['segments'])==len(raw['english_segments'])==len(raw['ukrainian_segments']),'Missing source segment')
    for i,segment in enumerate(decision['segments']):
        en,uk=raw['english_segments'][i],raw['ukrainian_segments'][i]
        expected=canonical({'entry_id':rid,'segment_index':i,'english':en,'ukrainian':uk})
        need(segment['segment_id']==rid+':'+str(i) and segment['segment_index']==i
            and segment['source_segment_sha256']==expected and segment['original_ukrainian']==uk
            and segment.get('english',en)==en,'Source segment binding differs')
        need(segment['decision'] in ['accept','correct','quarantine']
            and isinstance(segment['final_ukrainian'],str) and segment['final_ukrainian'].strip()
            and segment['rationale'].strip(),'Empty or unknown authored segment')
        need((segment['final_ukrainian']!=uk)==(segment['decision']=='correct'),'Correction invariant differs')


def validate(directory,source_path):
    root=directory.resolve()
    manifest=load(root/'manifest.json')
    need(manifest['purpose']=='SEPARATE_SOL_RESOLVED_CORPUS_AND_APP_BASELINE_OVERLAYS'
        and manifest['sourceDictionarySHA256']==SOURCE and manifest['appBaselineDictionarySHA256']==BASE,
        'Unexpected source universes')
    need(all(manifest[k] is False for k in ['humanValidation','linguisticAccuracyCertified','runtimeApproval','publicationApproval']),
        'Public data cannot approve itself or claim human accuracy validation')
    provenance=manifest['appBaselineSourceProvenance']
    need(provenance['dictionarySHA256']==BASE and provenance['license']==manifest['license']=='CC-BY-SA-4.0'
        and provenance['metadata']['license']=='CC BY-SA 4.0'
        and provenance['metadata']['source_url']=='https://cc-cedict.org/editor/editor.php?handler=Download'
        and provenance['licenseURL']=='https://creativecommons.org/licenses/by-sa/4.0/'
        and provenance['attribution'],'Baseline source licence or provenance differs')
    expected={'corpus/manifest.json','corpus/review-evidence.json.gz','corpus/translations.json.gz',
        'corpus/held-records.json.gz','corpus/validate.py','baseline-source-records.json.gz',
        'baseline-review-evidence.json.gz','baseline-translations.json.gz','baseline-held-records.json.gz',
        'resolution-lineage.json.gz','runtime-coverage.json','validate.py','README.md'}
    need(set(manifest['files'])==expected,'Unexpected public package inventory')
    for name,pin in manifest['files'].items():
        data=(root/name).read_bytes()
        need(sha(data)==pin['sha256'] and len(data)==pin['bytes'],'Public package bytes differ: '+name)
    spec=importlib.util.spec_from_file_location('preserved_corpus_validator',root/'corpus/validate.py')
    corpus_validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(corpus_validator)
    corpus_result=corpus_validator.validate(root/'corpus',source_path)
    need(corpus_result['completeSourceReview'] and corpus_result['reviewedRecords']==125264
        and corpus_result['reviewedSegments']==199737,'Incomplete original corpus coverage')
    raw_corpus={r['id']:r for r in load(source_path)}
    proof={r['decision']['entry_id']:r for r in load(root/'corpus/review-evidence.json.gz')}
    baseline_rows=load(root/'baseline-source-records.json.gz')
    baseline={r['id']:r for r in baseline_rows}
    need(len(baseline_rows)==len(baseline)==1758 and not set(baseline).intersection(raw_corpus),
        'Baseline rows are a separate fixed source universe')
    for rid,raw in baseline.items():
        eid=raw['baseline_entry_id']
        need(raw['baseline_dictionary_sha256']==BASE and raw['source_kind']=='APP_ENGLISH_BASELINE'
            and isinstance(eid,int) and eid>0,'Baseline source provenance differs')
        expected_id=sha(('app-baseline\t'+BASE+'\t'+str(eid)).encode())[:16]
        need(rid==expected_id and raw['english_segments']==raw['ukrainian_segments'],
            'Baseline compatibility field must retain the original English input')
        original=json.loads(raw['raw_source'])
        need(original=={'entryID':eid,'simplified':raw['simplified'],'traditional':raw['traditional'],
            'reading':raw['pinyin'],'english':'\n'.join(raw['english_segments'])},'Baseline source meaning differs')
    baseline_proof_rows=load(root/'baseline-review-evidence.json.gz')
    baseline_proof={r['decision']['entry_id']:r for r in baseline_proof_rows}
    need(len(baseline_proof_rows)==len(baseline_proof)==1758 and set(baseline_proof)==set(baseline),
        'Baseline review coverage differs')
    translated=[];held=[]
    for rid,item in sorted(baseline_proof.items()):
        raw=baseline[rid];decision=item['decision'];check_decision(raw,decision)
        need(item['model']=='gpt-6.1-sol','Unexpected baseline reviewer model')
        if corpus_validator.eligible(decision):
            need({f['flag'] for f in decision['flag_resolutions']}==set(raw['uncertainty_flags']),
                'Missing original baseline flag resolution')
            translated.append({'id':rid,'entryID':raw['baseline_entry_id'],'traditional':raw['traditional'],
                'simplified':raw['simplified'],'reading':raw['pinyin'],'english_segments':raw['english_segments'],
                'ukrainian_segments':texts(decision),'sourceKind':'app_english_baseline',
                'sourceDictionarySHA256':BASE,'sourceRecordSHA256':canonical(raw),
                'sourceReviewSHA256':item['sourceReviewSHA256'],'reviewerModel':item['model']})
        else:
            held.append({'id':rid,'entryID':raw['baseline_entry_id'],'reasons':decision['unresolved_reasons'],
                'sourceReviewSHA256':item['sourceReviewSHA256']})
    need(translated==load(root/'baseline-translations.json.gz') and held==load(root/'baseline-held-records.json.gz'),
        'Baseline eligible/held projection differs from authored final decisions')
    lineage=load(root/'resolution-lineage.json.gz')
    need(len(lineage)==10049 and len({r['id'] for r in lineage})==10049,'Resolution targets differ')
    counts=collections.Counter()
    for row in lineage:
        rid=row['id'];kind=row['origin'];counts[kind]+=1
        need(kind in ['corpus','app_english_baseline'],'Unknown lineage source origin')
        raw=raw_corpus[rid] if kind=='corpus' else baseline[rid]
        need(row['sourceRecordSHA256']==canonical(raw) and row['rounds'],'Missing original source or Sol follow-up')
        first=row['firstPass']
        if kind=='corpus':
            need(first is not None and first['model'] in ['gpt-6-astra','gpt-6.1-sol'],'Missing actual first-pass model')
            check_decision(raw,first['decision'])
        else:need(first is None,'Baseline additions cannot borrow original corpus review coverage')
        for i,item in enumerate(row['rounds']):
            need(item['model']=='gpt-6.1-sol' and len(item['sourceReviewSHA256'])==64 and item['reviewerKey'],
                'Missing Sol review provenance')
            check_decision(raw,item['decision'])
        check_reviewer_separation(kind,first,row['rounds'])
        final=row['rounds'][-1]
        projected=proof[rid] if kind=='corpus' else baseline_proof[rid]
        need(final['decision']==projected['decision'] and final['sourceReviewSHA256']==projected['sourceReviewSHA256'],
            'Public final text is not the latest accepted Sol decision')
        issues=row['reportedIssues']
        need(len({issue['issueID'] for issue in issues})==len(issues)
            and all(issue['sourceRecordSHA256']==canonical(raw) for issue in issues),'Reported issue source binding differs')
        issue_results=final['reportedIssueResolutions']
        by_issue={item['issue_id']:item for item in issue_results}
        need(len(by_issue)==len(issue_results) and set(by_issue)=={issue['issueID'] for issue in issues},
            'Reported source issue adjudication does not close')
        for item in issue_results:
            need(item['decision'] in ['resolved','unresolved'] and item['reason'].strip(),'Missing explicit issue judgment')
            if item['decision']=='unresolved':
                need(final['decision']['record_disposition']=='quarantine','Unresolved source issue entered qualified overlay')
        check_final_confirmation(kind,first,row['rounds'],corpus_validator.eligible)
    need(counts=={'corpus':8291,'app_english_baseline':1758},'Correction/held/mapping target accounting differs')
    need(manifest['corpusReviewedRecords']==125264 and manifest['corpusReviewedSegments']==199737
        and manifest['baselineReviewedRecords']==1758 and manifest['baselineEligibleRecords']==len(translated)
        and manifest['baselineHeldRecords']==len(held),'Separate source-universe totals differ')
    coverage=load(root/'runtime-coverage.json')
    check_coverage(coverage)
    return {'status':'PUBLIC_RESOLVED_CORPUS_AND_BASELINE_REPLAY_PASS',
        'corpus':corpus_result,'baselineReviewedRecords':1758,'baselineEligibleRecords':len(translated),
        'baselineHeldRecords':len(held),'resolutionTargets':10049,'humanValidation':False,
        'linguisticAccuracyCertified':False,'runtimeApproval':False,'publicationApproval':False,
        'hskCoverageScope':'aggregate_counts_only','privateMembershipReplayPerformed':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--source',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(validate(args.directory,args.source),ensure_ascii=False,indent=2))
