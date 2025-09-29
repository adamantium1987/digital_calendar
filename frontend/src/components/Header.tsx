import React from 'react';

interface HeaderProps {
  navigate: (path: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ navigate }) => {
  return (
    <div className="header">
      <h1>🗓️ Furrer Calendar Server</h1>
      <nav>
        <button onClick={() => navigate('/')} className="nav-link">Dashboard</button>
        <button onClick={() => navigate('/setup')} className="nav-link">Account Setup</button>
        <button onClick={() => navigate('/display')} className="nav-link">Calendar</button>
      </nav>
    </div>
  );
};