import { useState, useEffect } from 'react';

const BREAKPOINTS = {
  xl: 1600,
  lg: 1280,
  md: 1024
};

const GRID_LAYOUTS = {
  xl: 'clamp(260px, 18vw, 360px) 1fr clamp(220px, 14vw, 320px)',
  lg: 'clamp(240px, 20vw, 320px) 1fr clamp(220px, 14vw, 300px)',
  md: 'clamp(220px, 22vw, 300px) 1fr clamp(220px, 16vw, 280px)',
  sm: 'minmax(200px, 220px) 1fr minmax(220px, 260px)',
  ssr: 'clamp(240px, 20vw, 320px) 1fr clamp(220px, 14vw, 300px)'
};

const getResponsiveColumns = () => {
  if (typeof window === 'undefined') return GRID_LAYOUTS.ssr;

  const width = window.innerWidth;
  if (width >= BREAKPOINTS.xl) return GRID_LAYOUTS.xl;
  if (width >= BREAKPOINTS.lg) return GRID_LAYOUTS.lg;
  if (width >= BREAKPOINTS.md) return GRID_LAYOUTS.md;
  return GRID_LAYOUTS.sm;
};

export const useResponsiveGrid = () => {
  const [gridColumns, setGridColumns] = useState(getResponsiveColumns());

  useEffect(() => {
    const handleResize = () => setGridColumns(getResponsiveColumns());
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return gridColumns;
};