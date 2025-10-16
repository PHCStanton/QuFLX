import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import Header from './components/Header';
import Navigation from './components/Navigation';
import ErrorBoundary from './components/ErrorBoundary';
import DataAnalysis from './pages/DataAnalysis';
import StrategyBacktest from './pages/StrategyBacktest';
import LiveTrading from './pages/LiveTrading';
import ComponentShowcase from './pages/ComponentShowcase';

const navigationItems = [
  { to: '/', icon: '📊', label: 'Data Analysis' },
  { to: '/strategy', icon: '🎯', label: 'Strategy & Backtest' },
  { to: '/live', icon: '🚀', label: 'Live Trading' },
  { to: '/components', icon: '🎨', label: 'Components' }
];

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <div className="min-h-screen" style={{ background: 'var(--bg-primary)' }}>
          <Header />
          <Navigation items={navigationItems} />

          <div className="w-full p-6">
            <ErrorBoundary>
              <Routes>
                <Route path="/" element={<DataAnalysis />} />
                <Route path="/strategy" element={<StrategyBacktest />} />
                <Route path="/live" element={<LiveTrading />} />
                <Route path="/components" element={<ComponentShowcase />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </ErrorBoundary>
          </div>
        </div>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;