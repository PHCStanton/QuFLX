import { useState, useCallback, useEffect } from 'react';
import { formatIndicatorInstances } from '../utils/indicatorUtils';

/**
 * Custom hook for managing indicator state and calculations
 * Centralizes indicator logic and ensures backend-driven calculations
 */
export const useIndicators = ({ 
  asset,
  isConnected,
  calculateIndicators,
  indicatorData,
  indicatorError,
  isCalculatingIndicators 
}) => {
  // Store active indicators with their configurations
  const [activeIndicators, setActiveIndicators] = useState({});

  // Trigger backend calculation whenever indicators change
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log('[useIndicators] useEffect triggered', { isConnected, asset, activeIndicatorsCount: Object.keys(activeIndicators).length });
    }
    if (!isConnected || !asset) {
      if (process.env.NODE_ENV === 'development') {
        console.log('[useIndicators] Skipping calculation - missing connection or asset');
      }
      return;
    }

    try {
      const instances = formatIndicatorInstances(activeIndicators);
      if (process.env.NODE_ENV === 'development') {
        console.log('[useIndicators] Formatted instances:', instances);
      }
      if (Object.keys(instances).length > 0) {
        if (process.env.NODE_ENV === 'development') {
          console.log('[useIndicators] Triggering calculateIndicators with', instances);
        }
        calculateIndicators(asset, instances);
      } else {
        if (process.env.NODE_ENV === 'development') {
          console.log('[useIndicators] No instances to calculate');
        }
      }
    } catch (error) {
      console.error('[useIndicators] Error in indicator calculation:', error);
    }
  }, [isConnected, asset, activeIndicators, calculateIndicators]);

  // Add or update indicator instance
  const addIndicator = useCallback((config) => {
    if (process.env.NODE_ENV === 'development') {
      console.log('[useIndicators] addIndicator called with:', config);
    }
    const { instanceName, type, params, definition } = config;

    setActiveIndicators(prev => ({
      ...prev,
      [instanceName]: {
        type,
        params,
        color: definition.color,
        definition
      }
    }));
    if (process.env.NODE_ENV === 'development') {
      console.log('[useIndicators] Indicator added:', instanceName);
    }
  }, []);

  // Remove indicator instance
  const removeIndicator = useCallback((instanceName) => {
    setActiveIndicators(prev => {
      const { [instanceName]: removed, ...remaining } = prev;
      return remaining;
    });
  }, []);

  // Get indicator data in a standardized format
  const getIndicatorData = useCallback((instanceName) => {
    if (!indicatorData?.indicators?.[instanceName]) return null;

    const indicator = indicatorData.indicators[instanceName];
    if (!indicator) return null;

    // Get all numeric values from the indicator
    const values = Object.entries(indicator)
      .filter(([key, val]) =>
        typeof val === 'number' &&
        !['time', 'timestamp'].includes(key)
      )
      .reduce((acc, [key, val]) => ({
        ...acc,
        [key]: val.toFixed(2)
      }), {});

    // Get series data if available
    const series = indicatorData?.series?.[instanceName] || null;

    return {
      type: indicator.type,
      values,
      signal: indicator.signal || null,
      series,
      metadata: {
        ...indicator,
        values: undefined,
        signal: undefined,
        type: undefined,
        time: undefined,
        timestamp: undefined
      }
    };
  }, [indicatorData]);

  // Format indicator reading for display
  const formatIndicatorReading = useCallback((instanceName) => {
    const data = getIndicatorData(instanceName);
    if (!data) return null;

    // Get primary value based on indicator type
    const primaryValue = data.values.value ||
                        data.values.close ||
                        Object.values(data.values)[0] ||
                        null;

    if (primaryValue === null) return null;

    return {
      value: primaryValue,
      signal: data.signal,
      type: data.type,
      additionalValues: Object.entries(data.values)
        .filter(([key]) => key !== 'value' && key !== 'close')
        .reduce((acc, [key, val]) => ({
          ...acc,
          [key]: val
        }), {})
    };
  }, [getIndicatorData]);

  return {
    // State
    activeIndicators,
    indicatorData,
    indicatorError,
    isCalculatingIndicators,

    // Actions
    addIndicator,
    removeIndicator,
    
    // Getters
    getIndicatorData,
    formatIndicatorReading
  };
};