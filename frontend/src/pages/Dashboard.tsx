import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import { Header } from '../components/Header';
import { Toast } from '../components/Toast';
import { SyncStatus, Accounts, CacheStats } from '../types';

interface DashboardProps {
  navigate: (path: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ navigate }) => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [accounts, setAccounts] = useState<Accounts>({ google: [], apple: [] });
  const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'warning' | 'info' } | null>(null);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [status, accts] = await Promise.all([
        api.get<any>('/status'),
        api.get<any>('/accounts')
      ]);
      setSyncStatus(status);
      setAccounts(accts.accounts);
      setCacheStats(status.cache_stats);
      setLoading(false);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      setToast({ message: 'Failed to load dashboard data', type: 'error' });
      setLoading(false);
    }
  };

  const handleForceSync = async () => {
    setSyncing(true);
    try {
      await api.post('/sync');
      setToast({ message: 'Sync started successfully!', type: 'success' });
      setTimeout(loadDashboardData, 2000);
    } catch (error) {
      setToast({ message: 'Sync failed', type: 'error' });
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container">
      <Header navigate={navigate} />

      <div className="status-grid">
        <div className="card">
          <h3>Sync Status</h3>
          <p className={syncStatus?.currently_syncing ? 'status-warning' : 'status-good'}>
            {syncStatus?.currently_syncing ? '🔄 Currently syncing...' : '✅ Ready'}
          </p>
          <p><strong>Last Sync:</strong> {syncStatus?.last_full_sync ? new Date(syncStatus.last_full_sync).toLocaleString() : 'Never'}</p>
          <p><strong>Total Events:</strong> {syncStatus?.total_events || 0}</p>
          <p><strong>Total Calendars:</strong> {syncStatus?.total_calendars || 0}</p>
          <button
            onClick={handleForceSync}
            disabled={syncing}
            className="btn"
          >
            {syncing ? 'Syncing...' : 'Force Sync Now'}
          </button>
        </div>

        <div className="card">
          <h3>Cache Statistics</h3>
          <p><strong>Cached Events:</strong> {cacheStats?.total_events || 0}</p>
          <p><strong>Cached Calendars:</strong> {cacheStats?.total_calendars || 0}</p>
          {cacheStats?.date_range?.earliest && (
            <p>
              <strong>Date Range:</strong><br />
              {cacheStats.date_range.earliest.slice(0, 10)} to {cacheStats.date_range.latest?.slice(0, 10)}
            </p>
          )}
        </div>

        <div className="card">
          <h3>Connected Accounts</h3>
          <p><strong>Google:</strong> {accounts.google?.length || 0}</p>
          <p><strong>Apple:</strong> {accounts.apple?.length || 0}</p>
          {syncStatus?.errors && syncStatus.errors.length > 0 && (
            <p className="status-error"><strong>Recent Errors:</strong> {syncStatus.errors.length}</p>
          )}
          <button onClick={() => navigate('/setup')} className="btn btn-secondary">
            Manage Accounts
          </button>
        </div>
      </div>

      <div className="card">
        <h3>API Information</h3>
        <p>Pi Zero clients should connect to:</p>
        <code>http://{window.location.host}/display</code>
        <h4>Available Endpoints:</h4>
        <ul>
          <li><code>GET /api/events</code> - Get calendar events</li>
          <li><code>GET /api/calendars</code> - Get calendar list</li>
          <li><code>GET /api/status</code> - Get sync status</li>
          <li><code>GET /api/health</code> - Health check</li>
        </ul>
      </div>

      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
    </div>
  );
};