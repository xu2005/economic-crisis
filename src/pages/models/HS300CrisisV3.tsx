import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Badge, Button, Spinner } from '@fluentui/react-components';
import type { EChartsOption } from 'echarts';
import Chart from '../../components/Chart';
import { Notice, PageHeading, PrintButton, num } from '../../components/common';

type Row = Record<string, any>;
const pct = (v: number) => `${num(v * 100, 2)}%`;
const mainIds = ['v3-balanced', 'hs300-tr', 'china60-bond40', 'global60-bond40'];

function MetricTable({ rows }: { rows: Row[] }) {
  return <div className="table-scroll" tabIndex={0}><table><thead><tr><th>方案</th><th>CAGR</th><th>最大回撤</th><th>Calmar</th><th>Sortino</th><th>Ulcer</th><th>最长水下</th><th>期末财富</th></tr></thead><tbody>{rows.map(r => <tr key={r.id}><th>{r.label}</th><td>{pct(r.cagr)}</td><td>{pct(r.maxDrawdown)}</td><td>{num(r.calmar, 3)}</td><td>{num(r.sortino, 3)}</td><td>{pct(r.ulcer)}</td><td>{r.longestUnderwaterCalendarDays}日</td><td>¥{num(r.finalValue, 0)}</td></tr>)}</tbody></table></div>;
}

function V3Viewer({ data }: { data: Row }) {
  const byId = Object.fromEntries(data.summary.map((r: Row) => [r.id, r]));
  const main = mainIds.map(id => byId[id]);
  const equity = useMemo<EChartsOption>(() => ({
    tooltip: { trigger: 'axis' }, legend: { top: 0 }, grid: { left: 12, right: 12, top: 78, bottom: 50, containLabel: true },
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 4 }],
    xAxis: { type: 'category', data: data.curves['v3-balanced'].map((r: Row) => r[0]), axisLabel: { hideOverlap: true, formatter: (s: string) => s.slice(0, 4) } },
    yAxis: { type: 'value', name: '总资产／元' },
    series: mainIds.map(id => ({ name: byId[id].label, type: 'line', showSymbol: false, data: data.curves[id].map((r: Row) => r[1]), lineStyle: { width: id === 'v3-balanced' ? 3 : 2 } })),
  }), [data, byId]);
  const drawdown = useMemo<EChartsOption>(() => ({
    tooltip: { trigger: 'axis' }, legend: { top: 0 }, grid: { left: 12, right: 12, top: 78, bottom: 35, containLabel: true },
    xAxis: { type: 'category', data: data.curves['v3-balanced'].map((r: Row) => r[0]), axisLabel: { hideOverlap: true, formatter: (s: string) => s.slice(0, 4) } },
    yAxis: { type: 'value', name: '回撤／%' },
    series: mainIds.map(id => ({ name: byId[id].label, type: 'line', showSymbol: false, data: data.curves[id].map((r: Row) => -r[2] * 100) })),
  }), [data, byId]);
  const rolling = useMemo<EChartsOption>(() => {
    const rows = data.rolling.filter((r: Row) => r.strategy === 'v3-balanced');
    return { tooltip: { trigger: 'axis' }, legend: { top: 0 }, grid: { left: 12, right: 12, top: 70, bottom: 35, containLabel: true }, xAxis: { type: 'category', data: rows.map((r: Row) => r.startMonth), axisLabel: { hideOverlap: true } }, yAxis: { type: 'value', name: 'V3 CAGR差／百分点' }, series: [['v3MinusHs300Cagr', '相对沪深300全收益'], ['v3MinusChina60Cagr', '相对中国60/40'], ['v3MinusGlobal60Cagr', '相对全球60/40']].map(([key, name]) => ({ name, type: 'line', showSymbol: false, data: rows.map((r: Row) => r[key] * 100), markLine: { silent: true, data: [{ yAxis: 0 }] } })) } as EChartsOption;
  }, [data]);
  const tr = data.v2TotalReturnEvidence;
  const files = [['REPORT.md', 'V3完整报告'], ['MODEL_SPEC.md', '冻结模型规格'], ['full-review.zip', '完整复核 ZIP'], ['summary.csv', '核心指标 CSV'], ['v3-balanced-curve.csv', 'V3每日净值'], ['v3-balanced-fills.csv', 'V3逐笔账本'], ['rolling-starts.csv', '111个滚动起点'], ['module-decisions.csv', '模块处置清单'], ['data-quality.json', '数据质量'], ['test-report.json', '测试结果'], ['manifest.json', 'SHA-256清单'], ['results.json', '机器可读结果'], ['reproduce.py', '离线复现入口']];
  return <>
    <div className="tag-row"><Badge color="warning" appearance="tint">Verdict {data.verdict}</Badge><Badge appearance="tint">固定风险预算</Badge><Badge appearance="tint">不使用杠杆</Badge><Badge color="warning" appearance="tint">非实盘建议</Badge></div>
    <Notice title="V3历史结果已冻结；可实施性存在未决项">H11006与N11006利息再投资口径、跨时区成交、大陆产品映射和当日QDII限制尚未验证。7.95%不是已验证实盘收益。<Link to="/models/hs300/crisis-freeze">查看V3.1实盘可实施性审计与样本外预登记</Link></Notice>
    <Notice title="结论：退役复杂状态机">V2的Verdict C不支持继续维护多状态择时。V3改为30%沪深300全收益、30%全球股票、30%中国国债、10%黄金的年度固定风险预算。它是新的研究基准，不是历史最优权重。</Notice>
    <Notice title="一个不利但必须保留的结果">V3在111个滚动起点中只在8个窗口跑赢全球60/40，CAGR差中位数为{pct(data.rollingVerdict.medianVsGlobal60)}。因此V3的国内权益与黄金配置体现约束和分散，不是为了让回测收益最高。</Notice>

    <section className="model-section"><h2>1. Verdict 与核心指标</h2><div className="v2-summary">{main.map((r: Row) => <article className="v2-summary-card" key={r.id}><h3>{r.label}</h3><dl><div><dt>CAGR</dt><dd>{pct(r.cagr)}</dd></div><div><dt>最大回撤</dt><dd>{pct(r.maxDrawdown)}</dd></div><div><dt>Calmar</dt><dd>{num(r.calmar, 3)}</dd></div><div><dt>最长水下</dt><dd>{r.longestUnderwaterCalendarDays}日</dd></div></dl><p>期末 ¥{num(r.finalValue, 0)}</p></article>)}</div><MetricTable rows={main}/><p>V3最大回撤{pct(byId['v3-balanced'].maxDrawdown)}，低于旧危机模型约37.86%的风险上限；按规则保持无杠杆，不把它放大为“精确等回撤”。</p></section>

    <section className="model-section"><h2>2. V3冻结规则</h2><div className="v3-allocation"><article><strong>30%</strong><span>沪深300全收益</span><small>中国权益</small></article><article><strong>30%</strong><span>ACWI含分红代理</span><small>全球权益</small></article><article><strong>30%</strong><span>中国国债 H11006</span><small>久期防守，非现金</small></article><article><strong>10%</strong><span>GLD复权代理</span><small>黄金分散</small></article></div><p>每年在所有持仓成分均有真实报价的首个共同收盘再平衡；休市日的向前沿用报价只用于估值，不用于成交。没有PB、ERP、速率、锚点、危机标签或退出状态。</p></section>

    <section className="model-section"><h2>3. 净值与回撤</h2><Chart title="同一笔10万元的长期净值" question="人民币口径；跨境税费与真实产品映射尚未验证。" option={equity} fallback="V3、沪深300全收益、中国60/40与全球60/40的完整净值见CSV。" height={370}/><Chart title="回撤路径" question="最大回撤之外，同时比较Ulcer与水下持续时间。" option={drawdown} fallback="V3最大回撤18.36%，最长水下770自然日。" height={320}/><MetricTable rows={[byId['v3-balanced'], byId['v3-balanced-drift'], byId['v3-balanced-cost20']]}/><p>单边20bp压力使期末财富减少约¥{num(byId['v3-balanced'].finalValue - byId['v3-balanced-cost20'].finalValue, 0)}；税费、汇兑与各市场真实佣金仍未验证。</p></section>

    <section className="model-section"><h2>4. 111个滚动起点</h2><p>2011-10至2020-12，每月选择四类资产均有真实报价的首日，持有到2026-09-30。窗口重叠且长度不同，不作独立显著性检验。</p><Chart title="V3相对三个简单基准的CAGR差" question="零线以下表示V3落后。全球60/40是本轮更严厉的简单基准。" option={rolling} fallback="V3相对全球60/40的CAGR差中位数为负。" height={330}/><div className="guard-grid"><div><span className="meta">相对沪深300全收益</span><p>中位 {pct(data.rollingVerdict.medianVsHs300)} · 跑赢 {data.rollingVerdict.winsVsHs300}/111</p></div><div><span className="meta">相对中国60/40</span><p>中位 {pct(data.rollingVerdict.medianVsChina60)} · 跑赢 {data.rollingVerdict.winsVsChina60}/111</p></div><div><span className="meta">相对全球60/40</span><p>中位 {pct(data.rollingVerdict.medianVsGlobal60)} · 跑赢 {data.rollingVerdict.winsVsGlobal60}/111</p></div></div></section>

    <section className="model-section"><h2>5. V2反证没有被删除</h2><div className="table-scroll"><table><thead><tr><th>全收益统一次日收盘</th><th>CAGR</th><th>最大回撤</th><th>期末财富</th></tr></thead><tbody><tr><th>旧危机状态机</th><td>{pct(tr.crisis.cagr)}</td><td>{pct(tr.crisis.maxDrawdown)}</td><td>¥{num(tr.crisis.finalValue, 0)}</td></tr><tr><th>65%股票年度再平衡</th><td>{pct(tr.annual.cagr)}</td><td>{pct(tr.annual.maxDrawdown)}</td><td>¥{num(tr.annual.finalValue, 0)}</td></tr></tbody></table></div><p>价格指数原起点仍对旧模型有利：3.408% CAGR / 37.857% MDD，高于该窗口的等回撤静态价格组合。V3的结论来自全收益反例、滚动起点多数落后和复杂度审计，而不是抹掉有利窗口。</p><Link to="/models/hs300/crisis-validation">返回V2完整稳健性审计</Link></section>

    <section className="model-section"><h2>6. 六类资产机会成本</h2><div className="table-scroll"><table><thead><tr><th>资产/策略</th><th>币种</th><th>CAGR</th><th>最大回撤</th><th>Calmar</th><th>Sortino</th><th>最长水下</th><th>终值</th></tr></thead><tbody>{data.opportunity.map((r: Row) => <tr key={r.id}><th>{r.label}</th><td>{r.currency}</td><td>{pct(r.cagr)}</td><td>{pct(r.maxDrawdown)}</td><td>{num(r.calmar, 3)}</td><td>{num(r.sortino, 3)}</td><td>{r.longestUnderwaterCalendarDays}日</td><td>¥{num(r.finalValue, 0)}</td></tr>)}</tbody></table></div><p>海外资产同时保留了本币与人民币审计口径。这里展示人民币机会成本；汇率、国家、估值、税费和可获得性风险不能因高历史收益而省略。</p></section>

    <section className="model-section"><h2>7. 删除、保留与重构</h2><div className="table-scroll"><table><thead><tr><th>模块</th><th>V3处置</th><th>理由</th></tr></thead><tbody>{data.moduleDecisions.map((r: Row) => <tr key={r.module}><th>{r.module}</th><td>{r.decision}</td><td>{r.reason}</td></tr>)}</tbody></table></div></section>

    <section className="model-section"><h2>8. 数据与可执行性边界</h2><ul>{data.limitations.map((x: string) => <li key={x}>{x}</li>)}</ul><p>H00300、H11006与标普500总回报是指数；QQQ、ACWI、GLD是美国ETF代理。个人生活应急资金必须置于模型外，不能用有久期风险的H11006替代。</p></section>

    <section className="model-section"><h2>9. 可复核交付物</h2><div className="module-links">{files.map(([file, label]) => <a key={file} href={`./crisis-v3/${file}`} download>{label}</a>)}</div><p>V3独立账本测试10/10、站点回归测试13/13通过；V2的51项冻结测试经复核包哈希核对保留，但没有冒充为本次重新执行。</p></section>
    <Notice>Research only. V3回答的是“复杂状态机是否值得继续”，不是替用户决定资产配置。进入实盘前仍需验证可交易产品、税费、汇率与个人流动性约束。</Notice>
  </>;
}

export default function HS300CrisisV3() {
  const [data, setData] = useState<Row | null>(null); const [error, setError] = useState(false);
  useEffect(() => { fetch('./crisis-v3/results.json').then(r => { if (!r.ok) throw Error(); return r.json(); }).then(setData).catch(() => setError(true)); }, []);
  return <div className="page model-page"><div className="page-breadcrumb"><Link to="/models">模型实验室</Link> / <Link to="/models/hs300">沪深300</Link> / V3资产选择优先</div><PageHeading eyebrow="CRISIS ALLOCATION V3" title="先选择资产，再讨论买入方法" summary="复杂状态机退役审计 · 固定风险预算 · 2011-10-10—2026-09-30" action={<PrintButton/>}/>{data ? <V3Viewer data={data}/> : error ? <Notice title="V3数据加载失败"><Button onClick={() => location.reload()}>重新加载</Button><a href="./crisis-v3/REPORT.md">打开报告</a></Notice> : <Spinner label="加载V3复核结果"/>}</div>;
}
