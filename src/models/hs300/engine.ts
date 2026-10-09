export interface PyramidParameters { capital: number; gamma: number; maxDrawdown: number; step: number; deployment: number; }
export const baseline: PyramidParameters = { capital: 100000, gamma: 1.6, maxDrawdown: 40, step: 5, deployment: 100 };
export type Allocation = 'power' | 'equal' | 'geometric';
export interface LadderRow { level: number; drawdown: number; fraction: number; cumulative: number; increment: number; cash: number; }
export function validate(p: PyramidParameters): string | null {
  if (['capital', 'gamma', 'maxDrawdown', 'step', 'deployment'].some(k => !Number.isFinite(p[k as keyof PyramidParameters]))) return '请输入完整的有限数值参数。';
  if (p.capital <= 0 || p.capital > 1e9) return '本金范围为大于0、至10亿元。';
  if (p.gamma <= 0 || p.gamma > 5) return 'γ范围为大于0、至5。';
  if (p.maxDrawdown <= 0 || p.maxDrawdown >= 100) return '最大回撤必须大于0且小于100%。';
  if (p.step <= 0 || p.step > p.maxDrawdown || Math.ceil(p.maxDrawdown / p.step) > 50) return '步长应大于0，档位不超过50档。';
  if (p.deployment < 0 || p.deployment > 100) return '最大部署比例应在0–100%之间。';
  return null;
}
export function ladder(p: PyramidParameters, allocation: Allocation = 'power'): LadderRow[] {
  const error = validate(p); if (error) throw new Error(error);
  const n = Math.ceil(p.maxDrawdown / p.step);
  let previous = 0;
  return Array.from({ length: n }, (_, i) => {
    const drawdown = Math.min((i + 1) * p.step, p.maxDrawdown);
    const fraction = allocation === 'power' ? (drawdown / p.maxDrawdown) ** p.gamma : allocation === 'equal' ? (i + 1) / n : (1.3 ** (i + 1) - 1) / (1.3 ** n - 1);
    const cumulative = p.capital * p.deployment / 100 * fraction;
    const increment = cumulative - previous; previous = cumulative;
    return { level: i + 1, drawdown, fraction, cumulative, increment, cash: p.capital - cumulative };
  });
}
export function scenarioValue(p: PyramidParameters, allocation: Allocation, referenceDrawdown: number, terminalPrice: number, assetSensitivity: number) {
  if (![referenceDrawdown, terminalPrice, assetSensitivity].every(Number.isFinite) || terminalPrice <= 0 || referenceDrawdown < 0 || assetSensitivity < 0) throw new Error('情景参数无效');
  const rows = ladder(p, allocation).filter(r => r.drawdown <= referenceDrawdown);
  let units = 0, deployed = 0;
  for (const row of rows) { const price = 100 * (1 - row.drawdown / 100 * assetSensitivity); if (price <= 0) throw new Error('假设买入价格必须大于0'); units += row.increment / price; deployed += row.increment; }
  return { cash: p.capital - deployed, deployed, units, value: p.capital - deployed + units * terminalPrice, profit: units * terminalPrice - deployed };
}
export function anchorDrawdown(anchor: number, current: number) { if (!Number.isFinite(anchor) || !Number.isFinite(current) || anchor <= 0 || current <= 0) throw new Error('参考点位必须为正数'); return Math.max(0, (1 - current / anchor) * 100); }
