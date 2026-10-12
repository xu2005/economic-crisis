"""Offline PRICE_ONLY audit; never requests data and never generates spread signals."""
import csv, json, struct, math, statistics, hashlib, argparse
from pathlib import Path
from datetime import date

DIVISOR={'510300':1000,'511010':1000,'159307':1000,'000300':100}
def decode(path,code):
    b=Path(path).read_bytes()
    if not b or len(b)%32: raise ValueError('Invalid 32-byte record length')
    rows=[]; prior=None
    for i in range(0,len(b),32):
        d,o,h,l,c,amount,v,res=struct.unpack('<IIIIIfII',b[i:i+32])
        ds=f'{d:08d}'; dt=date(int(ds[:4]),int(ds[4:6]),int(ds[6:8]))
        if dt>date.today() or dt.weekday()>4 or (prior and dt<=prior): raise ValueError(f'Date/order error: {dt}')
        if not 0<l<=min(o,c)<=max(o,c)<=h: raise ValueError(f'OHLC error: {dt}')
        if not math.isfinite(amount) or amount<0: raise ValueError('Invalid amount')
        prior=dt; scale=DIVISOR[code]
        rows.append(dict(date=dt.isoformat(),open=o/scale,high=h/scale,low=l/scale,close=c/scale,volume_raw=v,amount_raw=amount,source='LOCAL_TDX_PRICE',price_adjustment='UNADJUSTED',quality_flag='STRUCTURAL_PASS_CALENDAR_UNVERIFIED'))
    return rows
def writecsv(p,rows):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    if not rows:return
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def metrics(values):
    returns=[b/a-1 for a,b in zip(values,values[1:])]
    peak=values[0]; dd=0
    for v in values: peak=max(peak,v);dd=min(dd,v/peak-1)
    return dict(price_return=values[-1]/values[0]-1,max_drawdown=dd,daily_volatility=statistics.stdev(returns) if len(returns)>1 else None)
def buy_hold(rows,budget=100000.,fee_bps=0,slippage_bps=0,lot=100):
    if budget<=0 or lot<=0 or fee_bps<0 or slippage_bps<0:raise ValueError('Invalid assumptions')
    f=fee_bps/10000;s=slippage_bps/10000;p=rows[0]['open']*(1+s)
    n=math.floor(budget/(p*(1+f))/lot)*lot;fee=n*p*f;cash=budget-n*p-fee
    if cash<-.000001:raise ValueError('Cash overdraft')
    ledger=[dict(date=r['date'],units=n,cash=cash,receivable=0,dividend_cash=0,close=r['close'],equity=cash+n*r['close'],fee=fee if i==0 else 0,trade_count=1 if i==0 and n else 0,evidence='ASSUMPTION_SCENARIO') for i,r in enumerate(rows)]
    return ledger,dict(start_equity=budget,end_equity=ledger[-1]['equity'],return_on_initial_cash=ledger[-1]['equity']/budget-1,fees=fee,turnover=n*p/budget,trades=int(n>0),fee_bps=fee_bps,slippage_bps=slippage_bps,lot=lot,end_liquidated=False)
def signal_action(spread):
    if spread is None or not math.isfinite(spread):raise ValueError('SIGNAL_UNAVAILABLE')
    if spread<1:return 'SELL'
    if spread>3:return 'DOUBLE'
    if spread>1.5:return 'NORMAL'
    return 'HOLD'
def dividend_scenario(rows,events,budget=100000.,fee_bps=5,slippage_bps=5,lot=100):
    """Assume payment-day end credit; reinvest on next observed trading-day open.
    Candidates are never certified. Record-date units determine entitlements.
    """
    keys=[e['ex_date'] for e in events]
    if len(set(keys))!=len(keys):raise ValueError('Duplicate dividend event')
    for e in events:
        if not e['record_date']<=e['ex_date']<=e['declared_payment_date'] or e['cash_per_share']<0:raise ValueError('Invalid dividend')
    base,m=buy_hold(rows,budget,fee_bps,slippage_bps,lot)
    n=base[0]['units'];cash=base[0]['cash'];fee=m['fees'];trades=int(n>0)
    ent={}; receivables={};paid=set();ledger=[];fills=[dict(date=rows[0]['date'],side='BUY',units=n,reason='ASSUMPTION_INITIAL_OPEN',fee=fee)]
    covered={r['date'] for r in rows}; skipped=[e['ex_date'] for e in events if e['record_date'] not in covered]
    for i,r in enumerate(rows):
        d=r['date']; credit=0;day_fee=fee if i==0 else 0
        for e in events:
            key=e['ex_date']
            if key in receivables and key not in paid and d>e['declared_payment_date']:
                amount=receivables.pop(key);cash+=amount;credit+=amount;paid.add(key)
        if credit:
            price=r['open']*(1+slippage_bps/10000);f=fee_bps/10000
            buy=math.floor(cash/(price*(1+f))/lot)*lot
            if buy:
                cost=buy*price;charge=cost*f;cash-=cost+charge;n+=buy;fee+=charge;day_fee+=charge;trades+=1
                fills.append(dict(date=d,side='BUY',units=buy,reason='ASSUMPTION_NEXT_OBSERVED_OPEN_AFTER_PAYMENT',fee=charge))
        for e in events:
            if e['record_date']==d:ent[e['ex_date']]=n*e['cash_per_share']
            if e['ex_date']==d and e['ex_date'] in ent:receivables[e['ex_date']]=ent[e['ex_date']]
        if cash<-.000001:raise ValueError('Cash overdraft')
        receivable=sum(receivables.values())
        ledger.append(dict(date=d,units=n,cash=cash,receivable=receivable,dividend_cash=credit,fee=day_fee,equity=cash+n*r['close']+receivable,evidence='ASSUMPTION_SCENARIO_SECONDARY_DIVIDENDS'))
    return ledger,fills,dict(return_on_initial_cash=ledger[-1]['equity']/budget-1,fees=fee,trades=trades,credited_events=len(paid),skipped_record_dates=skipped,actual_credit_verified=False)
def run(root):
    root=Path(root); allrows={}; audit=[]; summary=[]
    for code in DIVISOR:
        paths=list((root/'raw'/'local_vipdoc').glob(f'*{code}.day'))
        if len(paths)!=1:raise ValueError('Exactly one isolated file expected')
        p=paths[0];rows=decode(p,code);allrows[code]=rows
        writecsv(root/'normalized'/f'{code}.csv',rows)
        gaps=[dict(after=a['date'],before=b['date'],calendar_days=(date.fromisoformat(b['date'])-date.fromisoformat(a['date'])).days) for a,b in zip(rows,rows[1:]) if (date.fromisoformat(b['date'])-date.fromisoformat(a['date'])).days>4]
        jumps=[dict(date=b['date'],close_change=b['close']/a['close']-1) for a,b in zip(rows,rows[1:]) if abs(b['close']/a['close']-1)>.1]
        writecsv(root/'results'/f'{code}_calendar_gaps.csv',gaps)
        writecsv(root/'results'/f'{code}_large_moves.csv',jumps)
        m=metrics([r['close'] for r in rows]);summary.append(dict(code=code,type='PRICE_ONLY',evidence='LOCAL_TDX_PRICE',start=rows[0]['date'],end=rows[-1]['date'],rows=len(rows),**m))
        curve=[];peak=1
        for r in rows:
            x=r['close']/rows[0]['close'];peak=max(peak,x)
            curve.append(dict(date=r['date'],close=r['close'],price_index=x,drawdown=x/peak-1,evidence='LOCAL_TDX_PRICE'))
        writecsv(root/'results'/f'{code}_price_curve.csv',curve)
        audit.append(dict(code=code,market='sz' if code=='159307' else 'sh',raw_file=p.relative_to(root).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),start=rows[0]['date'],end=rows[-1]['date'],rows=len(rows),divisor=DIVISOR[code],price_adjustment='UNADJUSTED',ohlc_pass=True,unique_ordered_dates=True,weekdays_pass=True,future_dates=0,large_moves=len(jumps),calendar_gaps_over_4_days=len(gaps),calendar_coverage='UNKNOWN_NO_OFFICIAL_CALENDAR',history_status='PARTIAL_HISTORY',evidence='LOCAL_TDX_PRICE',volume_unit='UNVERIFIED_RAW',redistribution='LOCAL_ONLY'))
    sensitivity=[]
    for code in ['510300','511010','159307']:
        for bps in [0,5,10]:
            ledger,m=buy_hold(allrows[code],fee_bps=bps,slippage_bps=bps)
            writecsv(root/'results'/f'{code}_assumption_{bps}bps_ledger.csv',ledger)
            sensitivity.append(dict(code=code,type='ASSUMPTION_BUY_FIRST_OPEN_HOLD',evidence='ASSUMPTION_SCENARIO',start=allrows[code][0]['date'],end=allrows[code][-1]['date'],**m))
    # Domestic 60/40 is illustrative, not frozen V3.x or global strong benchmark.
    a={r['date']:r for r in allrows['510300']};b={r['date']:r for r in allrows['511010']}; dates=sorted(a.keys()&b.keys())
    x=a[dates[0]]['close'];y=b[dates[0]]['close']
    portfolio=[dict(date=d,price_index=.6*a[d]['close']/x+.4*b[d]['close']/y,evidence='ASSUMPTION_SCENARIO',type='ILLUSTRATIVE_DOMESTIC_60_40') for d in dates]
    writecsv(root/'results'/'illustrative_domestic_60_40_curve.csv',portfolio)
    summary.append(dict(code='ILLUSTRATIVE_DOMESTIC_60_40',type='ASSUMPTION_SCENARIO',evidence='ASSUMPTION_SCENARIO',start=dates[0],end=dates[-1],rows=len(dates),**metrics([r['price_index'] for r in portfolio])))
    writecsv(root/'results'/'price_metrics.csv',summary);writecsv(root/'results'/'fee_sensitivity.csv',sensitivity)
    (root/'reports'/'price_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    return summary
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(Path(__file__).resolve().parent));a=p.parse_args()
    print(json.dumps(run(a.root),ensure_ascii=False,indent=2))
