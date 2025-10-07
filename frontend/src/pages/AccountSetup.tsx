// AccountSetup.tsx - Using CSS classes
import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import { Header } from '../components/global/Header';
import { Toast } from '../components/global/Toast';
import {Accounts} from "../types/accounts";
import { useNavigate } from 'react-router-dom';


export const AccountSetup: React.FC = () => {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState<Accounts>({ google: [], apple: [] });
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const accts = await api.get<any>('/accounts');
      setAccounts(accts.accounts);
      setLoading(false);
    } catch (error) {
      console.error('Error loading accounts:', error);
      setLoading(false);
    }
  };

  const handleRemoveAccount = async (accountId: string, displayName: string) => {
    if (!window.confirm(`Remove account "${displayName}"?`)) return;

    try {
      await api.deleteAccount(accountId);
      setToast({ message: 'Account removed successfully', type: 'success' });
      loadAccounts();
    } catch (error) {
      setToast({ message: 'Failed to remove account', type: 'error' });
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading">Loading accounts...</div>
      </div>
    );
  }

  const hasAccounts = accounts.google?.length > 0 || accounts.apple?.length > 0;

  return (
    <div className="container">
      <Header navigate={navigate} title="Account Setup" />

      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: 'linear-gradient(135deg, var(--primary-500), var(--primary-600))',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '1.5rem'
          }}>
            +
          </div>
          <div>
            <h2 style={{ margin: 0, marginBottom: 'var(--space-1)' }}>Add New Account</h2>
            <p style={{ margin: 0, fontSize: '0.875rem' }}>Connect your calendar accounts to sync events across all your devices.</p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          <button
            onClick={() => navigate('/setup/google')}
            className="btn"
            style={{
              flex: 1,
              minWidth: '200px',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)'
            }}
          >
            <span style={{
              width: '20px',
              height: '20px',
              background: 'linear-gradient(135deg, #4285f4, #34a853)',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.75rem',
              fontWeight: '700'
            }}>
              G
            </span>
            Add Google Account
          </button>
          <button
            onClick={() => navigate('/setup/apple')}
            className="btn btn-secondary"
            style={{
              flex: 1,
              minWidth: '200px',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)'
            }}
          >
            <span style={{ fontSize: '0.875rem' }}>🍎</span>
            Add Apple Account
          </button>
        </div>
      </div>

      {hasAccounts ? (
        <div className="card">
          <h2>Configured Accounts</h2>

          {accounts.google?.map(account => (
            <div key={account.id} className="account-item">
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  background: 'linear-gradient(135deg, #4285f4, #34a853)',
                  borderRadius: 'var(--radius-lg)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: '1.25rem',
                  fontWeight: '700'
                }}>
                  G
                </div>
                <div style={{ flex: 1 }}>
                  <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                    Google: {account.display_name}
                    {account.authenticated ? (
                      <span className="status status-authenticated">Authenticated</span>
                    ) : (
                      <span className="status status-pending">Needs Authentication</span>
                    )}
                  </h3>
                  <p style={{ margin: 'var(--space-1) 0 0 0', fontSize: '0.875rem' }}>
                    <strong>Account ID:</strong> {account.id}
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                {!account.authenticated && (
                  <a href={`/oauth/google/start/${account.id}`} className="btn btn-warning">
                    Authenticate with Google
                  </a>
                )}
                <button
                  onClick={() => handleRemoveAccount(account.id, account.display_name)}
                  className="btn btn-danger"
                >
                  Remove Account
                </button>
              </div>
            </div>
          ))}

          {accounts.apple?.map(account => (
            <div key={account.id} className="account-item">
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  background: 'linear-gradient(135deg, #000000, #333333)',
                  borderRadius: 'var(--radius-lg)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontSize: '1rem'
                }}>
                  🍎
                </div>
                <div style={{ flex: 1 }}>
                  <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                    Apple: {account.display_name}
                    {account.authenticated ? (
                      <span className="status status-authenticated">Authenticated</span>
                    ) : (
                      <span className="status status-pending">Needs Authentication</span>
                    )}
                  </h3>
                  <p style={{ margin: 'var(--space-1) 0 0 0', fontSize: '0.875rem' }}>
                    <strong>Username:</strong> {account.username}
                  </p>
                  <p style={{ margin: 'var(--space-1) 0 0 0', fontSize: '0.875rem' }}>
                    <strong>Account ID:</strong> {account.id}
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                {!account.authenticated && (
                    <button
                        onClick={() => navigate(`/setup/apple?id=${account.id}&step=authenticate`)}
                        className="btn btn-warning"
                    >
                      Enter App-Specific Password
                    </button>
                )}
                <button
                    onClick={() => handleRemoveAccount(account.id, account.display_name)}
                    className="btn btn-danger"
                >
                  Remove Account
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card">
          <div className="no-events">
            No accounts configured yet. Add your first account above to get started.
          </div>
        </div>
      )}

      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
    </div>
  );
};
