import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import { Header } from '../components/Header';
import { Toast } from '../components/Toast';
import { Accounts } from '../types';

interface AccountSetupProps {
  navigate: (path: string) => void;
}

export const AccountSetup: React.FC<AccountSetupProps> = ({ navigate }) => {
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
        <div className="loading">Loading accounts</div>
      </div>
    );
  }

  const hasAccounts = accounts.google?.length > 0 || accounts.apple?.length > 0;

  return (
    <div className="container">
      <Header navigate={navigate} />

      <div className="card">
        <h2>Add New Account</h2>
        <p style={{ marginBottom: '1.5rem', color: 'var(--neutral-600)' }}>
          Connect your calendar accounts to sync events across all your devices.
        </p>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button onClick={() => navigate('/setup/google')} className="btn">
            Add Google Account
          </button>
          <button onClick={() => navigate('/setup/apple')} className="btn btn-secondary">
            Add Apple Account
          </button>
        </div>
      </div>

      {hasAccounts ? (
        <div className="card">
          <h2>Configured Accounts</h2>

          {accounts.google?.map(account => (
            <div key={account.id} className="account-item">
              <h3>
                Google: {account.display_name}
                {account.authenticated ? (
                  <span className="status status-authenticated">Authenticated</span>
                ) : (
                  <span className="status status-pending">Needs Authentication</span>
                )}
              </h3>
              <p><strong>Account ID:</strong> {account.id}</p>
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', flexWrap: 'wrap' }}>
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
              <h3>
                Apple: {account.display_name}
                {account.authenticated ? (
                  <span className="status status-authenticated">Authenticated</span>
                ) : (
                  <span className="status status-pending">Needs Authentication</span>
                )}
              </h3>
              <p><strong>Username:</strong> {account.username}</p>
              <p><strong>Account ID:</strong> {account.id}</p>
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', flexWrap: 'wrap' }}>
                {!account.authenticated && (
                  <a href={`/setup/apple/${account.id}/authenticate`} className="btn btn-warning">
                    Enter App-Specific Password
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