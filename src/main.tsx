import React from 'react';
import ReactDOM from 'react-dom/client';
import { HashRouter } from 'react-router-dom';
import { ThemeProvider } from './theme/theme';
import App from './app/App';
import './theme/styles.css';
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><ThemeProvider><HashRouter><App /></HashRouter></ThemeProvider></React.StrictMode>
);
