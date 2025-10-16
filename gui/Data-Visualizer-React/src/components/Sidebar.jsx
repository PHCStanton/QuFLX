import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { designTokens } from '../styles/designTokens';
import { useSidebar } from '../contexts/SidebarContext';

const ChartIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="20" x2="12" y2="10"></line>
    <line x1="18" y1="20" x2="18" y2="4"></line>
    <line x1="6" y1="20" x2="6" y2="16"></line>
  </svg>
);

const FlaskIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2v6a2 2 0 0 0 .245.96l5.51 10.08A2 2 0 0 1 18 22H6a2 2 0 0 1-1.755-2.96l5.51-10.08A2 2 0 0 0 10 8V2"></path>
    <path d="M6.453 15h11.094"></path>
  </svg>
);

const TradingIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
  </svg>
);

const ChevronLeftIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="15 18 9 12 15 6"></polyline>
  </svg>
);

const ChevronRightIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6"></polyline>
  </svg>
);

const menuItems = [
  { path: '/', icon: ChartIcon, label: 'Data Analysis' },
  { path: '/backtest', icon: FlaskIcon, label: 'Strategy Lab' },
  { path: '/live', icon: TradingIcon, label: 'Trading Hub' },
];

const Sidebar = () => {
  const { isExpanded, toggleSidebar } = useSidebar();
  const location = useLocation();

  const sidebarStyle = {
    position: 'fixed',
    left: 0,
    top: 0,
    height: '100vh',
    width: isExpanded ? '240px' : '64px',
    backgroundColor: designTokens.colors.card,
    borderRight: `1px solid ${designTokens.colors.border}`,
    transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    zIndex: 1000,
    display: 'flex',
    flexDirection: 'column',
  };

  const headerStyle = {
    padding: isExpanded ? '20px' : '20px 16px',
    borderBottom: `1px solid ${designTokens.colors.border}`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    minHeight: '72px',
  };

  const brandStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    overflow: 'hidden',
  };

  const logoStyle = {
    width: '32px',
    height: '32px',
    background: `linear-gradient(135deg, ${designTokens.colors.accent} 0%, ${designTokens.colors.accentHover} 100%)`,
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  };

  const logoTextStyle = {
    fontSize: '20px',
    fontWeight: '700',
    color: designTokens.colors.text.primary,
  };

  const brandTextStyle = {
    fontSize: '18px',
    fontWeight: '600',
    color: designTokens.colors.text.primary,
    whiteSpace: 'nowrap',
    opacity: isExpanded ? 1 : 0,
    transition: 'opacity 0.2s',
  };

  const toggleButtonStyle = {
    width: '32px',
    height: '32px',
    borderRadius: '6px',
    backgroundColor: 'transparent',
    border: `1px solid ${designTokens.colors.border}`,
    color: designTokens.colors.text.secondary,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s',
    flexShrink: 0,
  };

  const navStyle = {
    flex: 1,
    padding: '16px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    overflowY: 'auto',
    overflowX: 'hidden',
  };

  const getMenuItemStyle = (isActive) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: isExpanded ? '12px 16px' : '12px',
    borderRadius: '8px',
    textDecoration: 'none',
    color: isActive ? designTokens.colors.text.primary : designTokens.colors.text.secondary,
    backgroundColor: isActive ? `${designTokens.colors.accent}15` : 'transparent',
    border: isActive ? `1px solid ${designTokens.colors.accent}40` : '1px solid transparent',
    transition: 'all 0.2s',
    cursor: 'pointer',
    position: 'relative',
    justifyContent: isExpanded ? 'flex-start' : 'center',
  });

  const iconStyle = {
    width: '20px',
    height: '20px',
    flexShrink: 0,
  };

  const labelStyle = {
    fontSize: '14px',
    fontWeight: '500',
    whiteSpace: 'nowrap',
    opacity: isExpanded ? 1 : 0,
    transition: 'opacity 0.2s',
  };

  const activeIndicatorStyle = {
    position: 'absolute',
    left: 0,
    top: '50%',
    transform: 'translateY(-50%)',
    width: '3px',
    height: '20px',
    backgroundColor: designTokens.colors.accent,
    borderRadius: '0 2px 2px 0',
  };

  return (
    <div style={sidebarStyle}>
      <div style={headerStyle}>
        <div style={brandStyle}>
          <div style={logoStyle}>
            <span style={logoTextStyle}>Q</span>
          </div>
          <span style={brandTextStyle}>QuantumFlux</span>
        </div>
        <button
          style={toggleButtonStyle}
          onClick={toggleSidebar}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = designTokens.colors.border;
            e.currentTarget.style.color = designTokens.colors.text.primary;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
            e.currentTarget.style.color = designTokens.colors.text.secondary;
          }}
        >
          {isExpanded ? <ChevronLeftIcon className="w-4 h-4" /> : <ChevronRightIcon className="w-4 h-4" />}
        </button>
      </div>

      <nav style={navStyle}>
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              style={getMenuItemStyle(isActive)}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = `${designTokens.colors.border}80`;
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }
              }}
            >
              {isActive && <div style={activeIndicatorStyle} />}
              <Icon className="icon" style={iconStyle} />
              {isExpanded && <span style={labelStyle}>{item.label}</span>}
            </Link>
          );
        })}
      </nav>
    </div>
  );
};

export default Sidebar;
