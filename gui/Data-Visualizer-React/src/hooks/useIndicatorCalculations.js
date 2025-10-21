import { useState, useCallback, useEffect } from 'react';

/**
 * Hook for managing indicator calculations
 * Separates calculation logic from indicator state management
 */
export const useIndicatorCalculations = (socket) => {
  const [state, setState] = useState({
    data: null,
    error: null,
    isCalculating: false
  });

  const calculateIndicators = useCallback((asset, instances) => {
    if (!socket) {
      if (process.env.NODE_ENV === 'development') {
        console.log('[useIndicatorCalculations] calculateIndicators called but no socket available');
      }
      return;
    }

    if (process.env.NODE_ENV === 'development') {
      console.log('[useIndicatorCalculations] calculateIndicators called with:', { asset, instances });
    }
    setState(prev => ({ ...prev, isCalculating: true }));

    socket.emit('calculate_indicators', {
      asset,
      instances
    });
    if (process.env.NODE_ENV === 'development') {
      console.log('[useIndicatorCalculations] Emitted calculate_indicators event');
    }
  }, [socket]);

  if (process.env.NODE_ENV === 'development') {
    console.log('[useIndicatorCalculations] Socket ready:', !!socket);
  }
  // Handle indicator calculation results
  useEffect(() => {
    if (!socket) return;

    const handleIndicatorData = (data) => {
      setState({
        data,
        error: null,
        isCalculating: false
      });
    };

    const handleIndicatorError = (error) => {
      setState({
        data: null,
        error,
        isCalculating: false
      });
    };

    socket.on('indicators_calculated', handleIndicatorData);
    socket.on('indicators_error', handleIndicatorError);

    return () => {
      socket.off('indicators_calculated', handleIndicatorData);
      socket.off('indicators_error', handleIndicatorError);
    };
  }, [socket]);
  return {
    indicatorData: state.data,
    indicatorError: state.error,
    isCalculatingIndicators: state.isCalculating,
    calculateIndicators
  };
};