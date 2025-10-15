import React from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import Header from './components/Header';
import DataAnalysis from './pages/DataAnalysis';
import StrategyBacktest from './pages/StrategyBacktest';
import LiveTrading from './pages/LiveTrading';
import ComponentShowcase from './pages/ComponentShowcase';

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
          <Header />
          <nav
            className="glass text-slate-100 px-6 py-4 shadow-lg"
            style={{ borderColor: 'var(--card-border)' }}
          >
            <div className="w-full">
              <ul className="flex gap-8">
                <li>
                  <Link
                    to="/"
                    className="flex items-center gap-2 transition-colors font-medium"
                    style={{ color: 'var(--text-primary)' }}
                    onMouseEnter={(e) => e.target.style.color = 'var(--accent-blue)'}
                    onMouseLeave={(e) => e.target.style.color = 'var(--text-primary)'}
                  >
                    <span>📊</span>
                    <span>Data Analysis</span>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/strategy"
                    className="flex items-center gap-2 transition-colors font-medium"
                    style={{ color: 'var(--text-primary)' }}
                    onMouseEnter={(e) => e.target.style.color = 'var(--accent-blue)'}
                    onMouseLeave={(e) => e.target.style.color = 'var(--text-primary)'}
                  >
                    <span>🎯</span>
                    <span>Strategy & Backtest</span>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/live"
                    className="flex items-center gap-2 transition-colors font-medium"
                    style={{ color: 'var(--text-primary)' }}
                    onMouseEnter={(e) => e.target.style.color = 'var(--accent-blue)'}
                    onMouseLeave={(e) => e.target.style.color = 'var(--text-primary)'}
                  >
                    <span>🚀</span>
                    <span>Live Trading</span>
                  </Link>
                </li>
                <li>
                  <Link
                    to="/components"
                    className="flex items-center gap-2 transition-colors font-medium"
                    style={{ color: 'var(--text-primary)' }}
                    onMouseEnter={(e) => e.target.style.color = 'var(--accent-blue)'}
                    onMouseLeave={(e) => e.target.style.color = 'var(--text-primary)'}
                  >
                    <span>🎨</span>
                    <span>Components</span>
                  </Link>
                </li>
              </ul>
            </div>
          </nav>

          <div className="w-full p-6">
            <Routes>
              <Route path="/" element={<DataAnalysis />} />
              <Route path="/strategy" element={<StrategyBacktest />} />
              <Route path="/live" element={<LiveTrading />} />
              <Route path="/components" element={<ComponentShowcase />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;