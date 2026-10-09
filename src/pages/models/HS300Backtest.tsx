import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Badge, Field, Select } from '@fluentui/react-components';
import type { EChartsOption } from 'echarts';
import frozen from '../../data/hs300-history.public-placeholder.json';
import verification from '../../data/hs300-verification.json';
import { backtest, type BacktestConfig, type Bar } from '../../models/hs300/backtest';
import { baseline } from '../../models/hs300/engine';
import Chart from '../../components/Chart';
import { PageHeading, Notice, PrintButton, num, ExportButton, downloadCsv } from '../../components/common';
const pct=(n:number)=>num(n*100,2)+'%';
const names={power:'幂律分档',equal:'等额分档',geometric:'几何分档',lump:'一次性买入'};
const asset:Bar[]=frozen.asset, sse:Bar[]=frozen.sse;
function HS300BacktestWithData() {
  const [trigger,setTrigger]=useState<'hs300'|'sse'>('hs300');
  const [gamma,setGamma]=useState(1.6),[anchor,setAnchor]=useState<BacktestConfig['anchor']>('running-high');
  const [cost,setCost]=useState('base');
  const config:BacktestConfig=useMemo(()=>({parameters:{...baseline,gamma},anchor,allocation:'power',commissionBps:cost==='none'?0:cost==='stress'?50:3,slippageBps:cost==='none'?0:5}),[gamma,anchor,cost]);
  const results=useMemo(()=> (['power','equal','geometric','lump'] as const).map(allocation=>({allocation,...backtest(asset,trigger==='hs300'?asset:sse,{...config,allocation})})),[trigger,config]);
  const main=results[0],benchmark=results[3];
  const curveOption=useMemo<EChartsOption>(()=>({tooltip:{trigger:'axis',valueFormatter:v=>num(Number(v),0)+'元'},legend:{top:0,itemWidth:14,textStyle:{fontSize:12}},grid:{left:10,right:16,top:68,bottom:25,containLabel:true},xAxis:{type:'category',data:asset.map(x=>x.date),axisLabel:{hideOverlap:true,formatter:(x:string)=>x.slice(0,4)}},yAxis:{type:'value',name:'总资产 / 元',axisLabel:{formatter:(v:number)=>num(v/10000,0)+'万'}},series:results.map(r=>({name:names[r.allocation],type:'line',showSymbol:false,data:r.curve.map(x=>Number(x.equity.toFixed(2))),lineStyle:{width:r.allocation==='power'?3:1.5}}))}),[results]);
  const riskOption=useMemo<EChartsOption>(()=>({tooltip:{trigger:'axis',valueFormatter:v=>num(Number(v),2)+'%'},legend:{top:0,textStyle:{fontSize:12}},grid:{left:10,right:16,top:55,bottom:25,containLabel:true},xAxis:{type:'category',data:asset.map(x=>x.date),axisLabel:{hideOverlap:true,formatter:(x:string)=>x.slice(0,4)}},yAxis:{type:'value',name:'组合回撤 / %'},series:[main,benchmark].map(r=>({name:names[r.allocation],type:'line',showSymbol:false,data:r.curve.map(x=>Number((-100*x.drawdown).toFixed(3)))}))}),[main,benchmark]);
  const cohorts=frozen.report.cohorts.filter(x=>x.triggerId===trigger);
  const wins=cohorts.filter(x=>x.outperformance>0).length;
  const difference=main.metrics.totalReturn-benchmark.metrics.totalReturn;
  return <div className="page model-page">
    <div className="page-breadcrumb"><Link to="/models">模型实验室</Link> / <Link to="/models/hs300">沪深300预算</Link> / 历史回测</div>
    <PageHeading eyebrow="HS300 · HISTORICAL VALIDATION" title="沪深300 · 15年回测" summary={`${frozen.report.start} — ${frozen.report.end} · ${num(frozen.report.rows)}个交易日 · 数据冻结于2026-10-07`} action={<PrintButton />} />
    <div className="tag-row"><Badge appearance="tint" color="success">资金与成交逻辑检查通过</Badge><Badge appearance="tint" color="warning">早期预算核心基准</Badge></div>
    <div className="result-kpis backtest-kpis"><div><span>幂律终值</span><strong>¥{num(main.metrics.finalValue)}</strong><small>总收益 {pct(main.metrics.totalReturn)}</small></div><div><span>年化收益 / CAGR</span><strong>{pct(main.metrics.cagr)}</strong><small>以全部本金与实际日历时长计算</small></div><div><span>最大组合回撤</span><strong>{pct(main.metrics.maxDrawdown)}</strong><small>包含初始本金与每日收盘净值</small></div><div><span>期末现金</span><strong>¥{num(main.metrics.cash)}</strong><small>已执行 {main.metrics.filledLevels}/8档</small></div></div>
    <div className="backtest-controls">
      <Field label="触发参考"><Select value={trigger} onChange={(_,d)=>setTrigger(d.value as typeof trigger)}><option value="hs300">沪深300自身回撤</option><option value="sse">上证指数回撤 · 原任务参考</option></Select></Field>
      <Field label="幂指数 γ"><Select value={String(gamma)} onChange={(_,d)=>setGamma(Number(d.value))}>{[1,1.6,2,2.5,3].map(x=><option key={x} value={x}>{x}{x===1.6?' · 基准':''}</option>)}</Select></Field>
      <Field label="锚点规则"><Select value={anchor} onChange={(_,d)=>setAnchor(d.value as typeof anchor)}><option value="running-high">期间收盘新高上调</option><option value="initial-close">固定首日收盘</option></Select></Field>
      <Field label="单边费用假设"><Select value={cost} onChange={(_,d)=>setCost(d.value)}><option value="base">佣金0.03% + 滑点0.05%</option><option value="none">零费用对照</option><option value="stress">佣金0.50% + 滑点0.05%</option></Select></Field>
    </div>
    <Notice title="原文到位后的新增验证"><Link to="/models/hs300/crisis-validation">查看原文问题、大跌买入、时间门控与修复退出的15年验证。</Link> 本页保留早期无门控、不卖出的预算核心基准，便于比较。</Notice><Notice title="本次验证范围">本金10万元，最大部署100%，每5%回撤一档，最大档位40%。收盘触发、次日开盘买入，每档只执行一次，不卖出、不重置、不追加本金。锚点从回测首日收盘初始化；所有门控条件均未启用。这里验证的是已实现的预算核心，不能代替原完整算法的回测。</Notice>
    <Notice title="如何理解当前结果">幂律比一次性买入{difference>=0?'多':'少'}获得{num(Math.abs(difference)*100,2)}个百分点的总收益。{main.metrics.cash===0?`全部预算已在${main.metrics.lastFill}投入；此后持有相同价格指数，改变γ无法继续缓冲后续市场回撤。`:'固定本金仍有未部署现金；等待深跌也会错过上涨。'}核对计算正确与证明策略有效，是两件需要分别判断的事。</Notice>
    <Chart title="总资产随时间变化" question="每个方案都从同一10万元本金出发，现金与持仓共同计入组合。" option={curveOption} fallback={results.map(r=>`${names[r.allocation]}终值${num(r.metrics.finalValue)}元，总收益${pct(r.metrics.totalReturn)}，年化${pct(r.metrics.cagr)}`).join('；')} height={350} provenance="来源：中证官网OHLC，腾讯交易日期及补充数据 · 日线回测 · 2026-10-07" />
    <Chart title="每日组合回撤" question="投入预算的40%档位是触发参考跌幅；它不会把组合最大亏损限制在40%。" option={riskOption} fallback={`幂律最大回撤${pct(main.metrics.maxDrawdown)}；一次性买入${pct(benchmark.metrics.maxDrawdown)}。`} height={290} provenance="组合净值 = 现金 + 指数代理份额 × 当日收盘；回撤从此前最高组合净值计算。" />
    <section className="model-section"><h2>同本金比较</h2><div className="table-scroll" tabIndex={0} role="region" aria-label="四种资金分配回测对照"><table><thead><tr><th>方案</th><th>终值 / 元</th><th>总收益</th><th>年化</th><th>最大回撤</th><th>平均投资比例</th><th>期末现金 / 元</th></tr></thead><tbody>{results.map(r=><tr key={r.allocation}><td>{names[r.allocation]}</td><td>{num(r.metrics.finalValue)}</td><td>{pct(r.metrics.totalReturn)}</td><td>{pct(r.metrics.cagr)}</td><td>{pct(r.metrics.maxDrawdown)}</td><td>{pct(r.metrics.avgExposure)}</td><td>{num(r.metrics.cash)}</td></tr>)}</tbody></table></div><p className="meta">等额和几何保持相同触发档位、终端预算、费用和成交时点；几何比率固定1.3。一次性买入在首日开盘成交。平均投资比例为每日持仓市值/总资产的算术平均。</p></section>
    <section className="model-section"><h2>幂律成交记录</h2><p>跳过多档时，跨过的未执行档位全部排队到下一交易日，同一开盘价成交。新高上调锚点不会重置已花费的预算。</p><div className="model-actions"><ExportButton label="导出成交记录" onClick={()=>downloadCsv('hs300-backtest-current-fills.csv',[['Trigger',trigger],['Gamma',gamma],['Anchor',anchor],['Commission_bps',config.commissionBps],['Slippage_bps',config.slippageBps],['档位','信号日期','成交日期','信号回撤%','预算含佣金RMB','真实开盘点位','含滑点价格','指数代理份额','佣金RMB','剩余现金RMB'],...main.fills.map(x=>[x.level,x.signalDate??'',x.date,x.triggerDrawdown,x.budget,x.open,x.price,x.units,x.fee,x.cashAfter])])}/><ExportButton label="导出逐日账本" onClick={()=>downloadCsv('hs300-backtest-current-daily.csv',[['Trigger',trigger],['Gamma',gamma],['Anchor',anchor],['Commission_bps',config.commissionBps],['Slippage_bps',config.slippageBps],['日期','总资产RMB','现金RMB','指数代理份额','持仓市值RMB','组合回撤%','触发锚点','触发回撤%'],...main.curve.map(x=>[x.date,x.equity,x.cash,x.units,x.invested,x.drawdown*100,x.anchor,x.triggerDrawdown])])}/></div><div className="table-scroll" tabIndex={0} role="region" aria-label="幂律分档成交记录"><table><thead><tr><th>档位</th><th>信号日期</th><th>成交日期</th><th>信号回撤</th><th>预算 / 元</th><th>含滑点价格</th><th>余下现金 / 元</th></tr></thead><tbody>{main.fills.map(x=><tr key={x.level}><td>{x.level} · {x.threshold}%</td><td>{x.signalDate}</td><td>{x.date}</td><td>{num(x.triggerDrawdown,2)}%</td><td>{num(x.budget,2)}</td><td>{num(x.price,2)}</td><td>{num(x.cashAfter,2)}</td></tr>)}</tbody></table></div>{!main.fills.length&&<p>当前锚点规则下，没有跨过任何档位。</p>}{!!main.pendingLevels.length&&<p>最后一日待执行档位：{main.pendingLevels.join('、')}。没有下一交易日价格，因此未虚构成交。</p>}</section>
    <section className="model-section"><h2>更换入场起点：40个五年窗口</h2><p>从2011年第四季度至2021年第三季度，每季度首个交易日投入新的独立10万元本金，持有约五年。以下固定γ=1.6、新高锚点、基准费用，仅切换触发指数；不随上方γ、锚点或费用控件变化。</p><div className="result-kpis"><div><span>幂律终值高于一次性买入</span><strong>{wins}/{cohorts.length}</strong></div><div><span>五年总收益范围</span><strong>{pct(Math.min(...cohorts.map(x=>x.power.totalReturn)))} 至 {pct(Math.max(...cohorts.map(x=>x.power.totalReturn)))}</strong></div><div><span>最差窗口最大回撤</span><strong>{pct(Math.max(...cohorts.map(x=>x.power.maxDrawdown)))}</strong></div></div><p className="meta">窗口高度重叠，不能作为40次独立试验估计胜率；没有按回测收益调优参数。窗口末日只按收盘估值，没有模拟卖出。</p><details><summary>展开各窗口结果</summary><div className="table-scroll"><table><thead><tr><th>入场</th><th>终点</th><th>幂律总收益</th><th>一次性总收益</th><th>差额 / 百分点</th><th>幂律最大回撤</th></tr></thead><tbody>{cohorts.map(x=><tr key={x.start}><td>{x.start}</td><td>{x.end}</td><td>{pct(x.power.totalReturn)}</td><td>{pct(x.lump.totalReturn)}</td><td>{num(x.outperformance*100,2)}</td><td>{pct(x.power.maxDrawdown)}</td></tr>)}</tbody></table></div></details></section>
    <section className="model-section"><h2>正确性检查与发现</h2><div className="guard-grid"><div><h3>两套程序独立核对</h3><p>TypeScript交易状态机与Python预算、持仓账本对照7条完整历史路径，共{num(verification.comparedFields)}个字段；最大绝对差{verification.maxAbsoluteDifference.toExponential(2)}，低于1×10⁻⁷容差。</p></div><div><h3>13项测试通过</h3><p>覆盖跳档实际成交、末日信号不成交、两指数分离、锚点上调不补充预算、费用在预算之内、零部署及非整除步长。100条随机路径×4种配置检查资金守恒、唯一档位和历史前缀一致。</p></div><div><h3>修复一个输入边界</h3><p>旧验证只检查传入的值，遗漏字段可能产生NaN。现在逐项检查五个必填参数，缺失或非有限数值均拒绝。</p></div><div><h3>策略评价边界</h3><p>本页仅验证早期预算核心。原文已经取得，时间、冷却、右侧与补充退出的验证在新页面；历史PB/ERP仍缺失，未声称完整模型通过。</p></div></div></section>
    <section className="model-section"><h2>数据核对与口径</h2><ul><li>15年请求区间2011-10-07—2026-10-07，实际交易记录2011-10-10—2026-09-30，共3,641日。沪深300全部交易日期有中证官网OHLC与腾讯数据交叉覆盖。</li><li>删除官网年度查询产生的15条非交易日边界记录。沪深300发现12个字段差异，采用官网有效记录；2015-03-27腾讯高低价异常由官网记录替换。完整差异和文件SHA-256保存在数据审计中。</li><li>上证指数2018年官网请求返回403，该年243日采用腾讯；其余3,398日有官网交叉覆盖。触发与标的日期严格对齐，不填充缺失行情。</li><li>使用000300价格指数，没有红利再投资。分红、ETF费用、跟踪误差、整数手、税费和真实成交约束未纳入，指数份额只是价格代理。与全收益指数或真实ETF回报不能直接等同。</li><li>佣金和滑点是统一研究假设，不是实际券商报价；佣金包含在各档预算内，滑点通过买入价格体现。现金收益为零，期末按收盘标价。</li></ul><div className="module-links"><a href="https://www.csindex.com.cn/zh-CN/indices/index-detail/000300" target="_blank" rel="noreferrer">中证指数 · 沪深300</a><a href="https://gu.qq.com/sh000300/zs" target="_blank" rel="noreferrer">腾讯 · 沪深300行情</a><a href="https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/detail/files/zh_CN/000300_Index_Methodology_cn.pdf" target="_blank" rel="noreferrer">价格与全收益指数编制口径</a></div></section>
    <section className="model-section"><h2>下载与复核</h2><div className="module-links">{[['hs300-daily.csv','沪深300日线'],['sse-daily.csv','上证指数日线'],['provenance.json','原始请求与数据审计'],['results.json','固定基准完整结果'],['verification.json','独立验证结果'],['hs300-power-daily-ledger.csv','基准幂律逐日账本']].map(([file,label])=><a key={file} href={'./backtest/'+file} download>{label}</a>)}</div><p className="meta">固定下载文件对应γ=1.6、新高锚点、佣金3基点、滑点5基点。上方导出按钮使用当前控件参数。</p><Link to="/models/hs300">返回预算公式与原规则迁移清单</Link></section>
  </div>;
}

function HS300BacktestUnavailable() {
  return <div className="page model-page">
    <div className="page-breadcrumb"><Link to="/models">模型实验室</Link> / <Link to="/models/hs300">沪深300预算</Link> / 历史回测</div>
    <PageHeading eyebrow="HS300 · HISTORICAL VALIDATION" title="沪深300 · 15年回测" summary="公开整理副本未包含原始指数日线" action={<PrintButton />} />
    <Notice title="原始行情序列未纳入公开仓库">该副本遵守 V16 发布记录中的 raw_series_public=false 设置。完整历史回测需要在本地提供经授权的行情数据；此处不显示或重算历史结果。</Notice>
    <Link to="/models/hs300">返回预算公式与研究范围</Link>
  </div>;
}

export default function HS300Backtest() {
  return frozen.asset.length === 0 || frozen.sse.length === 0
    ? <HS300BacktestUnavailable />
    : <HS300BacktestWithData />;
}