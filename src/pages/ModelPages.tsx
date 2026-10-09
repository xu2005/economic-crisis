import { lazy, Suspense } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Badge, Spinner } from '@fluentui/react-components';
import { models } from '../data/registry';
import { PageHeading } from '../components/common';
import CrisisRadar from '../components/CrisisRadar';
import type { ModelSpec } from '../content/schema';
const HS300 = lazy(() => import('./models/HS300'));
const HS300Backtest = lazy(() => import('./models/HS300Backtest'));
const HS300CrisisValidation = lazy(() => import('./models/HS300CrisisValidation'));
const HS300CrisisV3 = lazy(() => import('./models/HS300CrisisV3'));
const CNYImplementability = lazy(() => import('./models/CNYImplementability'));
const HS300Implementation = lazy(() => import('./models/HS300Implementation'));
const HS300CrisisFreeze = lazy(() => import('./models/HS300CrisisFreeze'));
const Experiments = lazy(() => import('./models/Experiments'));
export function ModelDocumentation({ model }: { model: ModelSpec }) { return <section className="model-section model-doc" id="model-documentation"><h2>模型说明与版本</h2><dl><dt>Purpose</dt><dd>{model.purpose}</dd><dt>Inputs</dt><dd>{model.inputs.join('；')}</dd><dt>Assumptions</dt><dd>{model.assumptions.join('；')}</dd><dt>Formula</dt><dd>{model.formula}</dd><dt>Output</dt><dd>{model.output}</dd><dt>Limitations</dt><dd>{model.limitations.join('；')}</dd><dt>Version / Updated</dt><dd>{model.version} · {model.updated}</dd><dt>Changelog</dt><dd><ul>{model.changelog.map(s => <li key={s}>{s}</li>)}</ul></dd></dl></section>; }
export default function ModelPages() {
  const path = useLocation().pathname; const model = models.find(m => m.path === path);
  if (path === '/models/hs300/cny-implementability') return <Suspense fallback={<Spinner label="加载人民币税后研究" />}><CNYImplementability /></Suspense>;
  if (path === '/models/hs300/implementation-qualification') return <Suspense fallback={<Spinner label="加载V3.2实施资格" />}><HS300Implementation /></Suspense>;
  if (path === '/models/hs300/crisis-freeze') return <Suspense fallback={<Spinner label="加载V3.1冻结审计" />}><HS300CrisisFreeze /></Suspense>;
  if (path === '/models/hs300/crisis-v3') return <Suspense fallback={<Spinner label="加载V3资产配置审计" />}><HS300CrisisV3 /></Suspense>;
  if (path === '/models/hs300/crisis-validation') return <Suspense fallback={<Spinner label="加载危机算法验证" />}><HS300CrisisValidation /></Suspense>;
  if (path === '/models/hs300/backtest') return <Suspense fallback={<Spinner label="加载历史回测" />}><HS300Backtest /></Suspense>;
  if (path === '/models/hs300') return <Suspense fallback={<Spinner label="加载预算模型" />}><HS300 /></Suspense>;
  if (['/models/ai-capex', '/models/labour', '/models/housing'].includes(path)) return <Suspense fallback={<Spinner label="加载研究实验" />}><Experiments /></Suspense>;
  if (model?.id === 'phases') return <div className="page"><PageHeading eyebrow={model.subtitle} title={model.title} summary={model.purpose} /><CrisisRadar /><ModelDocumentation model={model} /></div>;
  if (path !== '/models' && path !== '/models/') return <div className="page empty-state"><h1>未找到模型</h1><Link to="/models">返回模型实验室</Link></div>;
  return <div className="page"><PageHeading eyebrow="MODEL LAB" title="模型实验室" summary="把目的、输入、假设与公式公开，把数值实验与现实观测分开。" /><div className="model-grid">{models.map(m => <article key={m.id} className="model-card"><Badge color="subtle" appearance="tint">{m.status}</Badge><div className="eyebrow">{m.subtitle}</div><h3>{m.title}</h3><p>{m.purpose}</p><Link to={m.path}>打开模型</Link>{m.id==='hs300'&&<p><Link to="/models/hs300/crisis-v3">查看V3资产选择优先审计</Link></p>}<div className="meta" style={{ marginTop: 16 }}>v{m.version} · {m.updated}</div></article>)}</div></div>;
}
