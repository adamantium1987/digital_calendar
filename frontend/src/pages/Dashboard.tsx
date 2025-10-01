import React, { useState, useEffect, useCallback } from 'react';
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

  // Chore-specific state
  const [chores, setChores] = useState<any[]>([]);
  const [choreSyncing, setChoreSyncing] = useState(false);
  const [choreLoading, setChoreLoading] = useState(false);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getIsoWeekStart = (d: Date) => {
    const copy = new Date(d);
    const day = copy.getDay(); // Sunday = 0
    copy.setDate(copy.getDate() - day);
    return copy.toISOString().slice(0, 10);
  };

  const loadChores = useCallback(async () => {
    try {
      const week = getIsoWeekStart(new Date());
      const res = await api.get<any>(`/chores`);
      const list = res?.chores ?? [];
      setChores(list);
    } catch (err) {
      console.error('Failed loading chores', err);
      setChores([]);
    }
  }, []);

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const [status, accts] = await Promise.all([
        api.get<any>('/status'),
        api.get<any>('/accounts')
      ]);
      setSyncStatus(status);
      setAccounts(accts.accounts);
      setCacheStats(status.cache_stats);
      await loadChores();
      setLoading(false);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      setToast({ message: 'Failed to load dashboard data', type: 'error' });
      setLoading(false);
    }
  }, [loadChores]);

  const handleForceSync = async () => {
    setSyncing(true);
    try {
      const res = (await api.post('/sync')) as { message?: string };
      setToast({ message: res.message || 'Sync started', type: 'success' });

      setTimeout(loadDashboardData, 2000);
    } catch (error) {
      setToast({ message: 'Sync failed', type: 'error' });
    } finally {
      setSyncing(false);
    }
  };

  // Chore actions
  const handleChoreSync = async () => {
    setChoreSyncing(true);
    try {
     const res = (await api.post('/chores/sync')) as { message?: string };
    setToast({ message: res.message || 'Chores sync started', type: 'success' });
      // refresh chores after a short delay
      setTimeout(loadChores, 1500);
    } catch (err) {
      console.error('Chore sync failed', err);
      setToast({ message: 'Chore sync failed', type: 'error' });
    } finally {
      setChoreSyncing(false);
    }
  };

  const handleChoreLoad = async () => {
    setChoreLoading(true);
    try {
      const res = (await api.post('/chores/load')) as { message?: string };
      setToast({ message: res.message || 'Chores loaded', type: 'success' });

      await loadChores();
    } catch (err) {
      console.error('Chore load failed', err);
      setToast({ message: 'Chore load failed', type: 'error' });
    } finally {
      setChoreLoading(false);
    }
  };

  // Auto-refresh chores when user returns from /chores:
  useEffect(() => {
    const refreshIfReturned = async () => {
      const ts = sessionStorage.getItem('opened_chore_page_at');
      if (!ts) return;
      // If flag exists, user previously navigated to /chores — refresh and clear flag
      try {
        await loadChores();
      } catch (e) {
        /* ignore */
      } finally {
        sessionStorage.removeItem('opened_chore_page_at');
      }
    };

    const onFocus = () => {
      void refreshIfReturned();
    };
    const onVisibility = () => {
      if (document.visibilityState === 'visible') {
        void refreshIfReturned();
      }
    };

    window.addEventListener('focus', onFocus);
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      window.removeEventListener('focus', onFocus);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [loadChores]);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading">Loading dashboard</div>
      </div>
    );
  }

  const totalAccounts = (accounts.google?.length || 0) + (accounts.apple?.length || 0);

  return (
    <div className="container">
      <Header navigate={navigate} />

      <div className="status-grid">
        <div className="card">
          <h3>Sync Status</h3>
          <p className={syncStatus?.currently_syncing ? 'status-warning' : 'status-good'}>
            {syncStatus?.currently_syncing ? 'Currently syncing...' : 'Ready'}
          </p>
          <p>
            <strong>Last Sync:</strong>{' '}
            {syncStatus?.last_full_sync
              ? new Date(syncStatus.last_full_sync).toLocaleString()
              : 'Never'}
          </p>
          <p><strong>Total Events:</strong> {syncStatus?.total_events || 0}</p>
          <p><strong>Total Calendars:</strong> {syncStatus?.total_calendars || 0}</p>
          <button
            onClick={handleForceSync}
            disabled={syncing || syncStatus?.currently_syncing}
            className="btn"
          >
            {syncing ? 'Syncing...' : 'Force Sync Now'}
          </button>
        </div>

        <div className="card">
          <h3>Cache Statistics</h3>
          <p><strong>Cached Events:</strong> {cacheStats?.total_events || 0}</p>
          <p><strong>Cached Calendars:</strong> {cacheStats?.total_calendars || 0}</p>
          {cacheStats?.date_range?.earliest && cacheStats?.date_range?.latest && (
            <p>
              <strong>Date Range:</strong><br />
              {new Date(cacheStats.date_range.earliest).toLocaleDateString()} to{' '}
              {new Date(cacheStats.date_range.latest).toLocaleDateString()}
            </p>
          )}
        </div>

        <div className="card">
          <h3>Connected Accounts</h3>
          <p><strong>Google:</strong> {accounts.google?.length || 0}</p>
          <p><strong>Apple:</strong> {accounts.apple?.length || 0}</p>
          <p><strong>Total:</strong> {totalAccounts}</p>
          {syncStatus?.errors && syncStatus.errors.length > 0 && (
            <p className="status-error">
              <strong>Recent Errors:</strong> {syncStatus.errors.length}
            </p>
          )}
          <button onClick={() => navigate('/setup')} className="btn btn-secondary">
            Manage Accounts
          </button>
        </div>

        {/* Chore Chart card matching the Connected Accounts style */}
        <div className="card">
          <h3>Chore Chart</h3>
          <p><strong>Total Chores:</strong> {chores?.length || 0}</p>
          {syncStatus?.errors && syncStatus.errors.length > 0 && (
            <p className="status-error">
              <strong>Recent Errors:</strong> {syncStatus.errors.length}
            </p>
          )}
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <button
              onClick={handleChoreSync}
              className="btn"
              disabled={choreSyncing}
            >
              {choreSyncing ? 'Syncing...' : 'Sync'}
            </button>

            <button
              onClick={handleChoreLoad}
              className="btn btn-secondary"
              disabled={choreLoading}
            >
              {choreLoading ? 'Loading...' : 'Load'}
            </button>

            <button
              onClick={() => {
                // set a flag so we know user opened the chores page — refresh when they return
                try {
                  sessionStorage.setItem('opened_chore_page_at', Date.now().toString());
                } catch (e) {
                  /* ignore storage errors silently */
                }
                navigate('/api/chores');
              }}
              className="btn btn-secondary"
            >
              Open Chore Chart
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>API Information</h3>
        <p>Pi Zero clients should connect to:</p>
        <code>http://{window.location.host}/display</code>

        <h3>Available Endpoints:</h3>
        <ul style={{lineHeight: '2'}}>
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
