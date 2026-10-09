import { useEffect, useRef, useState } from 'react';
import type { EChartsOption } from 'echarts';
import { useTheme } from '../theme/theme';
import { Button, Spinner } from '@fluentui/react-components';
export default function Chart({ title, question, option, fallback, provenance = '来源：用户输入与公式计算 · Model output · 2026-10-07', height = 300 }: { title: string; question: string; option: EChartsOption; fallback: string; provenance?: string; height?: number }) {
  const el = useRef<HTMLDivElement>(null); const { dark } = useTheme(); const [state, setState] = useState('loading'); const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true; let chart: import('echarts/core').ECharts | undefined; let observer: ResizeObserver | undefined;
    setState('loading');
    import('../theme/chartTheme').then(({ echarts: e, chartColors }) => {
      if (!active || !el.current) return;
      chart = e.init(el.current, dark ? 'dark' : undefined, { renderer: 'svg' });
      chart.setOption({ backgroundColor: 'transparent', color: chartColors, textStyle: { fontFamily: 'Segoe UI, Microsoft YaHei, sans-serif', fontSize: 13 }, aria: { enabled: true, label: { description: fallback } }, ...option });
      observer = new ResizeObserver(() => chart?.resize()); observer.observe(el.current); setState('ready');
    }).catch(() => { if (active) setState('error'); });
    return () => { active = false; observer?.disconnect(); chart?.dispose(); };
  }, [dark, option, fallback, retry]);
  return <figure className="chart-panel"><figcaption><h3>{title}</h3><p>{question}</p></figcaption><div className="chart-wrap" style={{ minHeight: height }}><div ref={el} style={{ width: '100%', height }} role="img" aria-label={fallback} />{state === 'loading' && <div className="chart-state"><Spinner label="加载图表" /></div>}{state === 'error' && <div className="chart-state"><p>图表暂时无法加载，计算表和文字结果仍可阅读。</p><Button onClick={() => setRetry(x => x + 1)}>重新加载</Button></div>}</div><details className="chart-fallback"><summary>图表文字说明</summary><p>{fallback}</p></details><div className="meta">{provenance}</div></figure>;
}
