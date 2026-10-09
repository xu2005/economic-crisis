import { useState } from 'react';
import { Badge, Button } from '@fluentui/react-components';
import { phases } from '../data/registry';
export default function CrisisRadar() {
  const [index, setIndex] = useState(0); const phase = phases[index];
  return <section className="radar"><div className="radar-title"><div><h2>危机雷达</h2><p>阶段可以跳跃、逆转，也可以在不同部门同时存在。</p></div><Badge appearance="tint" color="subtle">研究框架 · 非实时判断</Badge></div><div className="phase-track" role="group" aria-label="探索七个危机阶段">{phases.map((p, i) => <Button appearance="subtle" key={p.en} className={`phase ${i === index ? 'selected' : ''}`} aria-pressed={i === index} onClick={() => setIndex(i)}><span className="phase-number">{String(i + 1).padStart(2, '0')}</span><strong>{p.title}</strong><small>{p.en}</small></Button>)}</div><div className="phase-detail" aria-live="polite"><div><span className="eyebrow">阶段定义 / 当前浏览</span><h3>{phase.title}</h3><p>{phase.desc}</p></div><div><strong>观察什么</strong><p>{phase.watch}</p><span className="meta">{phase.examples}</span></div></div><p className="meta">当前没有市场状态判定。选择阶段仅改变解释面板，与HS300资金模型保持独立。</p></section>;
}
