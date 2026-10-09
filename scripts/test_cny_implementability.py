import unittest,json,math,copy
from pathlib import Path
import pandas as pd
import numpy as np
from cny_implementability import *
from cny_account import Account,four_return_levels,real_cagr
class CNYTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rules=read('tax_rules.json');cls.products=read('products.json')
 def frame(self):
  p=pd.DataFrame({'a':[100,100,150,140,160,170],'b':[100,100,100,100,100,100]},index=['2020-12-29','2020-12-30','2020-12-31','2021-01-04','2021-02-01','2021-03-01']);return p,p.notna()
 def product(self):
  p=copy.deepcopy(next(x for x in self.products if x['code']=='518880'));p['tax_categories_validated']=['domestic_openfund_redemption'];p.update({k:True for k in ['exact_mapping','legal_access','account_access','capital_access','product_access','liquidity_access','tax_validated','data_continuous','cost_validated']});return p
 def quote(self):return dict(timestamp='2026-10-08T01:31:00Z',observed_at='2026-10-08T01:31:00Z',kind='PRODUCT_PRICE',price=10.,bid=10.,ask=10.,nav=10.,fx=1.,reference_at='2026-10-08T01:31:00Z',sha256='a'*64,status='TRADABLE')
 def test_01_listing_is_not_inception(self):
  p=next(x for x in self.products if x['code']=='513500')
  with self.assertRaises(Blocked):investability(p,'2013-12-06')
  self.assertIn('LISTED',investability(p,'2014-01-15'))
 def test_02_index_backfill_never_investable(self):self.assertEqual(investability(self.product(),'2011-10-10','INDEX_BACKFILL'),'RESEARCH ONLY / INDEX BACKFILL')
 def test_03_tax_date_expiry(self):
  self.assertEqual(tax_rule(self.rules,'hk_connect_capital_gain','2027-12-31')['rate'],0)
  with self.assertRaises(Blocked):tax_rule(self.rules,'hk_connect_capital_gain','2028-01-01')
 def test_04_tax_unknown_not_zero(self):
  for cat in ['qdii_gain','gold_etf_gain','hk_connect_dividend']:
   with self.assertRaises(Blocked):tax_rule(self.rules,cat,'2026-10-08')
 def test_05_no_future_tax_publication(self):
  with self.assertRaises(Blocked):tax_rule(self.rules,'ashare_dividend','2015-09-09','2015-09-06')
 def test_06_tax_only_income(self):
  rule=tax_rule(self.rules,'foreign_security_realised_gain','2026-10-08');self.assertEqual(tax_amount(rule,10000),2000);self.assertEqual(tax_amount(rule,-100),0)
 def test_07_foreign_credit_no_double_tax(self):
  rule=tax_rule(self.rules,'foreign_dividend','2026-10-08');self.assertEqual(tax_amount(rule,1000,300,True),0);self.assertEqual(tax_amount(rule,1000,300,False),200)
 def test_08_months_and_years_are_calendar(self):
  rule=tax_rule(self.rules,'ashare_dividend','2026-10-08');self.assertEqual(dividend_rate(rule,'2024-02-29','2025-02-28'),.1);self.assertEqual(dividend_rate(rule,'2024-02-29','2025-03-01'),0)
 def test_09_currency_conversion(self):self.assertEqual(convert_cny(100,7.3),730)
 def test_10_fx_identity_interaction(self):
  x=fx_identity(100,120,7,7.3);self.assertAlmostEqual(x['cny_return'],x['asset_return']+x['fx_return']+x['interaction']);self.assertAlmostEqual(x['residual'],0)
 def test_11_fx_friction_is_not_fx_movement(self):
  self.assertEqual(fx_conversion_cost(10000,50),50);self.assertEqual(fx_conversion_cost(10000,50,route='DOMESTIC_CNY'),0)
 def test_12_fx_missing(self):
  for x in [None,0,float('nan')]:
   with self.assertRaises(Blocked):convert_cny(100,x)
 def test_13_commission_minimum(self):self.assertEqual(fee(100,0.0001,5),5);self.assertEqual(fee(0,.0001,5),0)
 def test_14_fund_nav_fees_not_twice(self):
  self.assertEqual(product_layer(120,.006,.002,1,'PRODUCT_NAV'),120);self.assertLess(product_layer(120,.006,.002,1),120)
 def test_15_premium(self):self.assertAlmostEqual(premium(103,100),.03)
 def test_16_discount(self):self.assertAlmostEqual(premium(95,100),-.05)
 def test_17_missing_price_not_filled(self):
  p,o=self.frame();p.iloc[2,0]=np.nan
  with self.assertRaises(Blocked):proxy_run(p,o,{'a':.6,'b':.4})
 def test_18_mapping_gate(self):
  self.assertTrue(next(x for x in self.products if x['code']=='160706')['market'].startswith('SZSE'));self.assertIsNone(next(x for x in self.products if x['code']=='GLOBAL-UNMAPPED')['legal_access']);self.assertEqual(mapping_status(self.product()),'IMPLEMENTABLE');self.assertTrue(all(mapping_status(x)!='IMPLEMENTABLE' for x in self.products))
 def test_19_lookahead_observed_at(self):
  q=self.quote();q['observed_at']='2026-10-09T01:31:00Z'
  with self.assertRaises(Blocked):validate_product_quote(q,self.product(),'2026-10-08T02:00:00Z')
 def test_20_quote_timestamp_alignment(self):
  q=self.quote();q['reference_at']='2026-10-07T01:31:00Z'
  with self.assertRaises(Blocked):validate_product_quote(q,self.product(),'2026-10-08T02:00:00Z')
 def test_21_absolute_threshold(self):self.assertTrue(due('absolute-5pp','2026-01-01','2026-01-02',np.array([.66,.34]),np.array([.6,.4])));self.assertFalse(due('absolute-5pp','2026-01-01','2026-01-02',np.array([.62,.38]),np.array([.6,.4])))
 def test_22_relative_threshold(self):self.assertTrue(due('relative-20pct','2026-01-01','2026-01-02',np.array([.73,.27]),np.array([.6,.4])))
 def test_23_calendar_modes(self):
  for mode,day,result in [('annual','2026-04-01',False),('quarterly','2026-04-01',True),('semiannual','2026-07-01',True)]:self.assertEqual(due(mode,'2026-03-31',day,np.array([.6,.4]),np.array([.6,.4])),result)
 def test_24_cashflow_buys_underweights_only(self):
  b=cashflow_budgets(np.array([80.,20.]),np.array([.5,.5]),10.);self.assertEqual(b[0],0);self.assertAlmostEqual(b.sum(),10)
 def test_25_cashflow_twr_not_deposits(self):
  p,o=self.frame();p[:]=100;r=proxy_run(p,o,{'a':.6,'b':.4},'cashflow-only',contribution=500);self.assertTrue(r['contributions']>100000);np.testing.assert_allclose([x['nav'] for x in r['curve']],1.,atol=1e-12)
 def test_26_aftertax_total_wealth(self):self.assertAlmostEqual(aftertax_return(100000,120000,2000),.18)
 def test_27_unknown_tax_blocks_return(self):
  with self.assertRaises(Blocked):aftertax_return(100000,120000,None)
 def test_28_buy_hold_independent(self):
  p,o=self.frame();r=proxy_run(p,o,{'a':1.});np.testing.assert_allclose([x['equity'] for x in r['curve']],[100000,100000,150000,140000,160000,170000],atol=1e-7)
 def test_29_cash_and_wealth_conservation(self):
  p,o=self.frame();r=proxy_run(p,o,{'a':.6,'b':.4},f=Friction(trade_bp=15,minimum_cny=5));cash=100000
  for x in r['curve']:
   cash+=sum(f['cash_flow'] for f in r['fills'] if f['date']==x['date']);self.assertAlmostEqual(cash,x['cash']);self.assertAlmostEqual(x['equity'],x['cash']+x['value_a']+x['value_b']);self.assertGreaterEqual(cash,-1e-7)
 def test_30_units_conserved_through_nav_drag(self):
  p,o=self.frame();r=proxy_run(p,o,{'a':1.},f=Friction(extra_product_bp=100));q=0.;start=pd.Timestamp(p.index[0])
  for x in r['curve']:
   q+=sum(z['units'] for z in r['fills'] if z['date']==x['date']);factor=math.exp(-.01*(pd.Timestamp(x['date'])-start).days/365.25);self.assertAlmostEqual(q*p.loc[x['date'],'a']*factor,x['value_a'])
 def test_31_signal_later_execution_prefix(self):
  p,o=self.frame();full=proxy_run(p,o,{'a':.6,'b':.4});part=proxy_run(p.iloc[:4],o.iloc[:4],{'a':.6,'b':.4});self.assertEqual(part['curve'],full['curve'][:4]);self.assertTrue(all(x['signal_at']<x['date'] for x in full['fills']))
 def test_32_determinism(self):
  p,o=self.frame();self.assertEqual(proxy_run(p,o,{'a':.6,'b':.4},f=Friction(trade_bp=15)),proxy_run(p,o,{'a':.6,'b':.4},f=Friction(trade_bp=15)))
 def test_33_primary_closed_secondary_route(self):self.assertIn('SECONDARY',access_route(False,True,.01));self.assertIn('BLOCKED',access_route(False,True,.1));self.assertIn('BLOCKED',access_route(None,None,None))
 def test_34_actual_account_lot_cash_tax(self):
  a=Account(cash=2000.);p=self.product();q=self.quote();execution=dict(executed_at=q['timestamp'],side='buy',units=100,price=10.)
  costs=dict(verified=True,source='test fixture only',commission_rate=.001,minimum=5,stamp_rate=0.)
  x=a.execute(p,q,'2026-10-08T00:00:00Z',execution,self.rules,'domestic_openfund_redemption',costs);self.assertEqual(a.cash,995);self.assertEqual(a.units[p['code']],100);self.assertEqual(a.wealth({p['code']:10}),1995)
  execution['units']=1
  with self.assertRaises(Blocked):a.execute(p,q,'2026-10-08T00:00:00Z',execution,self.rules,'domestic_openfund_redemption',costs)
 def test_35_dividend_no_double_count(self):
  a=Account();a.units['test']=100.;self.assertEqual(a.distribution('test',1,self.rules,'2026-10-08','domestic_openfund_distribution',application_verified=True),100)
  with self.assertRaises(Blocked):a.distribution('test',1,self.rules,'2026-10-08','domestic_openfund_distribution',True)
 def test_36_actual_unknown_tax_no_mutation(self):
  a=Account();before=copy.deepcopy(a);q=self.quote();e=dict(executed_at=q['timestamp'],side='buy',units=100,price=10)
  with self.assertRaises(Blocked):a.execute(self.product(),q,'2026-10-08T00:00:00Z',e,self.rules,'gold_etf_gain',dict(verified=True,source='fixture',commission_rate=0,minimum=0,stamp_rate=0))
  self.assertEqual(a,before)
 def test_37_historical_shift_does_not_use_same_date(self):
  p,o,x,prov=historical_panel();self.assertAlmostEqual(p.iloc[0]['world-proxy'],x.iloc[0]['world-proxy']);self.assertEqual(p.index[0],x.index[1]);self.assertEqual(prov['input'],'reports/crisis-v3/input/cross-asset-aligned.csv')
 def test_38_no_real_results_from_proxy(self):
  p,o=self.frame();r=proxy_run(p,o,{'a':1.});m=kpi(r);self.assertIsNone(m['aftertax_cagr']);self.assertIsNone(m['real_cagr']);self.assertIsNone(m['cumulative_tax']);self.assertIsNone(m['fund_expenses'])
 def test_39_saved_csv_web_kpi(self):
  result=json.loads((O/'results.json').read_text());saved=pd.read_csv(O/'proxy-stress-summary.csv')
  self.assertEqual(len(saved),96);self.assertEqual(len(result['formal_results']),5)
  for row in result['proxy_summary']:
   x=saved[(saved.id==row['id'])&(saved.scenario==row['scenario'])&(saved['mode']==row['mode'])].iloc[0];self.assertAlmostEqual(x.proxy_cagr,row['proxy_cagr'],places=12)
  self.assertTrue(all(x['aftertax_cagr'] is None for x in result['formal_results']))
  for x in result['proxy_curves']:
   expected=next(z['proxy_mdd'] for z in result['proxy_summary'] if z['id']==x['id'] and z['scenario']==x['scenario'] and z['mode']=='annual');self.assertAlmostEqual(max(z['drawdown'] for z in x['data']),expected,places=12)
 def test_40_protocol_no_optimisation(self):
  config=read('protocol.json');sha=config.pop('sha256');self.assertEqual(digest(config),sha);self.assertEqual(config['weights'],{'hs300-tr':.3,'world-proxy':.3,'china-treasury':.3,'gold':.1})
 def test_41_four_layers_do_not_fill_asset_gross(self):
  x=four_return_levels(100000,None,120000,119000,1000,True);self.assertIsNone(x['gross_asset_return']);self.assertAlmostEqual(x['investor_after_tax_cny_return'],.18)
 def test_42_real_cagr_uses_cpi(self):
  self.assertAlmostEqual(real_cagr(.05,100,102,1),1.05/1.02-1)
  with self.assertRaises(Blocked):real_cagr(.05,None,None,1)
 def test_43_formal_layer_requires_validation(self):self.assertIsNone(four_return_levels(100,120,115,110,0,False)['investor_after_tax_cny_return'])
 def test_44_actual_account_tax_scope_must_match(self):
  p=self.product();p['tax_categories_validated']=[];q=self.quote();e=dict(executed_at=q['timestamp'],side='buy',units=100,price=10)
  with self.assertRaises(Blocked):Account().execute(p,q,'2026-10-08T00:00:00Z',e,self.rules,'domestic_openfund_redemption',dict(verified=True,source='fixture',commission_rate=0,minimum=0,stamp_rate=0))
 def test_45_terminal_liquidation_is_explicit(self):
  p,o=self.frame();r=proxy_run(p,o,{'a':1.},f=Friction(hypothetical_gain_tax=.2));self.assertAlmostEqual(r['terminal'],r['curve'][-1]['cash']+sum(x['net_proceeds'] for x in r['liquidation']));self.assertEqual(r['liquidation'][0]['synthetic_tax'],r['terminal_synthetic_tax'])
if __name__=='__main__':unittest.main(verbosity=2)
