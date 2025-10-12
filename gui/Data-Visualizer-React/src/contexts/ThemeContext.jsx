import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    // Load theme from localStorage or default to 'original'
    const savedTheme = localStorage.getItem('trading-dashboard-theme');
    return savedTheme || 'original';
  });

  const [systemPreference, setSystemPreference] = useState(() => {
    // Detect system dark mode preference
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    // Save theme to localStorage
    localStorage.setItem('trading-dashboard-theme', theme);
  }, [theme]);

  useEffect(() => {
    // Apply theme to document
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e) => setSystemPreference(e.matches);
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const toggleTheme = () => {
    setTheme(prev => prev === 'original' ? 'cosmic-fire' : 'original');
  };

  const setThemeByName = (themeName) => {
    if (['original', 'cosmic-fire'].includes(themeName)) {
      setTheme(themeName);
    }
  };

  const value = {
    theme,
    systemPreference,
    toggleTheme,
    setTheme: setThemeByName,
    themes: {
      original: 'Original',
      'cosmic-fire': 'Cosmic Fire'
    }
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};