// Dashboard.tsx - Using CSS classes
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

  const loadChores = useCallback(async () => {
    try {
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

  const handleChoreSync = async () => {
    setChoreSyncing(true);
    try {
      const res = (await api.post('/chores/sync')) as { message?: string };
      setToast({ message: res.message || 'Chores sync started', type: 'success' });
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
        <div className="loading">Loading dashboard...</div>
      </div>
    );
  }

  const totalAccounts = (accounts.google?.length || 0) + (accounts.apple?.length || 0);

  return (
    <div className="container">
      <Header navigate={navigate} title="Dashboard" />

      <div className="status-grid">
        <div className="card">
          <h3>🔄 Sync Status</h3>
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
              marginBottom: 'var(--space-2)'
            }}>
              <div style={{
                width: '12px',
                height: '12px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: syncStatus?.currently_syncing ? 'var(--warning-500)' : 'var(--success-500)'
              }}></div>
              <span className={syncStatus?.currently_syncing ? 'status-warning' : 'status-good'}>
                {syncStatus?.currently_syncing ? 'Currently syncing...' : 'Ready'}
              </span>
            </div>
          </div>

          <div style={{ marginBottom: 'var(--space-3)' }}>
            <p style={{ margin: 0, fontSize: '0.875rem' }}>
              <strong>Last Sync:</strong>{' '}
              {syncStatus?.last_full_sync
                ? new Date(syncStatus.last_full_sync).toLocaleString()
                : 'Never'}
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 'var(--space-3)',
            marginBottom: 'var(--space-4)'
          }}>
            <div style={{
              background: 'var(--bg-primary)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-lg)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--primary-500)' }}>
                {syncStatus?.total_events || 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Events</div>
            </div>
            <div style={{
              background: 'var(--bg-primary)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-lg)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--primary-500)' }}>
                {syncStatus?.total_calendars || 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Calendars</div>
            </div>
          </div>

          <button
            onClick={handleForceSync}
            disabled={syncing || syncStatus?.currently_syncing}
            className="btn"
            style={{ width: '100%' }}
          >
            {syncing ? 'Syncing...' : 'Force Sync Now'}
          </button>
        </div>

        <div className="card">
          <h3>📊 Cache Statistics</h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 'var(--space-3)',
            marginBottom: 'var(--space-4)'
          }}>
            <div style={{
              background: 'var(--bg-primary)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-lg)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--success-500)' }}>
                {cacheStats?.total_events || 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Cached Events</div>
            </div>
            <div style={{
              background: 'var(--bg-primary)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-lg)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--success-500)' }}>
                {cacheStats?.total_calendars || 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Cached Calendars</div>
            </div>
          </div>

          {cacheStats?.date_range?.earliest && cacheStats?.date_range?.latest && (
            <div style={{
              background: 'var(--bg-primary)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-lg)',
              fontSize: '0.875rem'
            }}>
              <strong>Date Range:</strong><br />
              {new Date(cacheStats.date_range.earliest).toLocaleDateString()} to{' '}
              {new Date(cacheStats.date_range.latest).toLocaleDateString()}
            </div>
          )}
        </div>

        <div className="card">
          <h3>🔗 Connected Accounts</h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 'var(--space-3)',
            marginBottom: 'var(--space-4)'
          }}>
            <div style={{
              background: 'var(--bg-primary)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-lg)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--primary-500)' }}>
                {accounts.google?.length || 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Google</div>
            </div>
            <div style={{
              background: 'var(--bg-primary)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-lg)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--primary-500)' }}>
                {accounts.apple?.length || 0}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Apple</div>
            </div>
            <div style={{
              background: 'var(--bg-primary)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-lg)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--success-500)' }}>
                {totalAccounts}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Total</div>
            </div>
          </div>

          {syncStatus?.errors && syncStatus.errors.length > 0 && (
            <div style={{
              background: 'var(--error-50)',
              color: 'var(--error-600)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-lg)',
              marginBottom: 'var(--space-4)',
              fontSize: '0.875rem'
            }}>
              <strong>Recent Errors:</strong> {syncStatus.errors.length}
            </div>
          )}

          <button onClick={() => navigate('/setup')} className="btn btn-secondary" style={{ width: '100%' }}>
            Manage Accounts
          </button>
        </div>

        <div className="card">
          <h3>📝 Chore Chart</h3>
          <div style={{
            background: 'var(--bg-primary)',
            padding: 'var(--space-4)',
            borderRadius: 'var(--radius-lg)',
            textAlign: 'center',
            marginBottom: 'var(--space-4)'
          }}>
            <div style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--primary-500)' }}>
              {chores?.length || 0}
            </div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Total Chores</div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
              <button
                onClick={handleChoreSync}
                className="btn"
                disabled={choreSyncing}
                style={{ flex: 1 }}
              >
                {choreSyncing ? 'Syncing...' : 'Sync'}
              </button>

              <button
                onClick={handleChoreLoad}
                className="btn btn-secondary"
                disabled={choreLoading}
                style={{ flex: 1 }}
              >
                {choreLoading ? 'Loading...' : 'Load'}
              </button>
            </div>

            <button
              onClick={() => {
                try {
                  sessionStorage.setItem('opened_chore_page_at', Date.now().toString());
                } catch (e) {
                  /* ignore storage errors silently */
                }
                navigate('/chores');
              }}
              className="btn btn-secondary"
              style={{ width: '100%' }}
            >
              Open Chore Chart
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>🔗 API Information</h3>
        <p style={{ marginBottom: 'var(--space-4)' }}>Pi Zero clients should connect to:</p>
        <div style={{
          background: 'var(--bg-primary)',
          padding: 'var(--space-3)',
          borderRadius: 'var(--radius-lg)',
          marginBottom: 'var(--space-4)',
          fontFamily: 'monospace',
          fontSize: '0.875rem'
        }}>
          http://{window.location.host}/display
        </div>

        <h4 style={{ marginBottom: 'var(--space-3)' }}>Available Endpoints:</h4>
        <div style={{
          display: 'grid',
          gap: 'var(--space-2)',
          fontSize: '0.875rem'
        }}>
          <div style={{
            background: 'var(--bg-primary)',
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <code style={{ fontWeight: '600' }}>GET /api/events</code>
            <span style={{ color: 'var(--text-secondary)' }}>Get calendar events</span>
          </div>
          <div style={{
            background: 'var(--bg-primary)',
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <code style={{ fontWeight: '600' }}>GET /api/calendars</code>
            <span style={{ color: 'var(--text-secondary)' }}>Get calendar list</span>
          </div>
          <div style={{
            background: 'var(--bg-primary)',
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <code style={{ fontWeight: '600' }}>GET /api/status</code>
            <span style={{ color: 'var(--text-secondary)' }}>Get sync status</span>
          </div>
          <div style={{
            background: 'var(--bg-primary)',
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <code style={{ fontWeight: '600' }}>GET /api/health</code>
            <span style={{ color: 'var(--text-secondary)' }}>Health check</span>
          </div>
        </div>
      </div>

      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
    </div>
  );
};
