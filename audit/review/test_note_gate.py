import unittest,copy
from note_gate import *
def fixture():
 return [dict(id='one',traditional='一',simplified='一',pinyin='yi1',english_segments=['one'],raw_source='一 一 [yi1] /one/',source_line=1,ukrainian_segments=['один'],translation_status='model_generated',model_reviewed=False,review_status='not_model_reviewed',review_rating_before_corrections=None,correction_count=0,human_validation=False,has_known_uncertainty=True,uncertainty_flags=['translator_uncertainty'],uncertainty_notes=['Correct note for one.']),dict(id='two',traditional='二',simplified='二',pinyin='er4',english_segments=['two'],raw_source='二 二 [er4] /two/',source_line=2,ukrainian_segments=['два'],translation_status='model_generated',model_reviewed=False,review_status='not_model_reviewed',review_rating_before_corrections=None,correction_count=0,human_validation=False,has_known_uncertainty=True,uncertainty_flags=['translator_uncertainty'],uncertainty_notes=['Correct note for two.'])]
class GateTests(unittest.TestCase):
 def setUp(self):self.rows=fixture();self.e=note_event(self.rows[0],0,'retain_reviewed',reason='Read against source one.',review_source='review-test')
 def test_defaults_fail_closed(self):
  out,q,ledger,s=apply_gate(self.rows,[]);self.assertEqual(s['active_notes'],0);self.assertEqual(len(q),2);self.assertTrue(all(r['has_known_uncertainty'] for r in out));self.assertEqual(out[0]['uncertainty_flags'],self.rows[0]['uncertainty_flags'])
 def test_reviewed_note_retained(self):
  out,q,l,s=apply_gate(self.rows,[self.e]);self.assertEqual(out[0]['uncertainty_notes'],self.rows[0]['uncertainty_notes']);self.assertEqual(out[1]['uncertainty_notes'],[])
 def test_cross_entry_id_substitution_rejected(self):
  e=copy.deepcopy(self.e);e['id']='two'
  with self.assertRaises(GateValidationError):apply_gate(self.rows,[e])
 def test_stale_source_rejected(self):
  rows=copy.deepcopy(self.rows);rows[0]['english_segments']=['first']
  with self.assertRaises(GateValidationError):apply_gate(rows,[self.e])
 def test_changed_note_rejected(self):
  rows=copy.deepcopy(self.rows);rows[0]['uncertainty_notes']=['unrelated']
  with self.assertRaises(GateValidationError):apply_gate(rows,[self.e])
 def test_note_hash_tampering_rejected(self):
  e=copy.deepcopy(self.e);e['original_note_sha256']='0'*64
  with self.assertRaises(GateValidationError):apply_gate(self.rows,[e])
 def test_duplicate_approval_rejected(self):
  with self.assertRaises(GateValidationError):apply_gate(self.rows,[self.e,self.e])
 def test_row_reordering_does_not_reassign_notes(self):
  out,q,l,s=apply_gate(list(reversed(self.rows)),[self.e]);self.assertEqual(out[1]['id'],'one');self.assertEqual(out[1]['uncertainty_notes'],['Correct note for one.'])
 def test_immutable_input(self):
  before=copy.deepcopy(self.rows);apply_gate(self.rows,[self.e]);self.assertEqual(self.rows,before)
 def test_replacement_preserves_original_evidence(self):
  e=note_event(self.rows[0],0,'replace_reviewed',replacement='Verified replacement.',reason='Correct metadata.',review_source='review-test');out,q,l,s=apply_gate(self.rows,[e]);self.assertEqual(out[0]['uncertainty_notes'],['Verified replacement.']);self.assertEqual(q[0]['original_note'],'Correct note for one.')
 def test_rejection_preserves_original_flag(self):
  e=note_event(self.rows[0],0,'quarantine_rejected',reason='Wrong entry.',review_source='review-test');out,q,l,s=apply_gate(self.rows,[e]);self.assertTrue(out[0]['has_known_uncertainty']);self.assertEqual(out[0]['uncertainty_notes'],[])
 def test_stale_patch_rejected(self):
  r=self.rows[0];p=dict(id=r['id'],source_sha256=source_hash(r),baseline_record_sha256=digest(r),segment_index=0,before='wrong',after='одиниця',confidence='high')
  with self.assertRaises(GateValidationError):apply_gate(self.rows,[],[p])
 def test_reference_deletion_rejected(self):
  r=self.rows[0];r['english_segments']=['see 一[yi1]'];r['ukrainian_segments']=['див. 一[yi1]'];r['raw_source']='一 一 [yi1] /see 一[yi1]/';p=dict(id=r['id'],source_sha256=source_hash(r),baseline_record_sha256=digest(r),segment_index=0,before=r['ukrainian_segments'][0],after='див. один',confidence='high')
  with self.assertRaises(GateValidationError):apply_gate(self.rows,[],[p])
 def test_medium_patch_not_autoapplied(self):
  r=self.rows[0];p=dict(id=r['id'],source_sha256=source_hash(r),baseline_record_sha256=digest(r),segment_index=0,before='один',after='одиниця',confidence='medium')
  with self.assertRaises(GateValidationError):apply_gate(self.rows,[],[p])
class HardeningTests(unittest.TestCase):
 def test_whitespace_evidence_rejected(self):
  rows=fixture()
  with self.assertRaises(GateValidationError):note_event(rows[0],0,'retain_reviewed',reason=' ',review_source='source')
 def test_nonstring_evidence_rejected(self):
  rows=fixture()
  with self.assertRaises(GateValidationError):note_event(rows[0],0,'retain_reviewed',reason={'x':1},review_source=['source'])
 def test_malformed_notes_rejected(self):
  rows=fixture();rows[0]['uncertainty_notes']='not a list'
  with self.assertRaises(GateValidationError):apply_gate(rows,[])
 def test_misaligned_baseline_rejected(self):
  rows=fixture();rows[0]['ukrainian_segments']=[]
  with self.assertRaises(GateValidationError):apply_gate(rows,[])
 def test_noop_patch_rejected(self):
  rows=fixture();r=rows[0];p=dict(id=r['id'],source_sha256=source_hash(r),baseline_record_sha256=digest(r),segment_index=0,before='один',after='один',confidence='high')
  with self.assertRaises(GateValidationError):apply_gate(rows,[],[p])
 def test_quarantine_flags_do_not_alias_baseline(self):
  rows=fixture();out,q,l,s=apply_gate(rows,[]);q[0]['original_uncertainty_flags'].append('MUTATED');self.assertEqual(rows[0]['uncertainty_flags'],['translator_uncertainty'])
if __name__=='__main__':unittest.main()
