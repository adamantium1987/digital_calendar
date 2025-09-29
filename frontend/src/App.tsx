import React, { useState, useEffect } from 'react';
import { Dashboard } from './pages/Dashboard';
import { AccountSetup } from './pages/AccountSetup';
import { GoogleSetup } from './pages/GoogleSetup';
import { AppleSetup } from './pages/AppleSetup';
import { CalendarDisplay } from './pages/CalendarDisplay';

const App: React.FC = () => {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);

  useEffect(() => {
    const handlePopState = () => setCurrentPath(window.location.pathname);
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = (path: string) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
  };

  if (currentPath === '/setup') return <AccountSetup navigate={navigate} />;
  if (currentPath.startsWith('/setup/google')) return <GoogleSetup navigate={navigate} />;
  if (currentPath.startsWith('/setup/apple')) return <AppleSetup navigate={navigate} />;
  if (currentPath === '/display') return <CalendarDisplay />;
  return <Dashboard navigate={navigate} />;
};

export default App;