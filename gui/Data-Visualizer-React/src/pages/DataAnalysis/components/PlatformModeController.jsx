import React from 'react';

// Simplified 3-state machine for Platform mode
const PLATFORM_STATES = {
  DISCONNECTED: 'disconnected',  // Chrome not available
  READY: 'ready',                // Connected, can start
  STREAMING: 'streaming'         // Active stream
};

const PlatformModeController = ({
  streamState,
  streamError,
  detectedAsset,
  chromeConnected,
  handleDetectAsset,
  handleStartStream,
  handleStopStream,
  isDetecting
}) => {
  return (
    <div>
      <label
        className="block text-sm font-medium mb-2"
        style={{ color: 'var(--text-secondary)' }}
      >
        Stream Controls
      </label>
      <div
        className="glass border rounded-lg p-4 space-y-3"
        style={{ borderColor: 'var(--card-border)' }}
      >
        {/* Stream State Display */}
        {streamState === PLATFORM_STATES.DISCONNECTED && (
          <div className="flex items-center gap-2 text-yellow-400">
            <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
            <span className="text-sm">Waiting for Chrome connection...</span>
          </div>
        )}

        {streamState === PLATFORM_STATES.READY && chromeConnected && (
          <button
            onClick={handleDetectAsset}
            disabled={isDetecting}
            className="w-full px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
            style={{
              backgroundColor: 'var(--accent-purple)',
              color: 'var(--text-primary)'
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--accent-blue)'}
            onMouseLeave={(e) => e.target.style.backgroundColor = 'var(--accent-purple)'}
          >
            {isDetecting ? 'Detecting...' : 'Detect Asset from PocketOption'}
          </button>
        )}

        {streamState === PLATFORM_STATES.READY && !chromeConnected && (
          <div className="flex items-center gap-2 text-orange-400">
            <div className="w-2 h-2 rounded-full bg-orange-500"></div>
            <span className="text-sm">Chrome not connected</span>
          </div>
        )}

        {streamState === 'asset_detected' && detectedAsset && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-green-400">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"></path>
              </svg>
              <span className="text-sm font-medium">Detected: {detectedAsset}</span>
            </div>
            <button
              onClick={handleStartStream}
              className="w-full px-4 py-2 rounded-lg font-medium transition-colors"
              style={{
                backgroundColor: 'var(--accent-green)',
                color: 'var(--text-primary)'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--accent-blue)'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'var(--accent-green)'}
            >
              Start Stream
            </button>
          </div>
        )}

        {streamState === PLATFORM_STATES.STREAMING && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-green-400">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              <span className="text-sm font-medium">Streaming: {detectedAsset}</span>
            </div>
            <button
              onClick={handleStopStream}
              className="w-full px-4 py-2 rounded-lg font-medium transition-colors"
              style={{
                backgroundColor: 'var(--accent-red)',
                color: 'var(--text-primary)'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--accent-purple)'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'var(--accent-red)'}
            >
              Stop Stream
            </button>
          </div>
        )}

        {streamError && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-red-400">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"></path>
              </svg>
              <span className="text-sm">{streamError}</span>
            </div>
            <button
              onClick={handleDetectAsset}
              className="w-full px-4 py-2 rounded-lg font-medium transition-colors"
              style={{
                backgroundColor: 'var(--accent-purple)',
                color: 'var(--text-primary)'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--accent-blue)'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'var(--accent-purple)'}
            >
              Retry Detection
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PlatformModeController;