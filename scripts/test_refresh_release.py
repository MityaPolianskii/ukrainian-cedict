"""Fail-closed checks for source and review admission boundaries."""
import copy
import gzip
import tempfile
import unittest
from pathlib import Path
import refresh_release as release


class AdmissionBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.candidate=dict(author_key='author',human_validation=False,runtime_approved=False,
                            ukrainian_segments=['двері та вікна'])
        self.review=dict(reviewer_key='other reviewer',candidate_sha256=release.digest(self.candidate),
                         decision='accept',human_validation=False,rationale='Doors and windows are both retained.')

    def test_edited_translation_cannot_reuse_an_earlier_approval(self):
        release.candidate_check(self.candidate,self.review)
        altered=copy.deepcopy(self.candidate);altered['ukrainian_segments']=['лише двері']
        with self.assertRaisesRegex(ValueError,'exact candidate'):
            release.candidate_check(altered,self.review)

    def test_same_author_or_held_verdict_cannot_admit_a_candidate(self):
        for changes in [dict(reviewer_key='author'),dict(decision='hold'),dict(human_validation=True),dict(runtime_approved=True)]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                release.candidate_check(self.candidate,dict(self.review,**changes))

    def test_blank_or_absent_worker_identities_are_not_independent_review(self):
        for author in [None,'','  ']:
            c=dict(self.candidate,author_key=author);r=dict(self.review,candidate_sha256=release.digest(c))
            with self.subTest(author=author),self.assertRaisesRegex(ValueError,'author identity'):
                release.candidate_check(c,r)
        for reviewer in [None,'','  ']:
            with self.subTest(reviewer=reviewer),self.assertRaisesRegex(ValueError,'reviewer identity'):
                release.candidate_check(self.candidate,dict(self.review,reviewer_key=reviewer))

    def test_reference_formatting_does_not_permit_changed_tones_or_graphs(self):
        source=dict(english_segments=['see 律師事務所|律师事务所[lu : 4 shi1 shi4 wu4 suo3]'])
        release.translation_check(source,['див. 律師事務所|律师事务所[lu:4 shi1 shi4 wu4 suo3]'])
        for u in ['див. 律師事務所|律师事务所[lu:3 shi1 shi4 wu4 suo3]','адвокатська фірма']:
            with self.assertRaisesRegex(ValueError,'reference'):release.translation_check(source,[u])
        with self.assertRaisesRegex(ValueError,'reference'):
            release.translation_check(dict(english_segments=['see 〇[ling2]']),['див. нуль'])

    def test_manifest_cannot_relabel_model_work_as_human_or_runtime_approved(self):
        m=dict(release.MANIFEST_METADATA,counts={},files={k:{} for k in release.RELEASE_FILES});release.manifest_check(m)
        for changes in [dict(runtime_approved=True),dict(linguistic_accuracy_certified=True),
                        dict(human_validation_scope='all records validated'),dict(license='unrestricted')]:
            with self.subTest(changes=changes),self.assertRaisesRegex(ValueError,'metadata'):
                release.manifest_check(dict(m,**changes))
        with self.assertRaisesRegex(ValueError,'inventory'):release.manifest_check(dict(m,files={}))

    def test_human_batch_cannot_be_invented_expanded_or_publish_private_fields(self):
        with self.assertRaisesRegex(ValueError,'incomplete'):release.human_check([],{}, {})
        with self.assertRaisesRegex(ValueError,'fields'):
            release.human_check([dict(raw_user_response='private')],{}, {})
        invented={k:None for k in release.HUMAN_FIELDS};invented['entry_id']='unreviewed'
        with self.assertRaisesRegex(ValueError,'identity'):release.human_check([invented],{}, {})

    def test_superseded_candidates_cannot_be_current_or_lose_their_body(self):
        c=self.candidate;h=release.digest(c)
        history=dict(superseded_revision_candidates=[c],revision_history=[],superseded_review_verdicts=[])
        with self.assertRaisesRegex(ValueError,'also superseded'):release.history_check(history,{h})
        history=dict(superseded_revision_candidates=[],revision_history=[],superseded_review_verdicts=[self.review])
        with self.assertRaisesRegex(ValueError,'exact candidate body'):release.history_check(history,set())

    def test_unknown_upstream_snapshot_is_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'unexpected.gz';p.write_bytes(gzip.compress(b'#! entries=1\n'))
            with self.assertRaisesRegex(ValueError,'source bytes'):release.parse_source(p)


if __name__=='__main__':unittest.main()
