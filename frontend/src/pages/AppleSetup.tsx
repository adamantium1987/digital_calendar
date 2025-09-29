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
      <Header navigate={navigate} />

      <div className="card">
        <h1>🍎 Apple iCloud Setup</h1>

        {error && (
          <div className="error">{error}</div>
        )}

        <div className="instructions">
          <h3>📋 Setup Instructions</h3>
          <p><strong>You'll need an App-Specific Password:</strong></p>
          <ol>
            <li>Go to Apple ID website</li>
            <li>Sign in with your Apple ID</li>
            <li>Go to Security section</li>
            <li>Click Generate Password under App-Specific Passwords</li>
            <li>Enter a label like Pi Calendar</li>
            <li>Save the generated password for authentication</li>
          </ol>
          <p><strong>Note:</strong> Two-factor authentication must be enabled.</p>
        </div>

        <form onSubmit={handleSubmit} className="form">
          <div className="form-group">
            <label htmlFor="display_name">Display Name:</label>
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
            <label htmlFor="username">iCloud Email:</label>
            <input
              type="email"
              id="username"
              required
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
              placeholder="your@icloud.com"
            />
          </div>

          <button type="submit" disabled={submitting} className="btn">
            {submitting ? 'Adding Account...' : 'Add Apple Account'}
          </button>
        </form>

        <p><small>The App-Specific Password will be requested during authentication.</small></p>
        <p>
          <button onClick={() => navigate('/setup')} className="btn-link">
            ← Back to Account Setup
          </button>
        </p>
      </div>
    </div>
  );
};