"""Evidence boundaries, frozen outputs and repeat-generation integration checks."""
import copy, hashlib, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from cny_implementability import Blocked, digest, investability, mapping_status
from cny_product_evidence import (disclosed_fee, extra_nav_fee, fund_performance_diagnostic,
 normalise_text, parse_performance_table, product_observation_label, tax_document_applies, verify_raw)
import build_cny_evidence as builder
from cny_metadata import make_products
R=Path(__file__).resolve().parents[1];D=R/'data/v32-cny/evidence-round2';O=R/'reports/crisis-v32-cny'
class EvidenceRound2Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.e=json.loads((D/'evidence.json').read_text());cls.fees=cls.e['fee_disclosures'];cls.rows=cls.e['product_periods']
  cls.receipts=builder.receipts();cls.sources=json.loads((R/'data/v32-cny/data_sources.json').read_text());cls.products=make_products()
  cls.raw=next(x for x in cls.receipts if x['id']=='513500-prospectus2022' and x.get('original_sha256'));cls.text=builder.text_for(cls.raw)
 def test_01_fee_change_effective_boundary(self):
  with self.assertRaises(Blocked):disclosed_fee(self.fees,'510300','2024-11-21')
  x=disclosed_fee(self.fees,'510300','2024-11-22');self.assertEqual(x['management_fee'],.0015);self.assertEqual(x['custody_fee'],.0005)
 def test_02_same_day_publication_excluded(self):
  with self.assertRaises(Blocked):disclosed_fee(self.fees,'510300','2024-11-22','2024-11-20')
 def test_03_future_publication_excluded(self):
  with self.assertRaises(Blocked):disclosed_fee(self.fees,'510300','2024-11-22','2024-11-19')
 def test_04_historical_fees_not_backfilled(self):
  with self.assertRaises(Blocked):disclosed_fee(self.fees,'510300','2011-10-10')
 def test_05_snapshots_never_extrapolate(self):
  with self.assertRaises(Blocked):disclosed_fee(self.fees,'513500','2026-10-08')
  with self.assertRaises(Blocked):disclosed_fee(self.fees,'513500','2024-06-27')
 def test_06_snapshot_requires_later_knowledge(self):
  with self.assertRaises(Blocked):disclosed_fee(self.fees,'513500','2024-06-26')
  x=disclosed_fee(self.fees,'513500','2024-06-26','2024-06-27');self.assertEqual(x['custody_fee'],.0025);self.assertFalse(x['usable_for_formal_backtest'])
 def test_07_disclosed_change_is_not_current_qualification(self):
  x=disclosed_fee(self.fees,'510300','2026-10-08');self.assertFalse(x['usable_for_formal_backtest']);self.assertFalse(x['history_continuity_validated'])
 def test_08_superseded_and_unverified_fees_blocked(self):
  rows=copy.deepcopy(self.fees);rows[0]['superseded_on']='2025-01-01'
  with self.assertRaises(Blocked):disclosed_fee(rows,'510300','2025-01-01')
  rows[0]['content_verified']=False
  with self.assertRaises(Blocked):disclosed_fee(rows,'510300','2024-11-22')
 def test_09_real_nav_no_second_product_fee(self):
  self.assertEqual(extra_nav_fee(100,self.fees[0]),0.);self.assertEqual(extra_nav_fee(100,kind='DISTRIBUTION_ADJUSTED_PRODUCT_NAV'),0.)
  with self.assertRaises(Blocked):extra_nav_fee(100,kind='GROSS_INDEX')
 def test_10_missing_or_invalid_nav_blocks(self):
  for v in [None,0,-1,float('nan'),float('inf')]:
   with self.assertRaises(Blocked):extra_nav_fee(v)
 def test_11_all_original_bytes_hash_checked(self):
  success=[x for x in self.receipts if x.get('original_sha256')];self.assertEqual(len(success),7)
  for row in success:self.assertTrue(verify_raw(R,row))
 def test_12_tampered_original_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'source.raw';p.write_bytes(b'original');rec={'file':'source.raw','original_sha256':hashlib.sha256(b'original').hexdigest()};self.assertTrue(verify_raw(d,rec));p.write_bytes(b'modified')
   with self.assertRaises(Blocked):verify_raw(d,rec)
 def test_13_failed_attempts_retained_separately(self):
  failed=[r for r in self.sources if r['id'].startswith('R2-') and r['capture_status']=='FAILED'];self.assertEqual(len(failed),2);self.assertTrue(all(x.get('error') and not x['original_sha256'] for x in failed));self.assertEqual(sum(x['id'].startswith('R2-') for x in self.sources),9)
 def test_14_closed_fund_scope_not_etf_qdii(self):
  self.assertTrue(tax_document_applies('CLOSED_END','CLOSED_END'))
  for kind in ['ETF','QDII','GOLD_ETF']:self.assertFalse(tax_document_applies('CLOSED_END',kind))
  self.assertFalse(self.e['closed_fund_tax_scope']['tax_application_approved'])
 def test_15_issue_effective_publication_distinct(self):
  x=self.e['closed_fund_tax_scope'];self.assertEqual(x['issued'],'1998-08-06');self.assertEqual(x['effective'],'1998-03-01');self.assertIsNone(x['published_at'])
  x=next(s for s in self.sources if s['id']=='510300-annual2012');self.assertTrue(x['publication_date_conflict']);self.assertIsNone(x['first_publication_at']);self.assertIsNone(x['published_at'])
 def test_16_pre_listing_disclosure_not_execution(self):
  self.assertIn('PRE-LISTING',product_observation_label('2014-01-01','2014-01-15'));p=next(x for x in self.products if x['code']=='513500')
  with self.assertRaises(Blocked):investability(p,'2014-01-01')
  self.assertIn('NOT MARKET EXECUTION',product_observation_label('2015-01-01',p['listed']))
 def test_17_all_eleven_rows_and_six_columns_preserved(self):
  rows=parse_performance_table(self.text);self.assertEqual(len(rows),11)
  for got,saved in zip(rows,self.rows):
   for k,v in got.items():self.assertEqual(v,saved[k])
  self.assertFalse(rows[0]['full_calendar_year']);self.assertFalse(rows[-2]['full_calendar_year']);self.assertFalse(rows[-1]['full_calendar_year']);self.assertEqual(rows[-1]['fund_return'],1.4022)
 def test_18_pdf_whitespace_and_fullwidth_normalised(self):
  self.assertIn('NetTR',normalise_text(self.text));self.assertEqual(parse_performance_table(self.text),parse_performance_table(normalise_text(self.text)));self.assertEqual(normalise_text('Ｎｅｔ\n ＴＲ'), 'NetTR')
 def test_19_missing_table_row_rejected(self):
  s=normalise_text(self.text);a=s.index('2018年1月1日至2018年12月31日');b=s.index('2019年1月1日至2019年12月31日',a)
  with self.assertRaises(Blocked):parse_performance_table(s[:a]+s[b:])
 def test_20_changed_six_column_relationship_rejected(self):
  s=normalise_text(self.text).replace('13.38%0.67%13.40%0.69%-0.02%-0.02%','13.38%0.67%13.40%0.69%8.00%-0.02%')
  with self.assertRaises(Blocked):parse_performance_table(s)
 def test_21_missing_annual_year_blocked(self):
  with self.assertRaises(Blocked):fund_performance_diagnostic([r for r in self.rows if r['start']!='2018-01-01'])
 def test_22_duplicate_annual_year_blocked(self):
  with self.assertRaises(Blocked):fund_performance_diagnostic(self.rows+[self.rows[1]])
 def test_23_invalid_annual_value_or_dates_blocked(self):
  for field,value in [('fund_return',None),('fund_return',-1),('benchmark_return',float('nan')),('end','2014-11-30')]:
   rows=copy.deepcopy(self.rows);rows[1][field]=value
   with self.assertRaises(Blocked):fund_performance_diagnostic(rows)
 def test_24_annual_diagnostic_independent_compounding(self):
  f=[.1338,.0695,.1758,.1302,-.0118,.3164,.0953,.2432];b=[.134,.0691,.1882,.1407,-.0016,.3285,.1014,.2523];gf=gb=1.
  for x,y in zip(f,b):gf*=1+x;gb*=1+y
  d=self.e['product_diagnostic'];self.assertAlmostEqual(d['fund_cagr'],gf**(1/8)-1);self.assertAlmostEqual(d['benchmark_cagr'],gb**(1/8)-1);self.assertEqual(d['years'],8)
 def test_25_no_annual_to_daily_or_aftertax_inference(self):
  d=self.e['product_diagnostic']
  for k in ['max_drawdown','sharpe','sortino','aftertax_cagr']:self.assertIsNone(d[k])
  self.assertFalse(d['market_executable']);self.assertFalse(d['point_in_time']);self.assertTrue(all(r['market_return'] is None and r['aftertax_return'] is None for r in self.rows))
 def test_26_all_source_references_resolve(self):
  ids={s['id'] for s in self.sources};self.assertEqual(len(ids),len(self.sources))
  for p in self.products:
   self.assertTrue(set(p['sources'])<=ids)
   for values in p['field_sources'].values():self.assertTrue(set(values)<=ids)
  for rows in [self.fees,self.rows]:
   for x in rows:self.assertIn(x['source_id'],ids)
 def test_27_registry_rebuild_idempotent(self):
  self.assertEqual(builder.source_registry(self.sources,self.receipts),self.sources)
 def test_28_metadata_regeneration_keeps_evidence(self):
  self.assertEqual(self.products,json.loads((R/'data/v32-cny/products.json').read_text()));self.assertTrue(next(x for x in self.products if x['code']=='510300')['listing_verified']);self.assertTrue(all(mapping_status(p)!='IMPLEMENTABLE' for p in self.products));self.assertFalse(next(x for x in self.products if x['code']=='513500')['fee_current_at_observation_verified'])
 def test_29_temporary_result_enrichment_independent_of_output(self):
  with tempfile.TemporaryDirectory() as d,patch.object(builder,'O',Path(d)):
   self.assertEqual(builder.enrich_results({})['evidence_round2'],self.e)
 def test_30_frozen_numeric_csv_and_protocol_unchanged(self):
  baseline=json.loads((D/'baseline.json').read_text());self.assertEqual(len(baseline['frozen_outputs']),306)
  for name,sha in baseline['frozen_outputs'].items():self.assertEqual(hashlib.sha256((R/name).read_bytes()).hexdigest(),sha,name)
  protocol=json.loads((D/'protocol.json').read_text());sha=protocol.pop('sha256');self.assertEqual(digest(protocol),sha);self.assertTrue(protocol['weights_frozen'] and protocol['benchmarks_frozen'] and protocol['existing_oos_automation_stays_paused'])
 def test_31_csv_results_and_published_data_consistent(self):
  result=json.loads((O/'results.json').read_text());self.assertEqual(result['evidence_round2'],self.e)
  frame=pd.read_csv(O/'product-disclosed-periods.csv');self.assertEqual(len(frame),11)
  for row,saved in zip(frame.to_dict('records'),self.rows):
   for k in ['fund_return','benchmark_return','fund_return_std','benchmark_return_std','reported_gap','reported_std_gap']:self.assertAlmostEqual(row[k],saved[k],places=12)
  self.assertEqual((O/'results.json').read_bytes(),(R/'public/crisis-v32-cny/results.json').read_bytes())
  self.assertEqual((O/'product-disclosed-periods.csv').read_bytes(),(R/'public/crisis-v32-cny/product-disclosed-periods.csv').read_bytes())
 def test_32_formal_fields_and_strong_benchmark_remain_frozen(self):
  result=json.loads((O/'results.json').read_text());self.assertEqual(result['registered']['strong'],{'world-proxy':.6,'china-treasury':.4});self.assertEqual(result['registered']['weights'],{'hs300-tr':.3,'world-proxy':.3,'china-treasury':.3,'gold':.1})
  for r in result['formal_results']:self.assertIsNone(r['aftertax_cagr']);self.assertIsNone(r['wealth_aftertax_cny'])
  self.assertEqual(self.e['formal_aftertax_valid'],0);self.assertFalse(self.e['bond_variants']['numerical_series_replaced'])
if __name__=='__main__':unittest.main(verbosity=2)
