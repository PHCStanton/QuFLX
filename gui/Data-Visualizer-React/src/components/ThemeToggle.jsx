import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

const ThemeToggle = () => {
  const { theme, toggleTheme, themes } = useTheme();

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-[var(--text-secondary)]">
        {themes[theme]}
      </span>
      <button
        onClick={toggleTheme}
        className="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--accent-blue)] focus:ring-offset-2 focus:ring-offset-[var(--card-bg)]"
        style={{
          backgroundColor: theme === 'cosmic-fire' ? 'var(--accent-orange)' : 'var(--accent-blue)'
        }}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full transition-transform ${
            theme === 'cosmic-fire' ? 'translate-x-6' : 'translate-x-1'
          }`}
          style={{
            backgroundColor: 'var(--text-primary)'
          }}
        />
      </button>
    </div>
  );
};

export default ThemeToggle;