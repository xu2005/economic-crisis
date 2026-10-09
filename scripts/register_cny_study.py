"""Register the fixed CNY study before running experiments; capture official evidence."""
from pathlib import Path
import json,hashlib,datetime,urllib.request,concurrent.futures,shutil
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/v32-cny';O=ROOT/'reports/crisis-v32-cny'
D.mkdir(parents=True,exist_ok=True);O.mkdir(parents=True,exist_ok=True)
SOURCES=[
('fund-tax','财税〔2002〕128号·开放式证券投资基金','https://www.chinatax.gov.cn/chinatax/n810341/n810765/n812203/200207/c1208424/content.html','2002-08-22','A','个人申赎差价及分配暂免；不自动推断全部QDII/黄金底层税负'),
('pit-law','个人所得税法2018修正','https://jiangsu.chinatax.gov.cn/art/2018/8/31/art_23636_1794.html','2018-08-31','A','居民全球所得；分类所得20%；国债利息免税；不能对全部NAV增长一刀切扣税'),
('foreign-tax','2020年第3号·境外所得','https://www.chinatax.gov.cn/chinatax/n810341/n810765/c101653/202001/c5149318/content.html','2020-01-17','A','分类计税及有上限的境外税额抵免；追溯适用2019不等于2019当时已知'),
('ashare-div','财税〔2015〕101号·股息持有期限','https://www.chinatax.gov.cn/n810341/n810755/c1797427/content.html','2015-09-07','A','2015-09-08施行；持股超过一年暂免，短期20%/10%；按取得日期而非固定30/365天'),
('hk-exemption','2023年第23号·港股通等个人所得税','https://fgk.chinatax.gov.cn/zcfgk/c102416/c5211076/content.html','2023-08-21','A','转让差价优惠延续至2027-12-31；不是股息免税'),
('fx-access','个人外汇管理办法','https://www.safe.gov.cn/safe/2022/0818/21330.html','2006-12-25','A','2007-02-01施行；经常/资本项目分开，境外金融投资通过有资格境内机构'),
('fx-use','外汇局个人购汇用途问答','https://www.safe.gov.cn/xiamen/file/file/20211022/f4794075e84e40dd9394be523a52731b.pdf','2021-10-22','A','购汇不得用于尚未开放的境外证券等资本项目；不是自由美股资金通道'),
('etf-lot','上交所ETF交易单位','https://www.sse.com.cn/assortment/fund/etf/question/c/c_20240118_5734754.shtml','2024-01-18','B','二级市场最低100份；不能把一级大额申购门槛当成全部零售交易门槛'),
('etf-tax','上交所50ETF交易解释','https://www.sse.com.cn/assortment/fund/etf/home/c/c_20151111_4011009.shtml','2015-11-11','B','该ETF二级交易不缴印花税；不能替代各产品完整税务核验'),
('513500-listed','513500 2015半年度报告','https://www.sse.com.cn/disclosure/fund/announcement/c/2015-08-26/513500_2015_z.pdf','2015-08-26','A','成立2013-12-05，上市2014-01-15'),
('513100-listed','国泰513100上市公告','https://www.gtfund.com/contents/2013/5/14-1ee92bc6e3b147699a40d612256a4873.html','2013-05-14','A','上市2013-05-15'),
('513100-fees','国泰513100费率页','https://www.gtfund.com/product/productlist/haiwai/513100/feilv/index.html',None,'A','当前页面管理0.6%托管0.2%；费率有效期未知，不回填2011'),
('513100-index','国泰513100概况','https://www.gtfund.com/product/productlist/haiwai/513100/summary/index.html',None,'A','纳指100经汇率调整总收益基准；不是ACWI；跟踪目标不是实现跟踪误差'),
('nav-fees','国泰513100基金详情','https://e.gtfund.com/etrade/Jijin/view/id/513100',None,'A','公告净值已扣管理托管等费用，不再次扣费'),
]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def capture(s):
 id,title,url,published,level,scope=s;p=D/'official'/f'{id}.raw';p.parent.mkdir(exist_ok=True)
 meta=dict(id=id,name=title,url=url,published_at=published,evidence_level=level,scope=scope,frequency='legal document / product disclosure',coverage=None,manual_processing=False,proxy=False,publicly_reviewable=True,original_sha256=None,downloaded_at=None,capture_status='NOT CAPTURED',publication_timestamp_verified=False)
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=15) as r:
   b=r.read(5_000_001);meta['http_status']=r.status;meta['content_type']=r.headers.get('Content-Type')
   if len(b)>5_000_000:raise ValueError('source exceeds capture limit')
   p.write_bytes(b);meta.update(original_sha256=sha(p),downloaded_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),capture_status='BYTES SAVED; content verified by official-page browsing; raw hash is not law validation',file=str(p.relative_to(ROOT)))
 except Exception as e:meta.update(downloaded_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),capture_status='CAPTURE FAILED; official text read via web retrieval',error=type(e).__name__+': '+str(e)[:200])
 return meta
protocol=dict(id='V3.2-CNY-AfterTax-2026-10-08',registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),investor=dict(tax_residence='CN-mainland',income_currency='CNY',liability_currency='CNY',capital_cny=100000,accounts=['mainland ordinary brokerage','domestic fund account'],offshore_accounts=False,offshore_funding=False,institutional_quota=False),freeze_hash='158affed1e0241a5e824bf5210d2a6ee4f328a015e86f0fdbfbcdfcf704e2f52',weights={'hs300-tr':.3,'world-proxy':.3,'china-treasury':.3,'gold':.1},strong={'world-proxy':.6,'china-treasury':.4},modes=['annual','semiannual','quarterly','absolute-5pp','relative-20pct','cashflow-only'],scenarios=[dict(id='A',name='Low Friction',trade_bp=5,minimum_cny=0,extra_product_bp=0,world_entry_premium=0,fx_friction_bp=0,hypothetical_gain_tax=0),dict(id='B',name='Normal Retail Stress',trade_bp=15,minimum_cny=5,extra_product_bp=25,world_entry_premium=.01,fx_friction_bp=0,hypothetical_gain_tax=0),dict(id='C',name='High Friction',trade_bp=50,minimum_cny=5,extra_product_bp=100,world_entry_premium=.05,fx_friction_bp=0,hypothetical_gain_tax=0),dict(id='D',name='Tax + FX + Product Stress ONLY',trade_bp=50,minimum_cny=5,extra_product_bp=100,world_entry_premium=.10,fx_friction_bp=50,hypothetical_gain_tax=.20)],scenario_evidence='D; illustrative incremental drag, not actual product fees/tax; D direct-FX friction is a conditional separate route, not default QDII retail fee',historical_start='2011-10-10',historical_end='2026-09-30',time_rule='historical proxy mark at 08:00 Asia/Shanghai uses previous publisher-local day for every input; source publication timestamps unknown; diagnostic only, never actual executable quote',initial_entry='second panel day using first day decision; no look-ahead',cashflow_scenario='500 CNY at first observed month change; TWR unit issuance isolates contributions',metric_rule='CAGR actual calendar years; weekly returns for vol/Sortino, MAR=0 assumed D; Sharpe and real CAGR null absent RF/CPI',selection='no rankings or chosen best rule; all predeclared cells exported',formal_aftertax='null until mapped actual products, dated tax rules, fees, quotes, distributions, access all validated')
path=D/'protocol.json'
if not path.exists():
 protocol['sha256']=hashlib.sha256(json.dumps(protocol,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();path.write_text(json.dumps(protocol,ensure_ascii=False,indent=2)+'\n')
if not (D/'data_sources.json').exists():
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:entries=list(pool.map(capture,SOURCES))
 (D/'data_sources.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
if not (O/'pre-change-inventory.json').exists():
 baseline=Path('/workspace/scratch/6281b0b9d5d7/project-preflight.json')
 if baseline.exists():shutil.copy2(baseline,O/'pre-change-inventory.json')
print(json.dumps({'protocol':json.loads(path.read_text())['sha256'],'official_sources':len(SOURCES),'archived_source_commit':'88c4dc17124851480ef988939333bc620d32deca'}))
