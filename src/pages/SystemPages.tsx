import { Fragment, useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button, Badge } from '@fluentui/react-components';
import { PageHeading, SectionHeading, Evidence, Notice, NumberField, num, PrintButton } from '../components/common';
import { ResearchArticle, ResearchList, Chain } from './ResearchPages';
import SystemMap from '../components/SystemMap';
import CrisisRadar from '../components/CrisisRadar';
import { research } from '../content/research';
import { scenarios, indicators, timeline } from '../data/registry';
import { notes } from '../content/notes';
const moduleInfo: Record<string, { title: string; en: string; summary: string; ids: string[] }> = {
  '/ai': { title: 'AI资本周期', en: 'AI CAPITAL CYCLE', summary: '能力进步、资本投入与现金回报，属于三个不同的观察层面。', ids: ['ai-capital', 'ai-labour'] },
  '/global': { title: '全球经济', en: 'GLOBAL ECONOMY', summary: '从跨境贸易、美元融资与不同资产负债表观察国际传导。', ids: ['us-financial', 'china-growth', 'inflation-divergence', 'housing', 'labour', 'demography'] },
  '/china': { title: '中国经济', en: 'CHINA', summary: '增长结构、房地产与工业需求，沿反馈路径研究。', ids: ['china-growth', 'china-property', 'inflation-divergence'] },
  '/us': { title: '美国财政与美元', en: 'US FISCAL & FINANCIAL SYSTEM', summary: '财政 → 国债 → 利率 → 企业融资 → 估值 → 信贷 → 实体经济。', ids: ['us-financial'] },
  '/housing': { title: '全球房地产', en: 'GLOBAL HOUSING', summary: '十个经济体、统一维度；不同住房轨迹需要不同结构解释。', ids: ['housing', 'china-property'] },
  '/labour': { title: '劳动与生活水平', en: 'LABOUR & LIVING STANDARDS', summary: '比较可支配资源、有效时间与公共服务。', ids: ['labour', 'worktime', 'ai-labour'] },
  '/demography': { title: '人口与社会再生产', en: 'DEMOGRAPHY & SOCIAL REPRODUCTION', summary: '人口结构、生产率、自动化、资本与保障共同作用。', ids: ['demography', 'housing', 'labour'] },
};
function ResilienceCalculator() {
  const [cash, setCash] = useState(30000), [cost, setCost] = useState(5000);
  const valid = Number.isFinite(cash) && cash >= 0 && Number.isFinite(cost) && cost > 0;
  return <section className="model-section"><h2>现金缓冲情景</h2><p className="meta">Example · 示例输入，不代表建议储备金额 · 无收入、忽略利息与一次性支出的静态计算。</p><div className="experiment-input"><div className="fields"><NumberField label="可用现金 / RMB" value={cash} onChange={setCash} min={0} /><NumberField label="每月必要支出 / RMB" value={cost} onChange={setCost} min={1} /></div>{valid ? <div className="result-kpis"><div><span>静态缓冲月数</span><strong>{num(cash / cost, 1)}个月</strong></div></div> : <div className="validation-error" role="alert">可用现金须非负，必要支出须为正数。</div>}</div></section>;
}
export default function SystemPages() {
  const location = useLocation(); const path = location.pathname;
  useEffect(() => { const focus = new URLSearchParams(location.search).get('focus'); if (focus) document.getElementById(focus)?.scrollIntoView({ block: 'start' }); }, [location.search]);
  if (path === '/methodology') return <ResearchArticle id="methodology" />;
  if (path === '/resilience') return <><div className="page"><PageHeading eyebrow="RESILIENCE" title="个人危机应对" summary="首先活下来，然后才有资格购买廉价资产。" /><Notice title="研究次序">现金储备 → 固定成本 → 就业与技能 → 债务 → 地域迁移 → 资产部署纪律。</Notice><ResilienceCalculator /><ResearchList items={research.filter(r => ['resilience', 'labour'].includes(r.id))} /><div className="module-links"><Link to="/models/hs300">资金预算模型</Link><Link to="/models/labour">劳动收入比较器</Link></div></div></>;
  if (path === '/system') return <div className="page"><PageHeading eyebrow="GLOBAL CRISIS TRANSMISSION" title="危机系统" summary="开放系统中的资本、预期、信用与收入，多条旁路和多向反馈。" /><SystemMap /><CrisisRadar /><section className="model-section"><SectionHeading title="资本积累与动态循环" subtitle="金融、实体、政策与国际传导共同研究。" to="/research/capital-cycle" link="阅读核心机制" /><Chain items={['积累', '投资 / 信用扩张', '资产与预期上升', '边际回报下降', '融资收紧', '就业 / 消费减弱', '重新定价', '政策介入']} /></section><ResearchList items={research.filter(r => ['capital-cycle', 'us-financial', 'methodology'].includes(r.id))} /></div>;
  if (path === '/indicators') return <div className="page"><PageHeading eyebrow="INDICATOR REGISTER" title="指标登记册" summary="每个观察值都需要时间、来源与口径；没有观测，就保留缺口。" /><Notice>没有连接行情API或导入统计序列。所有Value为空，Date未提供；Updated仅表示登记册整理日期。</Notice><div className="indicator-list">{indicators.map(i => <article id={i.id} className="indicator-card" key={i.id}><Badge appearance="tint" color="subtle">{i.status}</Badge><h3>{i.label}</h3><dl><dt>Value</dt><dd>— · {i.unit}</dd><dt>Date</dt><dd>待提供</dd><dt>Source</dt><dd>{i.source}</dd><dt>Updated</dt><dd>{i.updatedAt}</dd><dt>频率</dt><dd>{i.frequency}</dd></dl><p>{i.notes}</p></article>)}</div></div>;
  if (path === '/timeline') return <div className="page"><PageHeading eyebrow="PROJECT TIMELINE" title="项目研究进展" summary="记录真实修订，不补造过去的研究日期。" /><div className="project-timeline">{timeline.map((t, i) => <div key={i}><time>{t.date}</time><h3>{t.title}</h3><p>{t.desc}</p></div>)}</div></div>;
  if (path.startsWith('/notes')) {
    const id = path.split('/')[2]; const n = notes.find(n => n.id === id);
    if (id && !n) return <div className="page empty-state"><h1>未找到笔记</h1><Link to="/notes">返回笔记库</Link></div>;
    if (n) return <div className="page"><PageHeading eyebrow="RESEARCH NOTE" title={n.title} summary={n.summary} action={<PrintButton />} /><div className="article-layout"><article className="article"><Evidence level={n.evidence} /><p className="meta">更新 {n.updatedAt} · 首版整理笔记</p>{n.body.map((p, i) => <p key={i}>{p}</p>)}<section><h2>依据</h2><ul>{n.sources.map(s => <li key={s}>{s}</li>)}</ul></section><section><h2>相关研究</h2><div className="module-links">{n.related.map(id => <Link key={id} to={'/research/' + id}>{research.find(r => r.id === id)?.title}</Link>)}</div></section><section><h2>修订记录</h2><p className="meta">v0.1 · {n.updatedAt} · 依据用户研究纲要整理。</p></section></article></div></div>;
    return <div className="page"><PageHeading eyebrow="RESEARCH NOTES" title="研究笔记" summary="把问题、假设与修订过程留下来。" action={<Link to="/timeline">项目进展</Link>} /><div className="note-list">{notes.map(n => <Link key={n.id} to={'/notes/' + n.id}><div><Evidence level={n.evidence} /><h3>{n.title}</h3><p>{n.summary}</p></div><time>{n.updatedAt}</time></Link>)}</div><Notice>此前笔记尚未导入。这些日期仅记录本次结构整理。</Notice></div>;
  }
  const module = moduleInfo[path];
  if (!module) return <div className="page empty-state">没有找到模块</div>;
  return <div className="page"><PageHeading eyebrow={module.en} title={module.title} summary={module.summary} action={<Link to="/indicators" className="button-link">查看数据缺口</Link>} />{path === '/global' && <div className="module-links">{Object.entries(moduleInfo).filter(([p]) => !['/global', '/ai'].includes(p)).map(([p, m]) => <Link key={p} to={p}>{m.title}</Link>)}</div>}<ResearchList items={research.filter(r => module.ids.includes(r.id))} />{path === '/ai' && <><section className="model-section"><SectionHeading title="AI危机传导：三种条件情景" subtitle="没有概率输出，前提改变时结论也需要更新。" />{scenarios.map(s => <Fragment key={s.id}><div className="model-section"><Evidence level="Scenario" /><h3 style={{ marginTop: 12 }}>{s.name}</h3><p>{s.premise}</p><Chain items={s.transmission} /><div className="guard-grid"><div><h3>触发与观察</h3><ul>{[...s.triggers, ...s.indicators].map(x => <li key={x}>{x}</li>)}</ul></div><div><h3>政策旁路 / 证伪</h3><ul>{[...s.policyResponses, ...s.falsifiers].map(x => <li key={x}>{x}</li>)}</ul><p>不确定性：{s.uncertainty} · {s.implications.join('；')}</p></div></div></div></Fragment>)}</section><div className="module-links"><Link to="/models/ai-capex">打开AI资本开支压力实验</Link><Link to="/history/comparison">历史比较矩阵</Link></div></>}{path === '/housing' && <div className="module-links"><Link to="/models/housing">十经济体住房比较器</Link></div>}{path === '/labour' && <div className="module-links"><Link to="/models/labour">生活资源与工时比较器</Link><Link to="/demography">人口与社会再生产</Link></div>}</div>;
}

