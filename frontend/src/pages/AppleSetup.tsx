// AppleSetup.tsx - Using CSS classes
import React, { useState } from 'react';
import { api } from '../utils/api';
import { Header } from '../components/Header';

interface AppleSetupProps {
  navigate: (path: string) => void;
}

export const AppleSetup: React.FC<AppleSetupProps> = ({ navigate }) => {
  const [formData, setFormData] = useState({
    display_name: '',
    username: ''
  });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      const response = await api.submitForm('/setup/apple', formData);

      if (response.redirected) {
        window.location.href = response.url;
      } else {
        const text = await response.text();
        if (text.includes('error')) {
          setError('Setup failed. Please check your credentials.');
        }
      }
    } catch (err) {
      setError('Setup failed: ' + (err as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container">
      <Header navigate={navigate} title="Apple iCloud Setup" />

      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: 'linear-gradient(135deg, #000000, #333333)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '1.25rem'
          }}>
            🍎
          </div>
          <div>
            <h2 style={{ margin: 0, marginBottom: 'var(--space-1)' }}>Apple iCloud Setup</h2>
            <p style={{ margin: 0, fontSize: '0.875rem' }}>Connect your Apple iCloud account</p>
          </div>
        </div>

        {error && (
          <div className="error">{error}</div>
        )}

        <div className="instructions">
          <h3>Setup Instructions</h3>
          <p><strong>You'll need an App-Specific Password:</strong></p>
          <ol>
            <li>Go to <a href="https://appleid.apple.com" target="_blank" rel="noopener noreferrer">Apple ID website</a></li>
            <li>Sign in with your Apple ID</li>
            <li>Go to Security section</li>
            <li>Click Generate Password under App-Specific Passwords</li>
            <li>Enter a label like "Pi Calendar"</li>
            <li>Save the generated password for authentication</li>
          </ol>
          <div style={{
            background: 'var(--warning-50)',
            border: '1px solid var(--warning-200)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--space-3)',
            marginTop: 'var(--space-3)'
          }}>
            <strong style={{ color: 'var(--warning-600)' }}>Note:</strong> Two-factor authentication must be enabled.
          </div>
        </div>

        <form onSubmit={handleSubmit} className="form">
          <div className="form-group">
            <label htmlFor="display_name">Display Name</label>
            <input
              type="text"
              id="display_name"
              required
              value={formData.display_name}
              onChange={(e) => setFormData({...formData, display_name: e.target.value})}
              placeholder="e.g., Personal iCloud"
            />
          </div>

          <div className="form-group">
            <label htmlFor="username">iCloud Email</label>
            <input
              type="email"
              id="username"
              required
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
              placeholder="your@icloud.com"
            />
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
            <button type="submit" disabled={submitting} className="btn" style={{ flex: 1 }}>
              {submitting ? 'Adding Account...' : 'Add Apple Account'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/setup')}
              className="btn btn-secondary"
            >
              Back to Setup
            </button>
          </div>
        </form>

        <div style={{
          background: 'var(--bg-primary)',
          padding: 'var(--space-3)',
          borderRadius: 'var(--radius-lg)',
          marginTop: 'var(--space-4)',
          fontSize: '0.875rem',
          color: 'var(--text-secondary)'
        }}>
          The App-Specific Password will be requested during authentication.
        </div>
      </div>
    </div>
  );
};
