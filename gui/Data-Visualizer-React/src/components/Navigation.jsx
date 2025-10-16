import React from 'react';
import { Link } from 'react-router-dom';

const NavigationItem = ({ to, icon, label }) => (
  <li>
    <Link
      to={to}
      className="flex items-center gap-2 transition-colors font-medium"
      style={{ color: 'var(--text-primary)' }}
      onMouseEnter={(e) => e.target.style.color = 'var(--accent-blue)'}
      onMouseLeave={(e) => e.target.style.color = 'var(--text-primary)'}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </Link>
  </li>
);

const Navigation = ({ items }) => (
  <nav
    className="glass text-slate-100 px-6 py-4 shadow-lg"
    style={{ borderColor: 'var(--card-border)' }}
  >
    <div className="w-full">
      <ul className="flex gap-8">
        {items.map((item, index) => (
          <NavigationItem key={index} {...item} />
        ))}
      </ul>
    </div>
  </nav>
);

export default Navigation;