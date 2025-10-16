import React, { useRef, useEffect, useState } from 'react';
import LightweightChart from './charts/LightweightChart';
import ErrorBoundary from './ErrorBoundary';
import { RealTimeDataStream } from '../utils/realTimeData';

/**
 * Real-time trading chart component with live data streaming
 * Demonstrates TradingView Lightweight Charts real-time capabilities
 */
const RealTimeChart = ({ 
  initialData = [], 
  updateInterval = 1000,
  enabledIndicators = {},
  height = 400,
  className = ''
}) => {
  const chartRef = useRef(null);
  const streamRef = useRef(null);
  const [data, setData] = useState(initialData);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStats, setStreamStats] = useState({
    dataPoints: 0,
    updateInterval: updateInterval,
    lastUpdate: null
  });

  // Initialize real-time data stream
  useEffect(() => {
    if (!streamRef.current) {
      streamRef.current = new RealTimeDataStream(initialData, updateInterval);
      
      // Subscribe to data updates
      const unsubscribe = streamRef.current.subscribe((newPoint, allData) => {
        setData(allData);
        setStreamStats({
          dataPoints: allData.length,
          updateInterval: streamRef.current.updateInterval,
          lastUpdate: new Date().toLocaleTimeString()
        });
        
        // Update chart with new data point
        if (chartRef.current && isStreaming) {
          chartRef.current.addDataPoint(newPoint);
        }
      });
      
      return () => {
        unsubscribe();
        if (streamRef.current) {
          streamRef.current.destroy();
        }
      };
    }
  }, [initialData, updateInterval, isStreaming]);

  // Start streaming
  const startStreaming = () => {
    if (streamRef.current && !isStreaming) {
      streamRef.current.startStreaming();
      setIsStreaming(true);
    }
  };

  // Stop streaming
  const stopStreaming = () => {
    if (streamRef.current && isStreaming) {
      streamRef.current.stopStreaming();
      setIsStreaming(false);
    }
  };

  // Update streaming interval
  const handleIntervalChange = (newInterval) => {
    if (streamRef.current) {
      streamRef.current.setUpdateInterval(newInterval);
      setStreamStats(prev => ({ ...prev, updateInterval: newInterval }));
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.destroy();
      }
    };
  }, []);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Real-time Controls */}
      <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Real-Time Data Stream</h3>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${
              isStreaming ? 'bg-green-500 animate-pulse' : 'bg-gray-500'
            }`} />
            <span className="text-sm text-slate-300">
              {isStreaming ? 'Live' : 'Stopped'}
            </span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="bg-slate-700/50 rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-1">Data Points</div>
            <div className="text-lg font-semibold text-white">{streamStats.dataPoints}</div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-1">Update Interval</div>
            <div className="text-lg font-semibold text-white">{streamStats.updateInterval}ms</div>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-3">
            <div className="text-xs text-slate-400 mb-1">Last Update</div>
            <div className="text-lg font-semibold text-white">
              {streamStats.lastUpdate || 'Never'}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex gap-2">
            <button
              onClick={startStreaming}
              disabled={isStreaming}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
            >
              Start Stream
            </button>
            <button
              onClick={stopStreaming}
              disabled={!isStreaming}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
            >
              Stop Stream
            </button>
          </div>
          
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-300">Interval:</label>
            <select
              value={streamStats.updateInterval}
              onChange={(e) => handleIntervalChange(Number(e.target.value))}
              className="bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm text-white"
            >
              <option value={500}>500ms</option>
              <option value={1000}>1s</option>
              <option value={2000}>2s</option>
              <option value={5000}>5s</option>
            </select>
          </div>
        </div>
      </div>
      
      {/* Real-time Chart */}
      <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-4">
        <ErrorBoundary>
          <LightweightChart
            ref={chartRef}
            data={data}
            enabledIndicators={enabledIndicators}
            height={height}
            enableRealTime={true}
            className="w-full"
          />
        </ErrorBoundary>
      </div>
    </div>
  );
};

export default RealTimeChart;