import React, { useState, useEffect } from 'react';
import { Dashboard } from './pages/Dashboard';
import { AccountSetup } from './pages/AccountSetup';
import { GoogleSetup } from './pages/GoogleSetup';
import { AppleSetup } from './pages/AppleSetup';
import { CalendarDisplay } from './pages/CalendarDisplay';
import { TaskChartDisplay } from './pages/TaskChartDisplay';

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

    // Prevent rendering React for API paths
  if (currentPath.startsWith('/api/')) {
    return <div>Loading API data...</div>;
  }

  if (currentPath === '/setup') return <AccountSetup navigate={navigate} />;
  if (currentPath.startsWith('/setup/google')) return <GoogleSetup navigate={navigate} />;

  if (currentPath.startsWith('/setup/apple')) {
    const urlParams = new URLSearchParams(window.location.search);
    const accountId = urlParams.get('id');
    const step = urlParams.get('step');
    return <AppleSetup navigate={navigate} accountId={accountId} step={step} />;
  }
  if (currentPath === '/tasks')return <TaskChartDisplay  navigate={navigate}/>;
  if (currentPath === '/display') return <CalendarDisplay  navigate={navigate}/>;
  return <Dashboard navigate={navigate} />;
};

export default App;