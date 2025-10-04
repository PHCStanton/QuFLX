import React from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom';
import Header from './components/Header';
import DataAnalysis from './pages/DataAnalysis';
import StrategyBacktest from './pages/StrategyBacktest';
import LiveTrading from './pages/LiveTrading';

function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
        <Header />
        <nav className="bg-slate-800/80 backdrop-blur-sm text-slate-100 px-6 py-4 shadow-lg border-b border-slate-700">
          <div className="max-w-7xl mx-auto">
            <ul className="flex gap-8">
              <li>
                <Link 
                  to="/" 
                  className="flex items-center gap-2 hover:text-blue-400 transition-colors font-medium"
                >
                  <span>📊</span>
                  <span>Data Analysis</span>
                </Link>
              </li>
              <li>
                <Link 
                  to="/strategy" 
                  className="flex items-center gap-2 hover:text-blue-400 transition-colors font-medium"
                >
                  <span>🎯</span>
                  <span>Strategy & Backtest</span>
                </Link>
              </li>
              <li>
                <Link 
                  to="/live" 
                  className="flex items-center gap-2 hover:text-blue-400 transition-colors font-medium"
                >
                  <span>🚀</span>
                  <span>Live Trading</span>
                </Link>
              </li>
            </ul>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto p-6">
          <Routes>
            <Route path="/" element={<DataAnalysis />} />
            <Route path="/strategy" element={<StrategyBacktest />} />
            <Route path="/live" element={<LiveTrading />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;