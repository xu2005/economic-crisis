export interface CapexInput { investment: number; revenue: number; utilization: number; costRatio: number; debtRatio: number; interest: number; life: number; }
export function capex(i: CapexInput) {
  if (Object.values(i).some(v => !Number.isFinite(v)) || i.investment <= 0 || i.revenue < 0 || i.life <= 0 || [i.utilization, i.costRatio, i.debtRatio].some(v => v < 0 || v > 100) || i.interest < 0) throw new Error('资本开支实验参数超出范围。');
  const sales = i.revenue * i.utilization / 100;
  const ebitda = sales * (1 - i.costRatio / 100);
  const debt = i.investment * i.debtRatio / 100;
  const service = debt * i.interest / 100 + debt / i.life;
  const depreciation = i.investment / i.life;
  const capacityMargin = i.revenue * (1 - i.costRatio / 100);
  return { sales, ebitda, service, depreciation, ebitReturn: (ebitda - depreciation) / i.investment * 100, dscr: service > 0 ? ebitda / service : null, breakEven: capacityMargin > 0 ? service / capacityMargin * 100 : null };
}
export interface LabourInput { name: string; income: number; housing: number; other: number; weekHours: number; weeks: number; commute: number; ppp: number; }
export function labour(i: LabourInput) {
  if ([i.income, i.housing, i.other, i.weekHours, i.weeks, i.commute, i.ppp].some(v => !Number.isFinite(v)) || i.income < 0 || i.housing < 0 || i.other < 0 || i.weekHours <= 0 || i.weeks <= 0 || i.weeks > 52 || i.commute < 0 || i.ppp <= 0) throw new Error('请核对年度金额、工时、周数与PPP。');
  const hours = (i.weekHours + i.commute) * i.weeks;
  const resource = (i.income - i.housing - i.other) / i.ppp;
  return { hours, resource, perHour: resource / hours, incomePerHour: i.income / i.ppp / (i.weekHours * i.weeks) };
}
