import { createContext, useContext, useEffect, useState, type ReactNode, type CSSProperties } from 'react';
import { FluentProvider, webDarkTheme, webLightTheme } from '@fluentui/react-components';
export type ThemeMode = 'light' | 'dark' | 'system';
const ThemeContext = createContext({ mode: 'system' as ThemeMode, dark: false, setMode: (_: ThemeMode) => {} });
export const useTheme = () => useContext(ThemeContext);
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<ThemeMode>(() => {
    try { const m = localStorage.getItem('co-theme'); return m === 'light' || m === 'dark' ? m : 'system'; } catch { return 'system'; }
  });
  const [systemDark, setSystemDark] = useState(() => matchMedia('(prefers-color-scheme: dark)').matches);
  useEffect(() => { const m = matchMedia('(prefers-color-scheme: dark)'); const f = () => setSystemDark(m.matches); m.addEventListener('change', f); return () => m.removeEventListener('change', f); }, []);
  const dark = mode === 'dark' || (mode === 'system' && systemDark);
  useEffect(() => { try { localStorage.setItem('co-theme', mode); } catch { /* preference unavailable */ } document.documentElement.style.colorScheme = dark ? 'dark' : 'light'; document.querySelector('meta[name="theme-color"]')?.setAttribute('content', dark ? '#141518' : '#f5f6f8'); }, [mode, dark]);
  const theme = dark ? webDarkTheme : webLightTheme;
  const vars = Object.fromEntries(Object.entries(theme).map(([k, v]) => [`--${k}`, v])) as CSSProperties;
  return <ThemeContext.Provider value={{ mode, dark, setMode }}><FluentProvider theme={theme} style={vars} className={dark ? 'theme-root dark' : 'theme-root'}>{children}</FluentProvider></ThemeContext.Provider>;
}
