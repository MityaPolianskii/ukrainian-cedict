#!/usr/bin/env python3
"""Validate a public record-level dictionary contribution without app resources."""
from pathlib import Path
import csv
import gzip
import hashlib
import io
import json
import sys
import xml.etree.ElementTree as ET

def require(value, message):
    if not value: raise ValueError(message)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def load(path): return json.loads(gzip.decompress(path.read_bytes()))

def validate(root, source_file):
    root, source_file = Path(root), Path(source_file)
    manifest = json.loads((root/'manifest.json').read_text())
    require(sha(source_file.read_bytes()) == manifest['source_snapshot_sha256'], 'Changed exact upstream source')
    sources = {r['id']:r for r in load(source_file)}
    for name, expected in manifest['files'].items():
        require(Path(name).name == name and not (root/name).is_symlink(), 'Unsafe data filename')
        raw = (root/name).read_bytes()
        require(len(raw)==expected['bytes'] and sha(raw)==expected['sha256'], 'Changed published file: '+name)
    rows = load(root/'dictionary.json.gz')
    require(len(rows)==manifest['public_records'], 'Wrong public record count')
    seen, ai, retained = set(), [], 0
    for r in rows:
        require(r['id'] not in seen and r['id'] in sources, 'Missing/duplicate exact public source')
        seen.add(r['id']); source=sources[r['id']]
        require(r['id']==sha('\t'.join(r[k] for k in ['traditional','simplified','pinyin']).encode())[:16], 'Changed identity')
        require(all(r[k]==source[k] for k in ['traditional','simplified','pinyin']), 'Changed Chinese or reading')
        require(r['source_english_segments']==source['english_segments'], 'Changed English source')
        require(r['translation_alignment']=='whole_record', 'Invented segment alignment')
        require(isinstance(r['translation'],str) and r['translation'].strip(), 'Empty target')
        require(r['license']=='CC-BY-SA-4.0' and r['source_url'].startswith('https://'), 'Missing source licence/reference')
        review=r['review']
        require(review['human_validation'] is False and review['runtime_approved'] is False, 'Unsupported approval claim')
        require(sha(r['translation'].encode())==review['target_sha256'], 'Target changed since review')
        if review['kind']=='independent_ai_review':
            require(review['decision'] in ['accepted','corrected','neutral'], 'Unresolved candidate')
            expected=sha('\n'.join(source['english_segments']).encode())
            require(review['source_text_sha256']==expected==r['source_english_sha256'], 'Review binds another source')
            require(review['original_review_sha256'] and all(len(x)==64 for x in review['original_review_sha256']), 'Missing review audit binding')
            ai.append(r)
        else:
            require(review['kind']=='retained_cfdict_source' and review['fresh_ai_review'] is False, 'Retained source relabelled as new review')
            retained += 1
        require(not any(k in r for k in ['entryID','appRowID','popularity','HSK','userData','sourceFilePath']), 'App field escaped projection')
    require(len(ai)==manifest['new_independent_ai_reviewed'] and retained==manifest['retained_cfdict'], 'Review counts differ')
    require(ai==load(root/'reviewed-additions.json.gz'), 'Additions differ from reviewed dictionary projection')
    xml=ET.fromstring(gzip.decompress((root/'reviewed-additions.xml.gz').read_bytes()))
    require(len(xml)==len(ai), 'XML count differs')
    for node,r in zip(xml,ai):
        require(all(node.findtext(tag)==r[key] for tag,key in [('candidate_id','id'),('trad','traditional'),('simp','simplified'),('py','pinyin')]), 'XML identity differs')
        require(list(node.find('trans'))[0].text==r['translation'], 'XML translation differs')
    table=list(csv.reader(io.StringIO(gzip.decompress((root/'dictionary.csv.gz').read_bytes()).decode())))
    require(len(table)==len(rows)+1, 'CSV count differs')
    for cells,r in zip(table[1:],rows):
        require(cells==[r[k] for k in ['traditional','simplified','pinyin','translation']]+[r['review']['kind'],r['source_url'],r['source_license']], 'CSV projection differs')
    return {'status':'passed','records':len(rows),'independent_ai_reviewed':len(ai),'retained_cfdict':retained,'human_validated_by_this_work':0}

if __name__=='__main__':
    root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'data'
    source=Path(sys.argv[2]) if len(sys.argv)>2 else Path(__file__).resolve().parents[1]/'sources/source-records.json.gz'
    print(json.dumps(validate(root,source)))
