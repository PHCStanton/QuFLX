import React, { useState, useEffect } from 'react';
import { strategyService } from '../services/StrategyService';
import { colors, typography, spacing, borderRadius, components } from '../styles/designTokens';

const StrategyBacktest = () => {
  const [strategies, setStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState('quantum_flux');
  const [dataFiles, setDataFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState('');
  const [backtestResults, setBacktestResults] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [config, setConfig] = useState({
    initialCapital: 10000,
    positionSize: 1
  });

  const getResponsiveColumns = () => {
    if (typeof window === 'undefined') return '20% 65% 15%';
    const width = window.innerWidth;
    if (width >= 1280) return '20% 65% 15%';
    if (width >= 1024) return '22% 60% 18%';
    return '20% 65% 15%';
  };

  const [gridColumns, setGridColumns] = useState(getResponsiveColumns());

  useEffect(() => {
    const handleResize = () => setGridColumns(getResponsiveColumns());
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    strategyService.initializeSocket();
    loadDataFiles();
    setStrategies([
      { id: 'quantum_flux', name: 'Quantum Flux', type: 'python', status: 'active' }
    ]);
  }, []);

  const loadDataFiles = async () => {
    const result = await strategyService.getAvailableDataFiles();
    if (result.success) {
      setDataFiles(result.files);
      if (result.files.length > 0) {
        setSelectedFile(result.files[0].path);
      }
    }
  };

  const runBacktest = async () => {
    if (!selectedFile || !selectedStrategy) {
      alert('Please select a strategy and data file');
      return;
    }

    setIsRunning(true);
    setBacktestResults(null);

    try {
      const result = await strategyService.runBacktest(selectedStrategy, selectedFile, config);
      
      if (result.success) {
        setBacktestResults(result.results);
      } else {
        alert(`Backtest failed: ${result.error}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const containerStyle = {
    display: 'grid',
    gridTemplateColumns: gridColumns,
    gap: spacing.lg,
    padding: spacing.lg,
    minHeight: 'calc(100vh - 120px)',
  };

  const cardStyle = {
    background: colors.cardBg,
    border: `1px solid ${colors.cardBorder}`,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
  };

  const selectStyle = {
    width: '100%',
    padding: spacing.md,
    background: colors.bgSecondary,
    border: `1px solid ${colors.cardBorder}`,
    borderRadius: borderRadius.lg,
    color: colors.textPrimary,
    fontSize: typography.fontSize.sm,
    fontFamily: typography.fontFamily.sans,
    outline: 'none',
  };

  const inputStyle = {
    width: '100%',
    padding: spacing.md,
    background: colors.bgSecondary,
    border: `1px solid ${colors.cardBorder}`,
    borderRadius: borderRadius.lg,
    color: colors.textPrimary,
    fontSize: typography.fontSize.sm,
    fontFamily: typography.fontFamily.sans,
    outline: 'none',
  };

  return (
    <div style={containerStyle}>
      {/* LEFT COLUMN - Strategy Selector & Config */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
        {/* Strategy Selector */}
        <div style={cardStyle}>
          <h3 style={{ 
            margin: 0, 
            marginBottom: spacing.md,
            fontSize: typography.fontSize.lg, 
            fontWeight: typography.fontWeight.semibold,
            color: colors.textPrimary 
          }}>
            Strategy Selector
          </h3>
          
          <div style={{
            padding: spacing.md,
            background: colors.accentGreen,
            borderRadius: borderRadius.lg,
            marginBottom: spacing.md,
            cursor: 'pointer',
          }}>
            <div style={{ 
              fontSize: typography.fontSize.base,
              fontWeight: typography.fontWeight.medium,
              color: '#000',
            }}>
              Quantum Flux
            </div>
          </div>
        </div>

        {/* Data Files */}
        <div style={cardStyle}>
          <label style={{ 
            display: 'block',
            marginBottom: spacing.sm,
            fontSize: typography.fontSize.sm,
            fontWeight: typography.fontWeight.medium,
            color: colors.textPrimary 
          }}>
            Data Files
          </label>
          <select value={selectedFile} onChange={(e) => setSelectedFile(e.target.value)} style={selectStyle}>
            {dataFiles.length === 0 ? (
              <option>CSV Pick</option>
            ) : (
              dataFiles.map((file, index) => (
                <option key={file.path || index} value={file.path}>
                  {file.asset} - {file.timeframe}
                </option>
              ))
            )}
          </select>
        </div>

        {/* Capital, Risk */}
        <div style={cardStyle}>
          <label style={{ 
            display: 'block',
            marginBottom: spacing.sm,
            fontSize: typography.fontSize.sm,
            fontWeight: typography.fontWeight.medium,
            color: colors.textPrimary 
          }}>
            Capital, Risk
          </label>
          <select style={selectStyle}>
            <option>Parameter</option>
          </select>
        </div>

        {/* Backtest Config */}
        <div style={cardStyle}>
          <label style={{ 
            display: 'block',
            marginBottom: spacing.sm,
            fontSize: typography.fontSize.sm,
            fontWeight: typography.fontWeight.medium,
            color: colors.textPrimary 
          }}>
            Backtest Config
          </label>
          <select style={selectStyle}>
            <option>Config Options</option>
          </select>
        </div>
      </div>

      {/* CENTER COLUMN - Profit Curve & Metrics */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
        {/* Profit Curve */}
        <div style={{ ...cardStyle, flex: 1, minHeight: '400px' }}>
          <h3 style={{ 
            margin: 0, 
            marginBottom: spacing.lg,
            fontSize: typography.fontSize.xl, 
            fontWeight: typography.fontWeight.semibold,
            color: colors.textPrimary 
          }}>
            Profit Curve
          </h3>
          
          {backtestResults ? (
            <div style={{ 
              width: '100%', 
              height: '300px', 
              background: colors.bgPrimary,
              borderRadius: borderRadius.lg,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: colors.textSecondary 
            }}>
              Equity curve chart placeholder
            </div>
          ) : (
            <div style={{ 
              width: '100%', 
              height: '300px', 
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              color: colors.textSecondary 
            }}>
              <div style={{ fontSize: typography.fontSize['3xl'], marginBottom: spacing.md }}>📊</div>
              <div>Run backtest to see profit curve</div>
            </div>
          )}
        </div>

        {/* Performance Metrics */}
        <div style={cardStyle}>
          <h3 style={{ 
            margin: 0, 
            marginBottom: spacing.lg,
            fontSize: typography.fontSize.xl, 
            fontWeight: typography.fontWeight.semibold,
            color: colors.textPrimary 
          }}>
            Performance Metrics
          </h3>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(3, 1fr)', 
            gap: spacing.md 
          }}>
            {/* Total Trades */}
            <div style={{ 
              padding: spacing.lg, 
              background: colors.bgSecondary, 
              borderRadius: borderRadius.lg,
              border: `1px solid ${colors.cardBorder}`
            }}>
              <div style={{ 
                fontSize: typography.fontSize.sm, 
                color: colors.textSecondary,
                marginBottom: spacing.xs 
              }}>
                Total Trades
              </div>
              <div style={{ 
                fontSize: typography.fontSize['3xl'], 
                fontWeight: typography.fontWeight.bold,
                color: colors.textPrimary 
              }}>
                {backtestResults?.statistics?.total_trades || '145'}
              </div>
            </div>

            {/* Win Rate */}
            <div style={{ 
              padding: spacing.lg, 
              background: colors.bgSecondary, 
              borderRadius: borderRadius.lg,
              border: `1px solid ${colors.cardBorder}`
            }}>
              <div style={{ 
                fontSize: typography.fontSize.sm, 
                color: colors.textSecondary,
                marginBottom: spacing.xs 
              }}>
                Win Rate
              </div>
              <div style={{ 
                fontSize: typography.fontSize['3xl'], 
                fontWeight: typography.fontWeight.bold,
                color: colors.textPrimary 
              }}>
                {backtestResults?.statistics?.win_rate?.toFixed(0) || '68'}%
              </div>
            </div>

            {/* Profit/Loss */}
            <div style={{ 
              padding: spacing.lg, 
              background: colors.bgSecondary, 
              borderRadius: borderRadius.lg,
              border: `1px solid ${colors.cardBorder}`
            }}>
              <div style={{ 
                fontSize: typography.fontSize.sm, 
                color: colors.textSecondary,
                marginBottom: spacing.xs 
              }}>
                Profit/Loss
              </div>
              <div style={{ 
                fontSize: typography.fontSize['3xl'], 
                fontWeight: typography.fontWeight.bold,
                color: colors.accentGreen 
              }}>
                +${backtestResults?.statistics?.total_profit?.toFixed(0) || '2,847'}
              </div>
            </div>

            {/* Success Indicator */}
            <div style={{ 
              padding: spacing.lg, 
              background: colors.bgSecondary, 
              borderRadius: borderRadius.lg,
              border: `1px solid ${colors.cardBorder}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: spacing.md
            }}>
              <div style={{ 
                width: '12px', 
                height: '40px', 
                background: colors.accentGreen, 
                borderRadius: borderRadius.full 
              }}></div>
              <div style={{ 
                width: '12px', 
                height: '40px', 
                background: colors.accentRed, 
                borderRadius: borderRadius.full 
              }}></div>
            </div>

            {/* Sharpe Ratio */}
            <div style={{ 
              padding: spacing.lg, 
              background: colors.bgSecondary, 
              borderRadius: borderRadius.lg,
              border: `1px solid ${colors.cardBorder}`
            }}>
              <div style={{ 
                fontSize: typography.fontSize.sm, 
                color: colors.textSecondary,
                marginBottom: spacing.xs 
              }}>
                Sharpe Ratio
              </div>
              <div style={{ 
                fontSize: typography.fontSize['3xl'], 
                fontWeight: typography.fontWeight.bold,
                color: colors.textPrimary 
              }}>
                1.84
              </div>
            </div>

            {/* Max Drawdown */}
            <div style={{ 
              padding: spacing.lg, 
              background: colors.bgSecondary, 
              borderRadius: borderRadius.lg,
              border: `1px solid ${colors.cardBorder}`
            }}>
              <div style={{ 
                fontSize: typography.fontSize.sm, 
                color: colors.textSecondary,
                marginBottom: spacing.xs 
              }}>
                Max Drawdown
              </div>
              <div style={{ 
                fontSize: typography.fontSize['3xl'], 
                fontWeight: typography.fontWeight.bold,
                color: colors.textPrimary 
              }}>
                -12%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT COLUMN - Trade History */}
      <div style={cardStyle}>
        <h3 style={{ 
          margin: 0, 
          marginBottom: spacing.lg,
          fontSize: typography.fontSize.lg, 
          fontWeight: typography.fontWeight.semibold,
          color: colors.textPrimary 
        }}>
          Trade History
        </h3>
        
        <div style={{ 
          fontSize: typography.fontSize.sm, 
          color: colors.textSecondary,
          marginBottom: spacing.md 
        }}>
          Riofx
        </div>

        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          gap: spacing.sm,
          maxHeight: '600px',
          overflowY: 'auto' 
        }}>
          {backtestResults?.trades?.slice(0, 20).map((trade, idx) => (
            <div key={idx} style={{
              display: 'grid',
              gridTemplateColumns: 'auto 1fr auto',
              alignItems: 'center',
              gap: spacing.md,
              padding: spacing.sm,
              background: colors.bgSecondary,
              borderRadius: borderRadius.md,
            }}>
              <div style={{
                fontSize: typography.fontSize.xs,
                color: colors.textSecondary
              }}>
                #{idx + 1}
              </div>
              <div style={{
                fontSize: typography.fontSize.xs,
                color: colors.textSecondary
              }}>
                {trade.signal === 'call' ? 'CALL' : 'PUT'}
              </div>
              <div style={{
                padding: `${spacing.xs} ${spacing.sm}`,
                background: trade.won ? colors.accentGreen : colors.accentRed,
                borderRadius: borderRadius.md,
                fontSize: typography.fontSize.xs,
                fontWeight: typography.fontWeight.semibold,
                color: '#000'
              }}>
                {trade.won ? 'CALL' : 'CALL'}
              </div>
            </div>
          )) || [
            // Mock data when no backtest results
            { id: '#1e293b', side: 'Plge', badge: 'CALL', color: colors.accentGreen },
            { id: '#12293b', side: 'CALL', badge: 'CALL', color: colors.accentRed },
            { id: '#10b981', side: 'PUL', badge: 'CALL', color: colors.accentRed },
            { id: '#10b981', side: 'PUT', badge: 'cf4444', color: colors.accentRed },
            { id: '#$14334', side: 'PUT', badge: 'cf4444', color: colors.accentRed },
          ].map((item, idx) => (
            <div key={idx} style={{
              display: 'grid',
              gridTemplateColumns: 'auto 1fr auto',
              alignItems: 'center',
              gap: spacing.md,
              padding: spacing.sm,
              background: colors.bgSecondary,
              borderRadius: borderRadius.md,
            }}>
              <input type="checkbox" style={{ width: '16px', height: '16px' }} />
              <div style={{
                fontSize: typography.fontSize.xs,
                color: colors.textSecondary
              }}>
                {item.id}
              </div>
              <div style={{
                padding: `${spacing.xs} ${spacing.sm}`,
                background: item.color,
                borderRadius: borderRadius.md,
                fontSize: typography.fontSize.xs,
                fontWeight: typography.fontWeight.semibold,
                color: '#000'
              }}>
                {item.badge}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StrategyBacktest;
