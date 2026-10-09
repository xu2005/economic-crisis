"""CNY after-tax implementability: dated validation and separately labelled proxy stress.
No optimiser. Real-product outputs are gated, never filled with index back-history.
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
import argparse,datetime,hashlib,json,math,shutil
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];D=R/'data/v32-cny';O=R/'reports/crisis-v32-cny'
class Blocked(ValueError):pass

def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def read(name):return json.loads((D/name).read_text())
def save(name,obj):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def csv(name,rows,columns=None):
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True);pd.DataFrame(rows,columns=columns).to_csv(target,index=False)
def aware(s):
 t=pd.Timestamp(s)
 if t.tzinfo is None:raise Blocked('timezone required')
 return t.tz_convert('UTC')
def known_at(record,cutoff):
 return max(aware(record['timestamp']),aware(record['observed_at']))<=aware(cutoff)
def investability(product,date,kind='PRODUCT_NAV'):
 if kind=='INDEX_BACKFILL':return 'RESEARCH ONLY / INDEX BACKFILL'
 start=product.get('listed')
 if start is None or str(date)[:10]<start:raise Blocked('ETF listing date absent or not reached')
 if not product.get('listing_verified'):raise Blocked('listing evidence not verified')
 return 'LISTED; further access / tax / liquidity validation required'
def mapping_status(product):
 required=['exact_mapping','legal_access','account_access','capital_access','product_access','liquidity_access','tax_validated','data_continuous','cost_validated']
 return 'IMPLEMENTABLE' if all(product.get(k) is True for k in required) else 'IMPLEMENTATION NOT VALIDATED'
def access_route(primary_open,secondary_open,premium,maximum=.03):
 # A verified secondary route can exist while primary creations are suspended.
 if secondary_open is True and premium is not None and math.isfinite(premium) and abs(premium)<=maximum:return 'SECONDARY ROUTE ONLY; other gates required'
 if primary_open is True:return 'PRIMARY ROUTE ONLY; minimum subscription and remaining gates required'
 return 'BLOCKED / UNKNOWN'
def premium(market,iopv):
 if market is None or iopv is None or not math.isfinite(market) or not math.isfinite(iopv) or market<=0 or iopv<=0:raise Blocked('synchronous market and reference NAV required')
 return market/iopv-1

def tax_rule(rules,category,event_date,knowledge_date=None):
 knowledge=knowledge_date or event_date
 valid=[r for r in rules if r['category']==category and r.get('verified') is True and r['evidence_level'] in ['A','B'] and r.get('published') and r['published']<knowledge and r['effective']<=event_date and (r.get('expires') is None or event_date<=r['expires'])]
 if len(valid)!=1:raise Blocked('TAX TREATMENT UNCERTAIN: '+category)
 return valid[0]
def tax_amount(rule,income,foreign_paid=0.,foreign_credit_eligible=False):
 if income<0:return 0. # no invented refund or cross-category loss offset
 tax=income*rule['rate']
 credit=min(tax,max(0.,foreign_paid)) if foreign_credit_eligible else 0.
 return tax-credit

def dividend_rate(rule,acquired,assessment_date):
 # Caller supplies disposition/settlement date for deferred short-held dividends.
 if assessment_date<acquired:raise Blocked('invalid holding period')
 a=pd.Timestamp(acquired);b=pd.Timestamp(assessment_date)
 if b>a+pd.DateOffset(years=1):return rule['tiers']['over_year']
 if b>a+pd.DateOffset(months=1):return rule['tiers']['month_to_year']
 return rule['tiers']['within_month']
def convert_cny(native,fx):
 if fx is None or not math.isfinite(fx) or fx<=0:raise Blocked('missing FX, never substitute zero/one')
 return native*fx

def fx_identity(native_start,native_end,fx_start,fx_end):
 c=convert_cny(native_end,fx_end)/convert_cny(native_start,fx_start);a=native_end/native_start;f=fx_end/fx_start
 return dict(asset_return=a-1,fx_return=f-1,interaction=(a-1)*(f-1),cny_return=c-1,residual=c-a*f)
def fx_conversion_cost(notional_cny,spread_bp,fixed=0.,route='DIRECT_FX'):
 if route=='DOMESTIC_CNY':return 0. # QDII fund conversion costs are in NAV, retail does not remit
 if not 0<=spread_bp<10000 or fixed<0:raise Blocked('invalid FX friction')
 return abs(notional_cny)*spread_bp/10000+fixed

def fee(notional,rate,minimum):return max(abs(notional)*rate,minimum) if abs(notional)>1e-10 else 0.
def product_layer(gross,annual_management,annual_custody,years,kind='GROSS_INDEX',tracking_drag=0.):
 if kind in ['PRODUCT_NAV','ADJUSTED_PRODUCT_NAV']:return gross
 return gross*math.exp(-(annual_management+annual_custody+tracking_drag)*years)
def aftertax_return(start,end,tax):
 if start<=0 or tax is None:raise Blocked('after-tax denominator or tax unknown')
 return (end-tax)/start-1

def validate_product_quote(q,product,cutoff):
 investability(product,q['timestamp'][:10],q['kind'])
 if q['kind'] not in ['PRODUCT_NAV','PRODUCT_PRICE']:raise Blocked('index cannot be INVESTABLE RETURN')
 if mapping_status(product)!='IMPLEMENTABLE':raise Blocked('mapping / tax / access / data gates unresolved')
 if not known_at(q,cutoff):raise Blocked('future or unobserved quote')
 for k in ['price','bid','ask','nav','fx']:
  if q.get(k) is None or not math.isfinite(q[k]) or q[k]<=0:raise Blocked('missing '+k)
 if q['ask']<q['bid']:raise Blocked('crossed quote')
 if not q.get('reference_at') or abs((aware(q['reference_at'])-aware(q['timestamp'])).total_seconds())>60:raise Blocked('NAV / IOPV timestamp mismatch')
 if not q.get('sha256') or len(q['sha256'])!=64:raise Blocked('raw evidence hash required')
 if q.get('status')!='TRADABLE':raise Blocked('market / product unavailable')
 return premium(q['price'],q['nav'])
def validate_execution(decision_at,execution):
 if aware(execution['executed_at'])<=aware(decision_at):raise Blocked('execution must be later than decision cutoff')
 if execution.get('price') is None or execution['price']<=0:raise Blocked('missing actual execution price')

def validate_series(frame):
 if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:raise Blocked('duplicate or unsorted dates')
 if frame.empty or not np.isfinite(frame.to_numpy(dtype=float)).all() or (frame<=0).any().any():raise Blocked('missing/nonpositive data; no backfill')

def due(mode,previous,date,weights,targets):
 if previous is None:return False
 old=pd.Timestamp(previous);new=pd.Timestamp(date)
 if mode in ['annual','semiannual','quarterly']:
  periods={'annual':12,'semiannual':6,'quarterly':3}[mode]
  return (old.year*12+old.month-1)//periods != (new.year*12+new.month-1)//periods
 if mode=='absolute-5pp':return bool(np.max(np.abs(weights-targets))>=.05)
 if mode=='relative-20pct':return bool(np.max(np.abs(weights/targets-1))>=.20)
 if mode=='cashflow-only':return False
 raise Blocked('unknown rebalance rule')

def cashflow_budgets(values,targets,cash):
 gap=np.maximum((values.sum()+cash)*targets-values,0.)
 return gap*(cash/gap.sum()) if gap.sum()>0 else np.zeros_like(values)

@dataclass(frozen=True)
class Friction:
 trade_bp:float=0
 minimum_cny:float=0
 extra_product_bp:float=0
 world_entry_premium:float=0
 fx_friction_bp:float=0
 hypothetical_gain_tax:float=0

def proxy_run(prices,observed,weights,mode='annual',f=Friction(),contribution=0.):
 """EXPLICIT PROXY STRESS. No real-product / statutory after-tax claim.
 Previous snapshot decides; pending orders wait for all currently observed marks.
 Input marks are already lagged to 08:00; assumes trading at marks for diagnostics.
 """
 validate_series(prices);assets=list(weights);p=prices[assets].copy();w=np.array(list(weights.values()))
 if not np.isclose(w.sum(),1.) or (w<=0).any():raise Blocked('invalid weights')
 q=np.zeros(len(w));basis=np.zeros(len(w));cash=100000.;navunits=100000.;contributed=100000.
 tradecost=fxcost=tax=expenses=premiumcost=turnover=0.;fills=[];curve=[];pending=None;last=None;last_values=None
 for i,(date,row) in enumerate(p.iterrows()):
  rawpx=row.to_numpy(float);dt=0 if last is None else (pd.Timestamp(date)-pd.Timestamp(last)).days/365.25
  elapsed=(pd.Timestamp(date)-pd.Timestamp(p.index[0])).days/365.25
  factor=math.exp(-f.extra_product_bp/10000*elapsed);px=rawpx*factor
  drag=float(q@rawpx)*factor*math.expm1(f.extra_product_bp/10000*dt);expenses+=drag # incremental hypothetical NAV drag; units conserved
  value=q*px;wealth=cash+float(value.sum());flow=0.
  if contribution and last and date[:7]!=last[:7]:
   flow=contribution;navunits+=flow/(wealth/navunits);cash+=flow;contributed+=flow
  joint=bool(observed.loc[date,assets].all())
  if pending is not None and joint:
   target=w*(cash+float(value.sum()))
   only_buys=mode=='cashflow-only' and i>1
   if only_buys:target=value+cashflow_budgets(value,w,cash)
   # Sell first. Aggregate average CNY tax basis; D synthetic gain tax not statutory.
   for j,a in enumerate(assets):
    delta=min(0.,target[j]-value[j]);units=-delta/px[j]
    if units<=1e-10:continue
    base=basis[j]*(units/q[j]);commission=fee(delta,f.trade_bp/10000,f.minimum_cny)
    friction=fx_conversion_cost(delta,f.fx_friction_bp,route='DIRECT_FX' if a in ['world-proxy','gold'] else 'DOMESTIC_CNY')
    proceeds=-delta-commission-friction;taxpaid=max(0.,proceeds-base)*f.hypothetical_gain_tax
    cash+=proceeds-taxpaid;q[j]-=units;basis[j]-=base
    tradecost+=commission;fxcost+=friction;tax+=taxpaid;turnover+=abs(delta)
    fills.append(dict(date=date,signal_at=pending,asset=a,side='sell',units=-units,price=px[j],notional=-delta,commission=commission,fx_friction=friction,premium_loss=0.,synthetic_tax=taxpaid,cash_flow=proceeds-taxpaid,cash_after=cash,layer='PROXY_STRESS'))
   value=q*px;budget=np.maximum(target-value,0.)
   # Plan all buy costs jointly; bisection prevents hidden overdraft / order bias.
   def costscale(scale):
    total=0.
    for j,a in enumerate(assets):
     b=budget[j]*scale
     if b<=1e-10:continue
     entry=f.world_entry_premium if i==1 and a=='world-proxy' else 0.
     n=b*(1+entry);total+=n+fee(n,f.trade_bp/10000,f.minimum_cny)+fx_conversion_cost(n,f.fx_friction_bp,route='DIRECT_FX' if a in ['world-proxy','gold'] else 'DOMESTIC_CNY')
    return total
   lo=0.;hi=1.
   for _ in range(50):
    mid=(lo+hi)/2
    if costscale(mid)>cash:hi=mid
    else:lo=mid
   for j,a in enumerate(assets):
    b=budget[j]*lo
    if b<=1e-9:continue
    entry=f.world_entry_premium if i==1 and a=='world-proxy' else 0.;n=b*(1+entry)
    commission=fee(n,f.trade_bp/10000,f.minimum_cny);friction=fx_conversion_cost(n,f.fx_friction_bp,route='DIRECT_FX' if a in ['world-proxy','gold'] else 'DOMESTIC_CNY');out=n+commission+friction
    units=b/px[j];q[j]+=units;basis[j]+=out;cash-=out;tradecost+=commission;fxcost+=friction;premiumcost+=n-b;turnover+=n
    fills.append(dict(date=date,signal_at=pending,asset=a,side='buy',units=units,price=px[j],notional=n,commission=commission,fx_friction=friction,premium_loss=n-b,synthetic_tax=0.,cash_flow=-out,cash_after=cash,layer='PROXY_STRESS'))
   pending=None
  if cash < -1e-6:raise AssertionError('cash overdraft')
  wealth=cash+float(q@px);v=q*px
  # Calendar/threshold decision uses this snapshot, trades only a later date.
  if i==0:pending=date
  elif due(mode,last,date,v/wealth,w):pending=pending or date
  elif mode=='cashflow-only' and flow:pending=pending or date
  curve.append(dict(date=date,equity=wealth,nav=wealth/navunits,cash=cash,total_contributions=contributed,external_flow=flow,unit_count=navunits,transaction_cost=tradecost,fx_friction=fxcost,synthetic_tax=tax,fund_extra_drag=expenses,premium_loss=premiumcost,**{f'value_{a}':float(v[j]) for j,a in enumerate(assets)}))
  last=date;last_values=v
 # Terminal liquidation cost/tax is separate, never falsely changes the daily NAV.
 liquidation_fee=liquidation_fx=liquidation_tax=0.;liquidation=[]
 for j,a in enumerate(assets):
  n=float(q[j]*px[j]);c=fee(n,f.trade_bp/10000,f.minimum_cny);fx=fx_conversion_cost(n,f.fx_friction_bp,route='DIRECT_FX' if a in ['world-proxy','gold'] else 'DOMESTIC_CNY');t=max(0.,n-c-fx-basis[j])*f.hypothetical_gain_tax
  liquidation_fee+=c;liquidation_fx+=fx;liquidation_tax+=t
  liquidation.append(dict(date=p.index[-1],asset=a,units=float(q[j]),mark_price=float(px[j]),gross_value=n,cost_basis=float(basis[j]),commission=c,fx_friction=fx,synthetic_tax=t,net_proceeds=n-c-fx-t,status='CONDITIONAL TERMINAL MARK LIQUIDATION; no next executable quote'))
 terminal=curve[-1]['equity']-liquidation_fee-liquidation_fx-liquidation_tax
 return dict(curve=curve,fills=fills,liquidation=liquidation,terminal=terminal,terminal_synthetic_tax=liquidation_tax,cumulative_transaction_cost=tradecost+liquidation_fee,cumulative_fx_friction=fxcost+liquidation_fx,cumulative_synthetic_tax=tax+liquidation_tax,fund_extra_drag=expenses,premium_loss=premiumcost,turnover_notional=turnover+float(q@px),contributions=contributed,terminal_basis=float(basis.sum()))

def kpi(run):
 c=pd.DataFrame(run['curve']);s=pd.Series(c.nav.to_numpy(),index=pd.to_datetime(c.date));years=(s.index[-1]-s.index[0]).days/365.25
 if years<=0:raise Blocked('window too short')
 dd=1-s/s.cummax();weekly=s.resample('W-FRI').last().dropna();ret=weekly.pct_change().dropna();down=np.minimum(ret,0);vol=float(ret.std(ddof=1)*np.sqrt(52)) if len(ret)>1 else None
 downside=float(np.sqrt(np.mean(np.square(down)))*np.sqrt(52)) if len(ret) else 0.
 cg=float(s.iloc[-1]**(1/years)-1);duration=0;peak=s.index[0];maxdur=0;recovered=[];episode_start=None
 for day,val in dd.items():
  if val<=1e-12:
   if episode_start is not None:recovered.append((day-episode_start).days);episode_start=None
   peak=day
  else:
   duration=(day-peak).days;maxdur=max(maxdur,duration);episode_start=episode_start or peak
 def worst(days):
  dates=s.index.to_numpy();values=s.to_numpy();idx=np.searchsorted(dates,dates-np.timedelta64(days,'D'),side='right')-1;mask=idx>=0
  if not mask.any():return None
  ratios=values[mask]/values[idx[mask]]
  if days>365:
   years=(dates[mask]-dates[idx[mask]])/np.timedelta64(1,'D')/365.25;ratios=ratios**(1/years)
  return float(np.min(ratios-1))
 crises=[]
 for begin,end in [('2015-06-01','2016-03-01'),('2018-01-01','2018-12-31'),('2020-02-01','2020-05-31'),('2021-01-01','2024-12-31')]:
  x=s.loc[begin:end]
  if len(x):crises.append(float((1-x/x.cummax()).max()))
 m=dict(proxy_cagr=cg,proxy_mdd=float(dd.max()),proxy_calmar=cg/float(dd.max()) if dd.max()>0 else None,annualised_volatility=vol,sortino_mar0=float(ret.mean()*52/downside) if downside>0 else None,ulcer=float(np.sqrt(np.mean(np.square(dd)))),max_drawdown_duration_days=maxdur,recovery_time_days=max(recovered) if recovered else None,unrecovered_since=episode_start.strftime('%Y-%m-%d') if episode_start is not None else None,time_under_water_fraction=float((dd>1e-12).mean()),worst_1y=worst(365),worst_3y=worst(1096),crisis_mdd=max(crises) if crises else None,turnover_annual=run['turnover_notional']/float(c.equity.mean())/years,trade_count=len(run['fills']),terminal_proxy_liquidated_cny=run['terminal'],proxy_liquidated_twr_cagr=(run['terminal']/c.equity.iloc[-1]*s.iloc[-1])**(1/years)-1,real_cagr=None,aftertax_cagr=None,sharpe=None,cumulative_transaction_cost=run['cumulative_transaction_cost'],cumulative_tax=None,cumulative_synthetic_tax=run['cumulative_synthetic_tax'],fx_friction=run['cumulative_fx_friction'],fund_expenses=None,incremental_product_drag=run['fund_extra_drag'],premium_loss=run['premium_loss'],tracking_error=None,fx_contribution=None,formal_aftertax_cny_wealth=None)
 return m

def historical_panel():
 # Never alter the old aligned panel. Separate diagnostic series shifts BOTH CN and US.
 src=R/'reports/crisis-v3/input/cross-asset-aligned.csv';audit=R/'reports/crisis-v3/input/cross-asset-alignment-audit.csv'
 x=pd.read_csv(src).set_index('date');a=pd.read_csv(audit).set_index('date')
 cols=['hs300-tr','world-proxy','china-treasury','gold'];p=x[cols].shift(1).iloc[1:].copy();p.columns=cols
 observed=pd.DataFrame({k:a['observed_'+k].shift(1).iloc[1:].astype(bool) for k in cols},index=p.index)
 # FX is NOT shifted twice: already embedded in foreign CNY marks before shifting.
 notes=dict(name='08:00 historical proxy diagnostic',input=str(src.relative_to(R)),sha256=hashlib.sha256(src.read_bytes()).hexdigest(),start=p.index[0],end=p.index[-1],rows=len(p),frequency='union of publisher-local trading dates; lag one panel row',adjustment='H00300 issuer TR; ACWI/GLD adjusted-close×CNYFX; H11006 convention unresolved',missing='old forward-filled nontrading marks for valuation only; joint observed flags required for hypothetical trade; no actual bid/ask',lookahead='prior publisher-local date only; no reconstructed historical publication/observed timestamp; revision bias unresolved',coverage_note='end 2026-09-30 diagnostic contains at most prior-local-date source closes; it is not the original V3 NAV',manual_processing=False,proxy=True,publicly_reviewable=True)
 return p,observed,x,notes

def main():
 O.mkdir(parents=True,exist_ok=True);config=read('protocol.json');raw={k:v for k,v in config.items() if k!='sha256'}
 if digest(raw)!=config['sha256']:raise Blocked('registered protocol changed')
 products=read('products.json');rules=read('tax_rules.json');sources=read('data_sources.json')
 p,observed,old,prov=historical_panel();models=[('china100','100%中国股票（H00300理论）',{'hs300-tr':1.}),('china60','中国股票60%＋中国国债40%',{'hs300-tr':.6,'china-treasury':.4}),('global60','强基准：全球股票60%＋中国国债40%',config['strong']),('v3','冻结V3：30/30/30/10',config['weights'])]
 summary=[];curves=[];complexity=[]
 for scenario in config['scenarios']:
  f=Friction(**{k:v for k,v in scenario.items() if k not in ['id','name']})
  for id,label,w in models:
   for mode in config['modes']:
    run=proxy_run(p,observed,w,mode,f);metrics=kpi(run);key=f'{id}-{scenario["id"]}-{mode}'
    row=dict(id=id,label=label,scenario=scenario['id'],mode=mode,layer='PROXY_STRESS / INDEX BACKFILL',**metrics);summary.append(row)
    csv(f'curves/{key}.csv',run['curve']);csv(f'liquidations/{key}.csv',run['liquidation']);csv(f'ledgers/{key}.csv',run['fills'],['date','signal_at','asset','side','units','price','notional','commission','fx_friction','premium_loss','synthetic_tax','cash_flow','cash_after','layer'])
    if mode=='annual':
     n=np.array([z['nav'] for z in run['curve']]);dd=1-n/np.maximum.accumulate(n);indices=sorted(set(range(0,len(n),10))|{int(np.argmax(dd)),len(n)-1})
     curves.append(dict(id=id,scenario=scenario['id'],data=[dict(date=run['curve'][i]['date'],nav=float(n[i]),drawdown=float(dd[i])) for i in indices]))
  for mode in config['modes']:
   a=next(r for r in summary if r['id']=='v3' and r['scenario']==scenario['id'] and r['mode']==mode);b=next(r for r in summary if r['id']=='global60' and r['scenario']==scenario['id'] and r['mode']==mode)
   complexity.append(dict(scenario=scenario['id'],mode=mode,proxy_cagr_delta=a['proxy_cagr']-b['proxy_cagr'],proxy_mdd_delta=a['proxy_mdd']-b['proxy_mdd'],turnover_delta=a['turnover_annual']-b['turnover_annual'],transaction_cost_delta=a['cumulative_transaction_cost']-b['cumulative_transaction_cost'],actual_aftertax_risk_adjusted_delta=None,extra_assets=2,extra_accounts=0,retail_currencies=1,underlying_currency_risk='multiple; not equal to quotation currency',qualitative='V3增加中国股票与黄金产品维护；两者都依赖未批准全球映射及国债口径；暂无可重复的真实税后增量价值'))
 cashflows=[]
 for id,label,w in models:
  sc=config['scenarios'][1];f=Friction(**{k:v for k,v in sc.items() if k not in ['id','name']})
  run=proxy_run(p,observed,w,'cashflow-only',f,500);cashflows.append(dict(id=id,label=label,scenario='B',contributed_cny=run['contributions'],net_profit_cny=run['terminal']-run['contributions'],return_definition='TWR; external contributions buy units before investment; not terminal / initial CAGR',**kpi(run)));csv(f'curves/{id}-cashflow500.csv',run['curve']);csv(f'ledgers/{id}-cashflow500.csv',run['fills']);csv(f'liquidations/{id}-cashflow500.csv',run['liquidation'])
 formal=[]
 for id,label,w in models+[('v32-candidate','V3.2大陆候选（相同冻结权重，全球腿未映射）',config['weights'])]:
  formal.append(dict(id=id,label=label,status='FREEZE / IMPLEMENTATION BLOCKED',aftertax_cagr=None,real_cagr=None,wealth_aftertax_cny=None,reason='完整真实产品NAV/分红/同步 bid-ask/费率历史/税务适用/实际可得性未齐备；候选不是静默换成S&P500或511010'))
 fx=[]
 for asset in ['world-proxy','gold']:
  native0=float(old[asset].iloc[0]/old.fx.iloc[0]);native1=float(old[asset].iloc[-1]/old.fx.iloc[-1]);fx.append(dict(asset=asset,**fx_identity(native0,native1,float(old.fx.iloc[0]),float(old.fx.iloc[-1])),fx_friction=None,note='frozen legacy end-point identity, not portfolio dollar attribution'))
 premiums=[dict(premium=t,exit_premium=0.,world_v3_loss=100000*.3*t/(1+t),world_strong_loss=100000*.6*t/(1+t),flag='WARNING' if t>=.01 else 'BASE') for t in [0,.01,.03,.05,.10]]
 assumptions=[dict(id='A'+str(i+1),text=t,evidence='D',impact=impact) for i,(t,impact) in enumerate([
 ('压力费用5/15/50bp、最低0/5元、额外0/25/100bp；未核实券商报价','不得解释真实费用或真实税后收益'),('代理基金已含费用，额外损耗仅为假设复制差；产品NAV不再扣管理托管或跟踪损耗','防止双重扣费'),('场景D20%税仅为所有代理已实现正利得压力；不代表境内基金税率、不是直接境外完整税表','cumulative_tax及aftertax_cagr正式字段保持空'),('场景D美元换汇50bp仅独立DIRECT_FX假设路径，境内人民币QDII零售直接换汇为0','QDII基金内部摩擦已在净值中；不捏造个人汇款成本'),('现金残余收益0；Sortino MAR=0；缺RF/CPI不输出Sharpe/Real CAGR','非真实无风险现金序列'),('全部指数历史只作研究；前一发布者本地日估值不是次日真实成交','源发布时间/修订偏差仍待验证'),('再平衡规则全部预登记；无最优规则或权重排名','不把样本收益差作为调参依据'),('现金流实验每月500元，TWR单位化；理论分红调整价格不再重复加股息','实际分红净值+现金事件需要另齐')])]
 blockers=['ACWI严格大陆映射未批准','H11006与N11006收益口径未对账','511010久期与全期限国债不等价','2011产品成立/上市前收益不可实施','真实基金净值与现金分红完整序列缺失','实际同步价格/IOPV/买卖价差与QDII可得性历史缺失','当前费率披露没有完整历史生效段','税收原文核实与特定QDII/黄金产品适用仍须分开','账户佣金/税务及申赎确认未验证','官方CPI及完整可比无风险曲线未齐；Real CAGR/Sharpe空','共同08:00信息集、真实成交及冻结长期OOS仍不足']
 sources=read('data_sources.json') # final evidence register, independent from experiment inputs
 previous=json.loads((R/'reports/crisis-v31/results.json').read_text());archive=json.loads((O/'archive/qualification-2026-10-08/archive-receipt.json').read_text())
 result=dict(version='V3.2 CNY After-Tax Study',verdict='FREEZE / IMPLEMENTATION BLOCKED',implementation_answer='DATA INSUFFICIENT: 暂时无法判断复杂全球配置是否在大陆人民币税后仍值得实施；不将未知税费当0。',registered=config,investor=config['investor'],historical_frozen=previous['historicalSummary'],rolling=previous['rolling'],previous_costs=previous['costStress'],archive=archive,products=products,tax_rules=rules,sources=sources,assumptions=assumptions,proxy_summary=summary,proxy_curves=curves,formal_results=formal,cashflow_experiments=cashflows,complexity=complexity,fx=fx,premium_stress=premiums,blockers=blockers,provenance=prov,status_definitions={'FREEZE':'研究权重/强基准冻结，不因样本调规则','IMPLEMENTATION BLOCKED':'任何关键税务/映射/准入/数据/执行门槛失败或未知','RESEARCH VALID':'研究数据与口径复核通过；不自动代表可实施（当前H11006仍有条件）','IMPLEMENTATION NOT VALIDATED':'候选研究存在，产品应用证据未齐','PARTIALLY IMPLEMENTABLE':'独立产品路径全部关键门槛获证，完整组合未通过；本轮尚未授予','IMPLEMENTABLE':'全部腿严格映射，上市日期、五项准入、费用/税务适用、连续时点数据与成交可执行性均有A/B证据'})
 from build_cny_evidence import enrich_results
 enrich_results(result)
 save('results.json',result);save('protocol.json',config);save('products.json',products);save('tax_rules.json',rules);save('data_sources.json',sources+read('column_provenance.json')+[prov]);save('assumptions.json',assumptions)
 csv('proxy-stress-summary.csv',summary);csv('formal-aftertax-results.csv',formal);csv('complexity.csv',complexity);csv('cashflow-experiments.csv',cashflows);csv('fx-attribution.csv',fx);csv('premium-stress.csv',premiums)
 csv('product-mapping.csv',[{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in x.items()} for x in products]);csv('tax-rules.csv',[{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in x.items()} for x in rules])
 print(json.dumps(dict(proxy_experiments=len(summary),cashflow_experiments=len(cashflows),formal_aftertax_valid=0,verdict=result['verdict']),ensure_ascii=False))
if __name__=='__main__':main()
