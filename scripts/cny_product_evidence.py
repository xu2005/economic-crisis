"""Dated disclosure evidence is distinct from executable investor returns."""
from pathlib import Path
import datetime, hashlib, math, re, unicodedata
from cny_implementability import Blocked

def normalise_text(text):
 return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text))

def parse_performance_table(text):
 """Parse the bounded section and retain all six source columns, in order.

 NFKC and whitespace normalisation handle PDF line wrapping, not missing data.
 Both difference columns must reconcile at the source's 0.01% precision.
 """
 s=normalise_text(text)
 heading='第十二部分基金的业绩'
 start=s.rfind(heading)
 if start<0:raise Blocked('performance heading missing')
 end=s.find('第十三部分基金的财产',start)
 if end<0:raise Blocked('performance section end missing')
 section=s[start:end]
 rx=r'(20\d\d)年(\d+)月(\d+)日至(20\d\d)年(\d+)月(\d+)日((?:-?\d+\.\d+%){6})'
 matches=list(re.finditer(rx,section))
 if len(matches)!=11:raise Blocked(f'expected all 11 disclosure periods, found {len(matches)}')
 out=[]
 for m in matches:
  y,mo,da,y2,mo2,da2=map(int,m.groups()[:6])
  try:a=datetime.date(y,mo,da).isoformat();b=datetime.date(y2,mo2,da2).isoformat()
  except ValueError as error:raise Blocked('invalid disclosure date') from error
  v=[float(x)/100 for x in re.findall(r'-?\d+\.\d+(?=%)',m.group(7))]
  if b<a or any(abs(v[i]-v[j]-v[k])>1.01e-4 for i,j,k in [(0,2,4),(1,3,5)]):raise Blocked('disclosure dates or six columns do not reconcile')
  out.append(dict(start=a,end=b,fund_return=v[0],fund_return_std=v[1],benchmark_return=v[2],benchmark_return_std=v[3],reported_gap=v[4],reported_std_gap=v[5],full_calendar_year=(mo,da,mo2,da2)==(1,1,12,31) and y==y2))
 if len({(r['start'],r['end']) for r in out})!=11:raise Blocked('duplicate disclosure period')
 if [(r['start'],r['end']) for r in out]!=[('2013-12-05','2013-12-31')]+[(f'{y}-01-01',f'{y}-12-31') for y in range(2014,2022)]+[('2022-01-01','2022-06-30'),('2013-12-05','2022-06-30')]:raise Blocked('unexpected disclosure coverage')
 return out

def enrich_products(products,evidence):
 """One metadata authoring path; source snapshots never qualify present terms."""
 if not evidence:return products
 fees={x['id']:x for x in evidence['fee_disclosures']}
 for p in products:
  if p['code']=='510300':
   fee=fees['510300-change-20241122']
   p.update(listing_verified=True,management_fee=fee['management_fee'],custody_fee=fee['custody_fee'],evidence_level='A',mapping_gap='正式上市公告核实2012-05-28；2024-11-22降费事件已核实，完整费率历史/真实NAV分红与交易费仍未齐',sources=['510300-listing-original','510300-annual2012','510300-feechange2024'],fee_effective_history=['510300-change-20241122'],fee_disclosure_as_of='2024-11-20',fee_current_at_observation_verified=False)
   p['field_sources'].update(identity=['510300-listing-original'],listing=['510300-listing-original','510300-annual2012'],fees=['510300-feechange2024'])
  if p['code']=='513500':
   fee=fees['513500-snapshot-20240626']
   p.update(index='标普500净总收益指数（Net TR）；人民币基金基准含估值汇率调整',management_fee=fee['management_fee'],custody_fee=fee['custody_fee'],fee_disclosure_as_of='2024-06-26',fee_current_at_observation_verified=False,fee_effective_history=['513500-snapshot-20221109','513500-snapshot-20240626'],mapping_gap='2022/2024披露费率0.60%/0.25%；不是ACWI，2026现行及连续历史费率未验证；年度NAV不是二级成交收益')
   p['sources']=list(dict.fromkeys(p['sources']+['513500-prospectus2022','513500-summary2024']))
   p['field_sources'].update(fees=['513500-prospectus2022','513500-summary2024'],index=['513500-prospectus2022'])
 return products

def disclosed_fee(records, code, event_date, knowledge_date=None):
 """Return the disclosed terms, never assert a complete fee-history coverage.

 A dated change can describe later terms; a snapshot cannot establish another
 day's fee. Date-only publication is excluded from that same day's information.
 """
 day=str(event_date)[:10];known=str(knowledge_date or event_date)[:10]
 candidates=[]
 for row in records:
  if row['code']!=code or not row.get('content_verified'):continue
  if not row.get('published_at') or row['published_at']>=known:continue
  if row['kind']=='CHANGE_EVENT':
   if row['effective']>day:continue
   if row.get('superseded_on') and day>=row['superseded_on']:continue
  elif row['kind']=='SNAPSHOT':
   if row['as_of']!=day:continue
  else:raise Blocked('unknown disclosure type')
  candidates.append(row)
 if not candidates:raise Blocked('no dated fee evidence for this date')
 row=max(candidates,key=lambda x:x['published_at'])
 return {**row,'status':'DISCLOSED TERMS / HISTORY CONTINUITY NOT QUALIFIED',
         'usable_for_formal_backtest':False}

def extra_nav_fee(nav, record=None, kind='PRODUCT_NAV'):
 if nav is None or not math.isfinite(nav) or nav<=0:raise Blocked('missing NAV')
 if kind in ['PRODUCT_NAV','DISTRIBUTION_ADJUSTED_PRODUCT_NAV']:
  return 0.0 # real NAV already recognises product expenses and fund-level tax
 raise Blocked('gross index replication needs complete fee and tracking history')

def verify_raw(root, receipt):
 if not receipt.get('original_sha256') or not receipt.get('file'):raise Blocked('no original bytes')
 p=Path(root)/receipt['file']
 if hashlib.sha256(p.read_bytes()).hexdigest()!=receipt['original_sha256']:raise Blocked('source hash mismatch')
 return True

def fund_performance_diagnostic(rows):
 """Compare disclosed full calendar-year NAV returns, not ETF market fills."""
 annual=[r for r in rows if r.get('full_calendar_year')]
 if not annual:raise Blocked('no full-year product disclosures')
 annual=sorted(annual,key=lambda x:x['start'])
 years=[int(r['start'][:4]) for r in annual]
 if years!=list(range(years[0],years[-1]+1)):raise Blocked('missing or duplicate annual period')
 f=b=1.
 for r in annual:
  if r['start']!=f"{int(r['start'][:4])}-01-01" or r['end']!=f"{int(r['start'][:4])}-12-31":raise Blocked('not a calendar year')
  for k in ['fund_return','benchmark_return']:
   if r.get(k) is None or not math.isfinite(r[k]) or r[k]<=-1:raise Blocked('missing / invalid reported return')
  f*=1+r['fund_return'];b*=1+r['benchmark_return']
 n=len(annual)
 return dict(layer='LEVEL 2 / DISCLOSED CNY FUND NAV PERFORMANCE',
             start=annual[0]['start'],end=annual[-1]['end'],years=n,
             fund_cagr=f**(1/n)-1,benchmark_cagr=b**(1/n)-1,
             geometric_drag=f**(1/n)-b**(1/n),fund_growth=f,benchmark_growth=b,
             mean_annual_gap=sum(r['fund_return']-r['benchmark_return'] for r in annual)/n,
             negative_years=sum(r['fund_return']<r['benchmark_return'] for r in annual),
             max_drawdown=None,sharpe=None,sortino=None,aftertax_cagr=None,
             market_executable=False,point_in_time=False,
             note='rounded annual disclosure; no daily risk inference; fees/taxes/FX/replication jointly embedded; not isolated fee attribution')

def product_observation_label(start, listed):
 if listed is None or start<listed:return 'FUND REPORTED / CONTAINS PRE-LISTING DATES'
 return 'FUND REPORTED / NOT MARKET EXECUTION'

def tax_document_applies(document_scope, product_type):
 """Scope match alone still does not validate current tax policy / all taxes."""
 return document_scope==product_type
