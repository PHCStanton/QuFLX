import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { SidebarProvider, useSidebar } from './contexts/SidebarContext';
import Sidebar from './components/Sidebar';
import ErrorBoundary from './components/ErrorBoundary';
import DataAnalysis from './pages/DataAnalysis';
import StrategyBacktest from './pages/StrategyBacktest';
import LiveTrading from './pages/LiveTrading';
import Components from './pages/Components';

const AppLayout = () => {
  const { sidebarWidth } = useSidebar();

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-primary)', display: 'flex' }}>
      <Sidebar />

      <div style={{ 
        marginLeft: `${sidebarWidth}px`, 
        flex: 1, 
        padding: '24px', 
        transition: 'margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        minHeight: '100vh'
      }}>
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<DataAnalysis />} />
            <Route path="/backtest" element={<StrategyBacktest />} />
            <Route path="/live" element={<LiveTrading />} />
            <Route path="/components" element={<Components />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ErrorBoundary>
      </div>
    </div>
  );
};

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <SidebarProvider>
          <AppLayout />
        </SidebarProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;