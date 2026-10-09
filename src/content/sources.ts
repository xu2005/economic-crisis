import type { Source } from './schema';
const s = (id: string, title: string, url: string, date: string): Source => ({ id, title, url, date, accessedAt: '2026-10-07', status: 'Verified' });
export const sources = {
  brief: { id: 'brief', title: '用户提供的项目任务与研究纲要', date: '2026-10-07', accessedAt: '2026-10-07', status: 'User brief' } as Source,
  ai: s('ai-finance', 'BIS · Financing the AI infrastructure boom', 'https://www.bis.org/publications/qr-202603/financing-ai-infrastructure-boom-on-and-off-balance-sheet-borrowing', '2026-03'),
  credit: s('digital-credit', 'BIS · Financing the digital economy: the role of private credit', 'https://www.bis.org/publications/qr-202609/financing-digital-economy-role-private-credit', '2026-09'),
  depression: s('depression', 'Federal Reserve History · The Great Depression', 'https://www.federalreservehistory.org/essays/great-depression', '2013-11-22'),
  oil: s('oil', 'Federal Reserve History · Oil Shock of 1973–74', 'https://www.federalreservehistory.org/essays/oil-shock-of-1973-74', '2013-11-22'),
  crash: s('crash', 'Federal Reserve History · Stock Market Crash of 1987', 'https://www.federalreservehistory.org/essays/stock-market-crash-of-1987', '2013-11-22'),
  asia: s('asia', 'Federal Reserve History · Asian Financial Crisis', 'https://www.federalreservehistory.org/essays/asian-financial-crisis', '2013-11-22'),
  dotcom: s('dotcom', 'Federal Reserve · The revolution in information technology', 'https://www.federalreserve.gov/boarddocs/speeches/2000/20000306.htm', '2000-03-06'),
  gfc: s('gfc', 'Federal Reserve History · The Great Recession and Its Aftermath', 'https://www.federalreservehistory.org/essays/great-recession-and-its-aftermath', '2013-11-22'),
  pandemic: s('pandemic', 'IMF · World Economic Outlook: The Great Lockdown', 'https://www.imf.org/en/publications/weo/issues/2020/04/14/weo-april-2020', '2020-04-14'),
  housing: s('housing', 'BIS · Residential property prices 数据与口径', 'https://data.bis.org/topics/RPP', '持续更新；未导入观测值'),
  pending: { id: 'pending', title: 'Source pending · 原讨论、统计序列与研究文献待补', date: '待提供', accessedAt: '2026-10-07', status: 'Source pending' } as Source,
};
