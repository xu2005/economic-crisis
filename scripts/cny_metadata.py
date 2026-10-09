"""Curated application scopes; unknowns are null, never evidence of exemption/access."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];D=R/'data/v32-cny'
def put(name,obj):(D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def make_products(evidence=None):
 common=dict(market='SSE',currency='CNY',trading_fee=None,subscription_fee=None,redemption_fee=None,tracking_error_realised=None,qdii_remaining_quota=None,premium_discount=None,legal_access=True,account_access=True,capital_access=True,product_access=None,liquidity_access=None,tax_validated=None,data_continuous=False,cost_validated=False,selected=False,status='IMPLEMENTATION NOT VALIDATED',tax='TAX TREATMENT UNCERTAIN: product / account application not verified',fee_effective_history=None,capital_control='domestic CNY product route; offshore underlying access belongs to fund',mechanism='secondary market lot100; primary creations/redemptions separate, actual status unknown')
 rows=[
 dict(code='510300',name='华泰柏瑞沪深300ETF（不是嘉实）',asset='hs300-tr',inception='2012-05-04',listed='2012-05-28',listing_verified=False,management_fee=None,custody_fee=None,index='沪深300价格指数；投资者分红另记',exact_mapping=None,qdii=False,mapping_gap='需要实际净值+分红与H00300口径比较；上市日期本轮仅二级资料佐证，待基金正式文件',sources=['510300-listing-secondary'],evidence_level='C'),
 dict(code='160706',market='SZSE / domestic fund channel',mechanism='境内基金申购/赎回与深圳LOF二级交易分别核查；最低份额与历史上市日期尚未验证，转型须分段',name='嘉实沪深300 / 后转ETF联接LOF A',asset='hs300-tr',inception='2005-08-29',listed=None,listing_verified=False,management_fee=None,custody_fee=None,index='历史法律形式及基准须按转型分段',exact_mapping=None,qdii=False,mapping_gap='2011成立不等于今日ETF法律形式/费率历史可回穿；未取得历史净值分红',sources=['S02','S03'],evidence_level='A'),
 dict(code='GLOBAL-UNMAPPED',market='NO APPROVED PRODUCT',legal_access=None,account_access=None,capital_access=None,product_access=False,mechanism='尚无批准产品及购买路径，不填零售准入已通过',name='ACWI精确大陆复制路径未批准',asset='world-proxy',inception=None,listed=None,listing_verified=False,management_fee=None,custody_fee=None,index='MSCI ACWI（研究）；未有批准产品',exact_mapping=False,qdii=None,mapping_gap='美股单指数和主动全球基金不等价；组合也须覆盖/再平衡/成本证据',sources=['S04','S10'],evidence_level='A'),
 dict(code='511010',name='国泰上证5年期国债ETF',asset='china-treasury',inception='2013-03-05',listed='2013-03-25',listing_verified=True,management_fee=.0015,custody_fee=.0005,index='上证5年期国债指数',exact_mapping=False,qdii=False,mapping_gap='5年期限与H11006全期限/利息再投资不能默认等价；即使可买也不是目标资产严格复制',tracking_error_target='年化不超过2%（目标，非实现值）',sources=['511010-disclosure','511010-listed','S14'],evidence_level='A'),
 dict(code='518880',name='华安黄金ETF',asset='gold',inception='2013-07-18',listed='2013-07-29',listing_verified=True,management_fee=.005,custody_fee=.001,index='境内黄金现货合约；不是海外GLD',exact_mapping=None,qdii=False,mapping_gap='SGE与LBMA/GLD基差、费税和交易机制需量化；0.2%费差不是总复制差',sources=['518880-disclosure','S06','S07'],evidence_level='A'),
 dict(code='513500',name='博时标普500ETF（机会成本对照，非ACWI替身）',asset='sp500-tr',inception='2013-12-05',listed='2014-01-15',listing_verified=True,management_fee=None,custody_fee=None,index='标普500',exact_mapping=False,qdii=True,mapping_gap='美国单一指数不等价ACWI；正式费率现行段/历史段尚未完整核实',sources=['513500-listed'],evidence_level='A'),
 dict(code='513100',name='国泰纳斯达克100ETF（机会成本对照）',asset='nasdaq100-proxy',inception='2013-04-25',listed='2013-05-15',listing_verified=True,management_fee=.006,custody_fee=.002,index='纳斯达克100（经汇率调整总收益基准）',exact_mapping=False,qdii=True,mapping_gap='科技集中不等价全球；官方当前费率网页无生效日期，不回填历史',tracking_error_target='年化不超过2%（目标，非实现值）',sources=['513100-listed','513100-fees','513100-index'],evidence_level='A'),
 ]
 for r in rows:
  for k,v in common.items():r.setdefault(k,v)
  r['field_sources']={'identity':r['sources'],'listing':r['sources'],'fees':r['sources'] if r['management_fee'] is not None else [],'access':['fx-access','etf-lot'],'tax':['fund-tax','pit-law'],'bid_ask':[],'quota':[],'tracking_realised':[]}
 if evidence is None:
  path=D/'evidence-round2/evidence.json'
  evidence=json.loads(path.read_text()) if path.exists() else None
 from cny_product_evidence import enrich_products
 return enrich_products(rows,evidence)

def main():
 put('products.json',make_products())
 rules=[]
 def rule(id,category,source,published,effective,rate,scope,expires=None,verified=True,**extra):
  rules.append(dict(id=id,category=category,source_id=source,published=published,effective=effective,expires=expires,rate=rate,scope=scope,subject='CN-mainland resident individual',evidence_level='A',verified=verified,application_status='document verified; instrument / income applicability requires explicit matching',**extra))
 rule('openfund-redemption','domestic_openfund_redemption','fund-tax','2002-08-22','2002-08-22',0.,'CSRC-approved open securities fund personal subscription/redemption gains; temporary condition; NOT automatic QDII/gold/ETF-secondary exemption')
 rule('openfund-distribution','domestic_openfund_distribution','fund-tax','2002-08-22','2002-08-22',0.,'fund distributions to investor; underlying fund taxes separate, no second charge on embedded NAV')
 rule('ashare-dividend','ashare_dividend','ashare-div','2015-09-07','2015-09-08',.2,'direct A-share dividend record dates from effective day; defer short-held settlement at disposition',tiers={'within_month':.2,'month_to_year':.1,'over_year':0.})
 rule('treasury-interest','treasury_interest','pit-law','2018-08-31','2019-01-01',0.,'direct treasury and nationally-issued financial bond INTEREST; not bond trading gains or every debt fund')
 rule('foreign-transfer','foreign_security_realised_gain','pit-law','2018-08-31','2019-01-01',.2,'direct foreign financial asset disposal profit net original cost/reasonable fees; classification/country credit and tax FX conversion mandatory, separate access check')
 rule('foreign-dividend','foreign_dividend','pit-law','2018-08-31','2019-01-01',.2,'direct foreign dividend, not additional levy on QDII fund NAV')
 rule('hk-capital','hk_connect_capital_gain','hk-exemption','2023-08-21','2023-08-21',0.,'mainland personal HK Connect / recognised HK fund capital gains; no automatic dividend exemption',expires='2027-12-31')
 for cat in ['domestic_etf_secondary_gain','gold_etf_gain','qdii_gain','qdii_dividend','hk_connect_dividend','ashare_capital_gain','corporate_bond_interest','bond_trading_gain']:
  rule('unresolved-'+cat,cat,'fund-tax' if 'etf' in cat or 'qdii' in cat else 'pit-law',None,'2011-10-10',None,'TAX TREATMENT UNCERTAIN; narrower rule/source application or historic periods not verified',verified=False)
 put('tax_rules.json',rules)
 # Empty templates describe FUTURE records. No artificial current-day quotes / transactions.
 if not (D/'product-observations.csv').exists():(D/'product-observations.csv').write_text('timestamp,observed_at,source,code,kind,nav,close,fx,bid,ask,reference_at,premium_discount,subscription_status,quota_status,sha256\n')
 if not (D/'execution-ledger.csv').exists():(D/'execution-ledger.csv').write_text('decision_at,executed_at,code,side,units,price,commission,fx_friction,stamp_tax,income_tax,dividend,cash_after,sha256\n')
if __name__=='__main__':main()
