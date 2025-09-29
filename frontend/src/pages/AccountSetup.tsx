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
    if (!window.confirm(`Remove account ${displayName}?`)) return;

    try {
      await api.deleteAccount(accountId);
      setToast({ message: 'Account removed', type: 'success' });
      loadAccounts();
    } catch (error) {
      setToast({ message: 'Failed to remove account', type: 'error' });
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

      <div className="card">
        <h2>Add New Account</h2>
        <button onClick={() => navigate('/setup/google')} className="btn">
          Add Google Account
        </button>
        <button onClick={() => navigate('/setup/apple')} className="btn">
          Add Apple Account
        </button>
      </div>

      {(accounts.google?.length > 0 || accounts.apple?.length > 0) && (
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
              {!account.authenticated && (
                <a href={`/oauth/google/start/${account.id}`} className="btn btn-warning">
                  Authenticate with Google
                </a>
              )}
              <button
                onClick={() => handleRemoveAccount(account.id, account.display_name)}
                className="btn btn-danger"
              >
                Remove
              </button>
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
              {!account.authenticated && (
                <a href={`/setup/apple/${account.id}/authenticate`} className="btn btn-warning">
                  Enter App-Specific Password
                </a>
              )}
              <button
                onClick={() => handleRemoveAccount(account.id, account.display_name)}
                className="btn btn-danger"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}

      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
    </div>
  );
};