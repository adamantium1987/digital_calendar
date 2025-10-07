// Header.tsx - Using CSS classes
import React from 'react';
import { DarkModeToggle } from './DarkModeToggle';

interface HeaderProps {
  navigate: (path: string) => void;
  title?: string;
  showNavigation?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  navigate,
  title = 'Pi Calendar',
  showNavigation = true
}) => {
  return (
    <div className="header">
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
        <h1>{title}</h1>
        {showNavigation && (
          <nav style={{ display: 'flex', gap: 'var(--space-3)' }}>
            <button onClick={() => navigate('/')} className="btn-link">
              Dashboard
            </button>
            <button onClick={() => navigate('/display')} className="btn-link">
              Calendar
            </button>
            <button onClick={() => navigate('/tasks')} className="btn-link">
              Tasks
            </button>
            <button onClick={() => navigate('/setup')} className="btn-link">
              Setup
            </button>
          </nav>
        )}
      </div>
      <div className="header-controls">
        <DarkModeToggle />
      </div>
    </div>
  );
};
