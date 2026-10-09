import { Badge, Button, Field, Input } from '@fluentui/react-components';
import { Print24Regular, ArrowDownload24Regular } from '@fluentui/react-icons';
import { Link } from 'react-router-dom';
import type { EvidenceLevel, Source } from '../content/schema';
import type { ReactNode } from 'react';
export const labels: Record<EvidenceLevel, string> = { Fact: '事实', 'Strong evidence': '强证据', Interpretation: '解释', Hypothesis: '假设', Scenario: '情景', 'Open question': '开放问题' };
export function Evidence({ level }: { level: EvidenceLevel }) { return <Badge appearance="tint" color={level === 'Scenario' ? 'informative' : level === 'Hypothesis' ? 'warning' : level === 'Fact' ? 'success' : 'subtle'} className="evidence">{labels[level]} · {level}</Badge>; }
export function PageHeading({ eyebrow, title, summary, action }: { eyebrow: string; title: string; summary: string; action?: ReactNode }) { return <header className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{summary}</p></div>{action && <div className="page-action">{action}</div>}</header>; }
export function SectionHeading({ title, subtitle, to, link }: { title: string; subtitle?: string; to?: string; link?: string }) { return <div className="section-heading"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{to && <Link to={to} className="text-link">{link || '查看全部'}</Link>}</div>; }
export function Notice({ children, title }: { children: ReactNode; title?: string }) { return <div className="notice" role="note">{title && <strong>{title}</strong>}<div>{children}</div></div>; }
export function Sources({ items }: { items: Source[] }) { return <section className="sources" id="sources"><h2>来源与资料</h2><ol>{items.map(s => <li id={`source-${s.id}`} key={s.id}>{s.url ? <a href={s.url} target="_blank" rel="noreferrer">{s.title}</a> : <span>{s.title}</span>}<div className="meta">日期 {s.date} · 核对 {s.accessedAt} · {s.status}</div></li>)}</ol></section>; }
export function PrintButton() { return <Button icon={<Print24Regular />} onClick={() => window.print()} className="no-print">打印</Button>; }
export function NumberField({ label, value, onChange, min, max, step = 1, hint }: { label: string; value: number; onChange: (n: number) => void; min?: number; max?: number; step?: number; hint?: string }) {
  return <Field label={label} hint={hint}><Input type="number" value={Number.isNaN(value) ? '' : String(value)} min={min} max={max} step={step} onChange={(_, d) => onChange(d.value === '' ? NaN : Number(d.value))} /></Field>;
}
export function downloadCsv(filename: string, rows: (string | number)[][]) { const csv = '\ufeff' + rows.map(row => row.map(x => `"${String(x).replaceAll('"', '""')}"`).join(',')).join('\r\n'); const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' })); const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
export function ExportButton({ onClick, label = '导出计算表' }: { onClick: () => void; label?: string }) { return <Button icon={<ArrowDownload24Regular />} onClick={onClick} className="no-print">{label}</Button>; }
export const num = (value: number, digits = 0) => Number.isFinite(value) ? value.toLocaleString('zh-CN', { maximumFractionDigits: digits, minimumFractionDigits: digits }) : '—';
