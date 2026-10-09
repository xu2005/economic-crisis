"""Build the reproducible second evidence round; never changes proxy outcomes."""
from pathlib import Path
import csv, hashlib, json, re
from cny_product_evidence import fund_performance_diagnostic, product_observation_label, verify_raw, normalise_text, parse_performance_table
from cny_implementability import Blocked
R=Path(__file__).resolve().parents[1];D=R/'data/v32-cny/evidence-round2';O=R/'reports/crisis-v32-cny'
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def receipts():
 rows=[]
 for p in sorted((D/'attempts').glob('*/receipts.json')):
  for row in json.loads(p.read_text()):rows.append({**row,'attempt':p.parent.name})
 return rows
def text_for(row):
 verify_raw(R,row);p=R/row['file']
 import fitz
 with fitz.open(stream=p.read_bytes(),filetype='pdf') as doc:
  return '\n'.join(page.get_text() for page in doc)

def enrich_results(result):
 # Canonical data snapshot is independent of report/temporary output paths.
 p=R/'data/v32-cny/evidence-round2/evidence.json'
 if p.exists():result['evidence_round2']=json.loads(p.read_text())
 return result

def verify_baseline():
 baseline=json.loads((D/'baseline.json').read_text())
 for p,h in baseline['frozen_outputs'].items():
  if hashlib.sha256((R/p).read_bytes()).hexdigest()!=h:raise Blocked('frozen numerical output changed: '+p)
 return len(baseline['frozen_outputs'])

def source_registry(existing,all_rows):
 # Stable source identity and append-only attempt identities have separate roles.
 ids={r['id'] for r in all_rows}
 registry=[s for s in existing if not s['id'].startswith('R2-') and s['id'] not in ids]
 good={r['id']:r for r in all_rows if r.get('original_sha256')}
 for sid,row in sorted(good.items()):
  item={**row,'id':sid,'scope':'原件内容核实；仅身份/披露日期/费用/Net TR/基金税主体范围，不批准实际交易或税后收益','capture_status':'ORIGINAL HASH + CONTENT VERIFIED; APPLICATION NOT QUALIFIED','content_verified':True,'point_in_time':False}
  if sid=='510300-annual2012':item.update(published_at=None,url_date='2013-03-27',document_issue_date='2013-03-28',first_publication_at=None,publication_date_conflict=True)
  if sid=='fund-tax1998-scope':item.update(published_at=None,document_issue_date='1998-08-06',first_publication_at=None,publication_timestamp_verified=False)
  registry.append(item)
 for x in all_rows:
  registry.append({**x,'id':'R2-'+x['id']+'-'+x['attempt'],'source_id':x['id'],'scope':'独立下载尝试回执；含失败。HTTP成功不等于应用资格','capture_status':x['status']})
 if len({x['id'] for x in registry})!=len(registry):raise Blocked('duplicate source identity')
 return registry

def main():
 preserved=verify_baseline()
 protocol=json.loads((D/'protocol.json').read_text())
 from cny_implementability import digest
 if digest({k:v for k,v in protocol.items() if k!='sha256'})!=protocol['sha256']:raise Blocked('evidence protocol changed')
 all_rows=receipts();good={r['id']:r for r in all_rows if r.get('original_sha256')}
 needed=['510300-listing-original','510300-annual2012','510300-feechange2024','513500-prospectus2022','513500-summary2024','fund-tax1998-scope','H11006-factsheet-followup']
 assert all(x in good for x in needed),'required source content is missing'
 for row in good.values():verify_raw(R,row)
 texts={k:text_for(v) for k,v in good.items() if (R/v['file']).read_bytes().startswith(b'%PDF')}
 fee_text=normalise_text(texts['510300-feechange2024']);assert all(x in fee_text for x in ['2024年11月22日','0.50%','0.15%','0.10%','0.05%'])
 prospect=texts['513500-prospectus2022'];clean=normalise_text(prospect)
 assert 'NetTR' in clean and '本基金的管理费按前一日基金资产净值0.60%' in clean and 'H=E×0.25%' in clean and 'H=E×0.06%' in clean and '费用下限' in clean
 summary=normalise_text(texts['513500-summary2024']);assert all(x in summary for x in ['固定比例0.60%','固定比例0.25%','0.91%','2024年6月26日'])
 listing=normalise_text(texts['510300-listing-original']);assert '上市交易日期:2012年5月28日' in listing and '二级市场交易代码:510300' in listing
 annual=normalise_text(texts['510300-annual2012']);assert '上市日期2012-05-28' in annual and '送出日期:2013年3月28日' in annual
 html=(R/good['fund-tax1998-scope']['file']).read_text(errors='replace');assert '封闭式' in html
 fact=texts['H11006-factsheet-followup'];assert 'N11006' in fact and 'H01006' in fact
 fees=[dict(id='510300-change-20241122',code='510300',kind='CHANGE_EVENT',effective='2024-11-22',as_of=None,published_at='2024-11-20',management_fee=.0015,custody_fee=.0005,previous_management_fee=.005,previous_custody_fee=.001,history_continuity_validated=False,content_verified=True,source_id='510300-feechange2024',raw_sha256=good['510300-feechange2024']['original_sha256']),
       dict(id='513500-snapshot-20221109',code='513500',kind='SNAPSHOT',effective=None,as_of='2022-11-09',published_at='2022-11-09',management_fee=.006,custody_fee=.0025,index_licence_fee=.0006,licence_minimum_applies=True,history_continuity_validated=False,content_verified=True,source_id='513500-prospectus2022',raw_sha256=good['513500-prospectus2022']['original_sha256']),
       dict(id='513500-snapshot-20240626',code='513500',kind='SNAPSHOT',effective=None,as_of='2024-06-26',published_at='2024-06-26',management_fee=.006,custody_fee=.0025,reported_estimated_operating_rate=.0091,operating_rate_not_fixed_fee=True,history_continuity_validated=False,content_verified=True,source_id='513500-summary2024',raw_sha256=good['513500-summary2024']['original_sha256'])]
 # Extract every row from the official performance table, including initial and partial periods.
 periods=[]
 for row in parse_performance_table(prospect):
  periods.append({**row,'code':'513500','currency':'CNY','benchmark':'S&P 500 Net TR × disclosed valuation FX convention','layer':'LEVEL 2 / REPORTED FUND NAV','date_access_label':product_observation_label(row['start'],'2014-01-15'),'published_at':'2022-11-09','observed_at':good['513500-prospectus2022']['observed_at'],'source_id':'513500-prospectus2022','source_sha256':good['513500-prospectus2022']['original_sha256'],'pdf_pages':'68–69','manual_processing':False,'retrospective':True,'aftertax_return':None,'market_return':None})
 diagnostic=fund_performance_diagnostic(periods)
 registry_path=R/'data/v32-cny/data_sources.json';registry=source_registry(json.loads(registry_path.read_text()),all_rows)
 out=dict(id='V3.2 Evidence Round 2',protocol=protocol,verdict='FREEZE / IMPLEMENTATION BLOCKED',captured=len(good),failed_attempts=sum(x['status']=='FAILED' for x in all_rows),receipts=all_rows,fee_disclosures=fees,product_periods=periods,product_diagnostic=diagnostic,
          closed_fund_tax_scope=dict(source_id='fund-tax1998-scope',subject='newly CSRC-approved closed-end securities investment funds',issued='1998-08-06',published_at=None,first_publication_unknown=True,effective='1998-03-01',retrospective_effective=True,scope_not_etf_or_qdii=True,tax_application_approved=False),
          bond_variants=dict(source_id='H11006-factsheet-followup',as_of='2026-08-31',used_code='H11006',clean_price_code='H01006',interest_reinvestment_code='N11006',methodology_reconciled=False,numerical_series_replaced=False),
          preserved_numeric_files=preserved,actual_trades=0,formal_aftertax_valid=0,
          open_gaps=['ACWI大陆精确路径','H11006/N11006现金再投公式和历史对账','连续产品NAV/分红/拆分','同期实际报价/IOPV/申购额度','历史费率连续性与2026现行确认','ETF/QDII具体所得税适用','账户成本与长期冻结OOS'])
 # Validate all references before writing any generated result.
 from cny_metadata import make_products
 products=make_products(out)
 referenced={f['source_id'] for f in fees}|{x['source_id'] for x in periods}|{out['closed_fund_tax_scope']['source_id'],out['bond_variants']['source_id']}
 for p in products:
  referenced.update(p['sources'])
  for values in p['field_sources'].values():referenced.update(values)
 if not referenced<={r['id'] for r in registry}:raise Blocked('dangling source references: '+str(referenced-{r['id'] for r in registry}))
 write(D/'fee_disclosures.json',fees);write(D/'product_periods.json',periods);write(D/'evidence.json',out)
 write(R/'data/v32-cny/products.json',products);write(O/'products.json',products);write(registry_path,registry);write(O/'evidence-round2.json',out)
 for name,rows in [('product-disclosed-periods.csv',periods),('fee-disclosures.csv',fees)]:
  with (O/name).open('w',newline='') as f:
   keys=list(dict.fromkeys(k for x in rows for k in x));w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)
 result=json.loads((O/'results.json').read_text());result['products']=products;result['sources']=registry;enrich_results(result);write(O/'results.json',result)
 # Same CSV serialization as the primary generator, including the unchanged schema.
 import pandas as pd
 pd.DataFrame([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in x.items()} for x in products]).to_csv(O/'product-mapping.csv',index=False)
 verify_baseline()
 print(json.dumps({'captured':len(good),'failed_attempts':out['failed_attempts'],'periods':len(periods),'diagnostic':diagnostic},ensure_ascii=False))
if __name__=='__main__':main()
