import React from 'react';

const ConnectionStatus = ({
  isConnected,
  isConnecting,
  chromeConnected,
  backendReconnected,
  chromeReconnected
}) => {
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        <div
          className="w-2 h-2 rounded-full"
          style={{
            backgroundColor: isConnected ? 'var(--accent-green)' : isConnecting ? 'var(--accent-orange)' : 'var(--accent-red)'
          }}
        ></div>
        <span
          className="text-xs"
          style={{ color: 'var(--text-muted)' }}
        >Backend: {isConnected ? 'Connected' : isConnecting ? 'Connecting...' : 'Disconnected'}</span>
      </div>
      <div className="flex items-center gap-2">
        <div
          className="w-2 h-2 rounded-full"
          style={{
            backgroundColor: chromeConnected ? 'var(--accent-green)' : 'var(--accent-orange)'
          }}
        ></div>
        <span
          className="text-xs"
          style={{ color: 'var(--text-muted)' }}
        >Chrome: {chromeConnected ? 'Connected' : 'Not Connected'}</span>
      </div>
      {backendReconnected && (
        <div className="flex items-center gap-1 px-2 py-1 bg-blue-500/20 border border-blue-500/50 rounded-md">
          <svg className="w-3 h-3 text-blue-400 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span className="text-xs text-blue-400 font-medium">Backend Reconnected</span>
        </div>
      )}
      {chromeReconnected && (
        <div className="flex items-center gap-1 px-2 py-1 bg-green-500/20 border border-green-500/50 rounded-md">
          <svg className="w-3 h-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"></path>
          </svg>
          <span className="text-xs text-green-400 font-medium">Chrome Reconnected</span>
        </div>
      )}
    </div>
  );
};

export default ConnectionStatus;