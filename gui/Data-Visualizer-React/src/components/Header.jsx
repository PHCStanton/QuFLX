import React, { useState } from 'react';
import ThemeToggle from './ThemeToggle';

const Header = () => {
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  return (
    <header className="glass border-b" style={{ borderColor: 'var(--card-border)' }}>
      <div className="flex justify-between items-center px-6 py-3">
        <div className="flex items-center space-x-3">
          <img
            src="/logo.svg"
            alt="Trading Analytics Logo"
            className="h-10 w-10 object-contain"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
          <div className="text-xl font-bold" style={{ color: 'var(--accent-blue)' }}>Quantum_Flux v.2.2.0</div>
        </div>
        <div className="flex items-center space-x-4">
          <ThemeToggle />
          <button
            className="p-2 rounded-full glass-hover"
            style={{
              '--hover-bg': 'var(--glass-bg)',
              '--hover-border': 'var(--glass-border)'
            }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" style={{ color: 'var(--text-secondary)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </button>
          <div className="relative">
            <button
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              className="flex items-center focus:outline-none glass-hover rounded-full p-1"
            >
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center font-bold"
                style={{
                  backgroundColor: 'var(--accent-blue)',
                  color: 'var(--text-primary)'
                }}
              >
                U
              </div>
            </button>
            {isProfileOpen && (
              <div
                className="absolute right-0 mt-2 w-48 glass rounded-md shadow-lg py-1 z-10"
                style={{ borderColor: 'var(--card-border)' }}
              >
                <a href="#" className="block px-4 py-2 text-sm hover:bg-slate-700/50 transition-colors" style={{ color: 'var(--text-primary)' }}>Your Profile</a>
                <a href="#" className="block px-4 py-2 text-sm hover:bg-slate-700/50 transition-colors" style={{ color: 'var(--text-primary)' }}>Settings</a>
                <a href="#" className="block px-4 py-2 text-sm hover:bg-slate-700/50 transition-colors" style={{ color: 'var(--text-primary)' }}>Sign out</a>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;