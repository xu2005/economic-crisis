import { lazy, Suspense, useEffect, useState, Component, type ReactNode } from 'react';
import { NavLink, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { Button, Tooltip, Select, Spinner, OverlayDrawer, DrawerHeader, DrawerHeaderTitle, DrawerBody, Dialog, DialogSurface, DialogBody, DialogTitle, DialogContent, Input } from '@fluentui/react-components';
import { Home24Regular, DataTrending24Regular, BrainCircuit24Regular, Globe24Regular, BuildingGovernment24Regular, Building24Regular, People24Regular, History24Regular, Beaker24Regular, Shield24Regular, Notebook24Regular, BookOpen24Regular, Search24Regular, PanelLeftContract24Regular, PanelLeftExpand24Regular, Navigation24Regular, Dismiss24Regular, WeatherMoon24Regular, ArrowClockwise24Regular } from '@fluentui/react-icons';
import { useTheme, type ThemeMode } from '../theme/theme';
import { research } from '../content/research';
import { cases } from '../content/cases';
import { notes } from '../content/notes';
import { models, indicators } from '../data/registry';
import Overview from '../pages/Overview';
const ResearchPages = lazy(() => import('../pages/ResearchPages'));
const HistoryPages = lazy(() => import('../pages/HistoryPages'));
const ModelPages = lazy(() => import('../pages/ModelPages'));
const SystemPages = lazy(() => import('../pages/SystemPages'));
const nav = [
  { path: '/', label: '研究总览', en: 'Overview', icon: Home24Regular },
  { path: '/system', label: '危机系统', en: 'Crisis system', icon: DataTrending24Regular },
  { path: '/ai', label: 'AI资本周期', en: 'AI capital cycle', icon: BrainCircuit24Regular },
  { path: '/global', label: '全球经济', en: 'Global economy', icon: Globe24Regular },
  { path: '/us', label: '美国财政与美元', en: 'United States', icon: BuildingGovernment24Regular, sub: true },
  { path: '/china', label: '中国经济', en: 'China', icon: Building24Regular, sub: true },
  { path: '/housing', label: '全球房地产', en: 'Housing', icon: Building24Regular, sub: true },
  { path: '/labour', label: '劳动与生活水平', en: 'Labour', icon: People24Regular, sub: true },
  { path: '/demography', label: '人口与再生产', en: 'Demography', icon: People24Regular, sub: true },
  { path: '/history', label: '历史危机', en: 'History', icon: History24Regular },
  { path: '/models', label: '模型实验室', en: 'Model lab', icon: Beaker24Regular },
  { path: '/resilience', label: '个人危机应对', en: 'Resilience', icon: Shield24Regular },
  { path: '/notes', label: '研究笔记', en: 'Research notes', icon: Notebook24Regular },
  { path: '/methodology', label: '研究方法', en: 'Methodology', icon: BookOpen24Regular },
];
export const searchIndex = [
  {id:'cny-implementability',title:'V3.2人民币税后可实施性',text:'税收 QDII 汇率 溢价 人民币 普通账户 摩擦 再平衡',kind:'模型',path:'/models/hs300/cny-implementability'},
  { id: 'hs300-crisis-v3', title: '沪深300 · V3资产选择优先', text: 'V3 固定风险预算 跨资产 国债 黄金 全球股票 退役状态机', kind: '模型', path: '/models/hs300/crisis-v3' },
  { id: 'hs300-implementation', title: '危机资本 · V3.2实施资格', text: 'V3.2 产品映射 数据管道 每日 资格 8项 硬门槛', kind: '模型', path: '/models/hs300/implementation-qualification' },
  { id: 'hs300-crisis-freeze', title: '危机资本 · V3.1冻结审计', text: 'V3.1 Freeze 大陆产品 QDII 费用 汇率 溢价 样本外 强基准', kind: '模型', path: '/models/hs300/crisis-freeze' },
  { id: 'hs300-crisis-validation', title: '沪深300 · 危机算法验证', text: '15年 大跌 买入 修复 获利 原文 成本 PB 时间门控 退出', kind: '模型', path: '/models/hs300/crisis-validation' },
  { id: 'hs300-backtest', title: '沪深300 · 预算核心回测', text: '历史数据 算法正确性 幂律 资金守恒 上证指数 回撤 交易记录', kind: '模型', path: '/models/hs300/backtest' },
  ...research.map(x => ({ id: 'r-' + x.id, title: x.title, text: [x.subtitle, x.summary, ...x.topics, ...x.regions, ...x.sections.flatMap(s => [s.title, ...s.text, ...(s.points || [])])].join(' '), kind: '研究', path: '/research/' + x.id })),
  ...cases.map(x => ({ id: 'c-' + x.id, title: x.year + ' · ' + x.title, text: x.subtitle + ' ' + x.summary, kind: '案例', path: '/history/' + x.id })),
  ...models.map(x => ({ id: 'm-' + x.id, title: x.title, text: x.subtitle + ' ' + x.purpose, kind: '模型', path: x.path })),
  ...notes.map(x => ({ id: 'n-' + x.id, title: x.title, text: x.body.join(' '), kind: '笔记', path: '/notes/' + x.id })),
  ...indicators.map(x => ({ id: 'i-' + x.id, title: x.label, text: x.notes + ' ' + x.source, kind: '指标', path: '/indicators?focus=' + x.id })),
];
class PageBoundary extends Component<{ children: ReactNode; route: string }, { error: boolean }> {
  state = { error: false }; static getDerivedStateFromError() { return { error: true }; }
  componentDidUpdate(previous: { route: string }) { if (previous.route !== this.props.route && this.state.error) this.setState({ error: false }); }
  render() { return this.state.error ? <div className="empty-state"><h1>页面暂时无法载入</h1><p>请检查网络或刷新页面。研究源文件仍保留在项目中。</p><Button icon={<ArrowClockwise24Regular />} onClick={() => location.reload()}>重新加载</Button></div> : this.props.children; }
}
function Search({ open, close }: { open: boolean; close: () => void }) {
  const [query, setQuery] = useState(''); const navigate = useNavigate();
  const q = query.trim().toLocaleLowerCase();
  const results = q ? searchIndex.filter(x => (x.title + ' ' + x.text).toLocaleLowerCase().includes(q)) : searchIndex.filter(x => x.kind === '模型').concat(searchIndex.filter(x => x.kind === '研究').slice(0, 4));
  useEffect(() => { if (!open) setQuery(''); }, [open]);
  return <Dialog open={open} onOpenChange={(_, d) => { if (!d.open) close(); }}><DialogSurface className="search-dialog"><DialogBody><DialogTitle action={<Button aria-label="关闭搜索" icon={<Dismiss24Regular />} appearance="subtle" onClick={close} />}>搜索研究工作台</DialogTitle><DialogContent><form onSubmit={e => { e.preventDefault(); if (results[0]) { navigate(results[0].path); close(); } }}><Input autoFocus contentBefore={<Search24Regular />} placeholder="研究、模型、历史、笔记或指标" aria-label="搜索关键词" value={query} onChange={(_, d) => setQuery(d.value)} className="search-input" /></form><p className="meta">{q ? `找到 ${results.length} 条结果` : '常用入口'} · Enter打开首项 · Tab选择 · Esc关闭</p><div className="search-results">{results.map(r => <Button key={r.id} appearance="subtle" onClick={() => { navigate(r.path); close(); }}><span><strong>{r.title}</strong><small>{r.kind}</small></span></Button>)}{!results.length && <div className="empty-state">没有匹配的内容。可以尝试“AI”“信用”或“劳动”。</div>}</div></DialogContent></DialogBody></DialogSurface></Dialog>;
}
export default function App() {
  const { mode, setMode } = useTheme(); const [collapsed, setCollapsed] = useState(false); const [drawer, setDrawer] = useState(false); const [search, setSearch] = useState(false); const [offline, setOffline] = useState(!navigator.onLine); const location = useLocation();
  const title = nav.find(x => x.path === location.pathname)?.label || research.find(x => '/research/' + x.id === location.pathname)?.title || models.find(x => x.path === location.pathname)?.title || (location.pathname.startsWith('/history/') ? '历史案例' : location.pathname.startsWith('/notes/') ? '研究笔记' : location.pathname === '/models/hs300/crisis-v3' ? '沪深300 · V3资产选择优先' : location.pathname === '/models/hs300/crisis-validation' ? '沪深300 · 危机算法验证' : location.pathname === '/models/hs300/backtest' ? '沪深300 · 预算核心回测' : location.pathname === '/indicators' ? '指标登记册' : '研究工作台');
  useEffect(() => { document.title = title + ' · Crisis Observatory'; setDrawer(false); window.scrollTo(0, 0); }, [location.pathname, title]);
  useEffect(() => {
    const key = (e: KeyboardEvent) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setSearch(v => !v); } };
    const online = () => setOffline(!navigator.onLine);
    const anchorClick = (e: MouseEvent) => {
      const link = (e.target as Element)?.closest('a'); const href = link?.getAttribute('href');
      if (href?.startsWith('#') && !href.startsWith('#/')) {
        const target = document.getElementById(href.slice(1));
        if (target) { e.preventDefault(); target.scrollIntoView({ block: 'start' }); if (target.id === 'main') target.focus(); }
      }
    };
    window.addEventListener('keydown', key); window.addEventListener('online', online); window.addEventListener('offline', online); document.addEventListener('click', anchorClick);
    return () => { window.removeEventListener('keydown', key); window.removeEventListener('online', online); window.removeEventListener('offline', online); document.removeEventListener('click', anchorClick); };
  }, []);
  const navigation = <nav aria-label="主导航">{nav.map(n => <Tooltip key={n.path} content={n.label} relationship="label" positioning="after"><NavLink to={n.path} end={n.path === '/'} className={({ isActive }) => `nav-item ${n.sub ? 'sub' : ''} ${isActive ? 'active' : ''}`}><n.icon /><span>{n.label}</span></NavLink></Tooltip>)}</nav>;
  return <div className={`app-shell ${collapsed ? 'collapsed' : ''}`}><a className="skip-link" href="#main">跳转到主内容</a><header className="global-header"><div className="brand"><img src="./favicon.svg" alt="" /><span>Crisis Observatory</span></div><Button className="mobile-menu" icon={<Navigation24Regular />} appearance="subtle" aria-label="打开全部导航" onClick={() => setDrawer(true)} /><div className="mobile-title">{title}</div><span className="header-divider" /><span className="header-subtitle">经济危机研究室</span><div className="header-actions"><Button icon={<Search24Regular />} className="search-launch" appearance="subtle" onClick={() => setSearch(true)} aria-label="搜索研究内容"><span>搜索工作台</span><kbd>Ctrl K</kbd></Button><div className="theme-control"><WeatherMoon24Regular /><Select aria-label="颜色主题" value={mode} onChange={(_, d) => setMode(d.value as ThemeMode)}><option value="light">亮色</option><option value="dark">暗色</option><option value="system">跟随系统</option></Select></div></div></header><aside className="sidebar"><div className="sidebar-heading"><span>研究工作台</span><Button appearance="subtle" size="small" icon={collapsed ? <PanelLeftExpand24Regular /> : <PanelLeftContract24Regular />} aria-label={collapsed ? '展开导航' : '收起导航'} onClick={() => setCollapsed(v => !v)} /></div>{navigation}<div className="sidebar-footer"><span className="eyebrow">PERSONAL RESEARCH</span><p>证据先于判断<br />模型保持开放</p><span className="meta">v0.1 · 2026-10-07</span></div></aside><OverlayDrawer position="start" open={drawer} onOpenChange={(_, d) => setDrawer(d.open)} className="nav-drawer"><DrawerHeader><DrawerHeaderTitle action={<Button aria-label="关闭导航" appearance="subtle" icon={<Dismiss24Regular />} onClick={() => setDrawer(false)} />}>研究工作台</DrawerHeaderTitle></DrawerHeader><DrawerBody>{navigation}</DrawerBody></OverlayDrawer><main id="main" tabIndex={-1}>{offline && <div className="offline-note" role="status">当前离线 · 已加载的内容与本地计算可用；外部来源和未缓存页面可能不可访问。</div>}<PageBoundary route={location.pathname}><Suspense fallback={<div className="page-loading"><Spinner label="加载研究内容" /></div>}><Routes><Route path="/" element={<Overview />} /><Route path="/research/*" element={<ResearchPages />} /><Route path="/history/*" element={<HistoryPages />} /><Route path="/models/*" element={<ModelPages />} />{['/system', '/ai', '/global', '/us', '/china', '/housing', '/labour', '/demography', '/resilience', '/methodology', '/indicators', '/notes/*', '/timeline'].map(path => <Route key={path} path={path} element={<SystemPages />} />)}<Route path="*" element={<div className="empty-state"><h1>页面不存在</h1><p>这个入口可能已更新。</p><NavLink to="/">返回研究总览</NavLink></div>} /></Routes></Suspense></PageBoundary><footer className="site-footer"><span>Crisis Observatory · 经济危机研究室</span><span>研究框架 / 非实时判断 · <NavLink to="/methodology">方法与边界</NavLink></span></footer></main><nav className="bottom-nav" aria-label="移动端快捷导航">{[{ to: '/', name: '总览', icon: Home24Regular }, { to: '/research', name: '研究', icon: BookOpen24Regular }, { to: '/models', name: '模型', icon: Beaker24Regular }, { to: '/history', name: '历史', icon: History24Regular }].map(n => <NavLink key={n.to} to={n.to} end={n.to === '/'}><n.icon /><span>{n.name}</span></NavLink>)}<Button appearance="subtle" icon={<Navigation24Regular />} onClick={() => setDrawer(true)}>更多</Button></nav><Search open={search} close={() => setSearch(false)} /></div>;
}
