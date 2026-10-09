import { ladder, validate, anchorDrawdown, type PyramidParameters, type Allocation } from './engine';

export interface Bar { date: string; open: number; high: number; low: number; close: number; }
export interface BacktestConfig {
  parameters: PyramidParameters;
  allocation: Allocation | 'lump';
  anchor: 'running-high' | 'initial-close';
  commissionBps: number;
  slippageBps: number;
}
export interface Fill { level: number; threshold: number; signalDate: string | null; date: string; triggerDrawdown: number; budget: number; open: number; price: number; units: number; fee: number; cashAfter: number; }
export interface Point { date: string; equity: number; cash: number; units: number; invested: number; drawdown: number; anchor: number; triggerDrawdown: number; }
export interface BacktestResult {
  config: BacktestConfig; fills: Fill[]; curve: Point[]; pendingLevels: number[];
  metrics: { finalValue: number; totalReturn: number; cagr: number; maxDrawdown: number; cash: number; spent: number; fees: number; avgExposure: number; filledLevels: number; firstFill: string | null; lastFill: string | null; };
}
function validBars(bars: Bar[]) {
  if (!bars.length) throw new Error('至少需要一条行情。');
  bars.forEach((b, i) => {
    const time = new Date(b.date + 'T00:00:00Z');
    if (!/^\d{4}-\d{2}-\d{2}$/.test(b.date) || !Number.isFinite(time.getTime()) || time.toISOString().slice(0, 10) !== b.date || (i && bars[i-1].date >= b.date)) throw new Error('日期必须真实、唯一并严格递增。');
    if (![b.open,b.high,b.low,b.close].every(v => Number.isFinite(v) && v > 0) || b.low > Math.min(b.open,b.close) || b.high < Math.max(b.open,b.close)) throw new Error('行情必须为有效正数OHLC。');
  });
}
/** Research baseline only: one capital pool, once per tier, close signal / next open,
 * high-water anchor starts at first close, no selling, resetting, gates, or dividends.
 * Fee is included in each tier's budget; fractional index units are a price proxy.
 */
export function backtest(asset: Bar[], trigger: Bar[], config: BacktestConfig): BacktestResult {
  validBars(asset); validBars(trigger);
  if (asset.length !== trigger.length || asset.some((b,i) => b.date !== trigger[i].date)) throw new Error('标的与触发指数的交易日期须完全对齐。');
  const error = validate(config.parameters); if (error) throw new Error(error);
  if (!['power','equal','geometric','lump'].includes(config.allocation) || !['running-high','initial-close'].includes(config.anchor)) throw new Error('未知回测规则。');
  if (![config.commissionBps,config.slippageBps].every(x => Number.isFinite(x) && x >= 0 && x <= 1000)) throw new Error('费用与滑点范围为0–1000基点。');
  const p = config.parameters;
  const levels = config.allocation === 'lump' ? [] : ladder(p,config.allocation);
  let cash = p.capital, units = 0, spent = 0, fees = 0, peak = p.capital, anchor = trigger[0].close;
  const fills: Fill[] = [], curve: Point[] = [], used = new Set<number>();
  let pending: { level: number; threshold: number; signalDate: string; drawdown: number; budget: number }[] = [];
  const execute = (b: Bar, order: {level: number; threshold: number; signalDate: string | null; drawdown: number; budget: number}) => {
    const budget = order.budget;
    if (budget <= 0) return;
    if (budget > cash + 1e-7) throw new Error('预算超出现金。');
    const price = b.open * (1 + config.slippageBps / 10000);
    const notional = budget / (1 + config.commissionBps / 10000);
    const added = notional / price, fee = budget - notional;
    cash -= budget; if (Math.abs(cash) < 1e-8) cash = 0;
    spent += budget; units += added; fees += fee;
    fills.push({level:order.level,threshold:order.threshold,signalDate:order.signalDate,date:b.date,triggerDrawdown:order.drawdown,budget,open:b.open,price,units:added,fee,cashAfter:cash});
  };
  asset.forEach((b,i) => {
    // Orders are frozen at the preceding close. Current close never selects its open fills.
    for (const order of pending) execute(b,order);
    pending = [];
    if (i === 0 && config.allocation === 'lump') execute(b,{level:0,threshold:0,signalDate:null,drawdown:0,budget:p.capital * p.deployment / 100});
    if (config.anchor === 'running-high') anchor = Math.max(anchor,trigger[i].close);
    const d = anchorDrawdown(anchor,trigger[i].close);
    for (const row of levels) {
      if (!used.has(row.level) && row.drawdown <= d + 1e-10) {
        used.add(row.level);
        if (row.increment > 0) pending.push({level:row.level,threshold:row.drawdown,signalDate:b.date,drawdown:d,budget:row.increment});
      }
    }
    const invested = units * b.close, equity = cash + invested;
    peak = Math.max(peak,equity);
    curve.push({date:b.date,equity,cash,units,invested,drawdown:1-equity/peak,anchor,triggerDrawdown:d});
    if (cash < -1e-7 || Math.abs(cash + spent - p.capital) > 1e-6 || spent > p.capital * p.deployment/100 + 1e-6) throw new Error('资金守恒校验失败。');
  });
  const final = curve.at(-1)!;
  const years = (new Date(final.date).getTime()-new Date(curve[0].date).getTime()) / (365.2425*86400000);
  return {config,fills,curve,pendingLevels:pending.map(x=>x.level),metrics:{
    finalValue:final.equity,totalReturn:final.equity/p.capital-1,cagr:years>0?(final.equity/p.capital)**(1/years)-1:0,
    maxDrawdown:Math.max(...curve.map(x=>x.drawdown)),cash,spent,fees,avgExposure:curve.reduce((s,x)=>s+x.invested/x.equity,0)/curve.length,
    filledLevels:fills.length,firstFill:fills[0]?.date??null,lastFill:fills.at(-1)?.date??null,
  }};
}
