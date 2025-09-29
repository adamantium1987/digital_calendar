import React, { useState } from 'react';
import { api } from '../utils/api';
import { Header } from '../components/Header';

interface GoogleSetupProps {
  navigate: (path: string) => void;
}

export const GoogleSetup: React.FC<GoogleSetupProps> = ({ navigate }) => {
  const [formData, setFormData] = useState({
    display_name: '',
    client_id: '',
    client_secret: ''
  });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      const response = await api.submitForm('/setup/google', formData);

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
        <h1>🔧 Google Calendar Setup</h1>

        {error && (
          <div className="error">{error}</div>
        )}

        <div className="instructions">
          <h3>📋 Setup Instructions</h3>
          <ol>
            <li>Go to Google Cloud Console</li>
            <li>Create a new project or select existing project</li>
            <li>Enable the Google Calendar API</li>
            <li>Create OAuth 2.0 Client ID credentials</li>
            <li>Add redirect URI: <code>http://localhost:5000/callback</code></li>
            <li>Copy the Client ID and Client Secret below</li>
          </ol>
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
              placeholder="e.g., Personal Gmail"
            />
          </div>

          <div className="form-group">
            <label htmlFor="client_id">Google Client ID:</label>
            <input
              type="text"
              id="client_id"
              required
              value={formData.client_id}
              onChange={(e) => setFormData({...formData, client_id: e.target.value})}
              placeholder="123456789-abcdefg.apps.googleusercontent.com"
            />
          </div>

          <div className="form-group">
            <label htmlFor="client_secret">Google Client Secret:</label>
            <input
              type="password"
              id="client_secret"
              required
              value={formData.client_secret}
              onChange={(e) => setFormData({...formData, client_secret: e.target.value})}
              placeholder="GOCSPX-..."
            />
          </div>

          <button type="submit" disabled={submitting} className="btn">
            {submitting ? 'Adding Account...' : 'Add Google Account'}
          </button>
        </form>

        <p>
          <button onClick={() => navigate('/setup')} className="btn-link">
            ← Back to Account Setup
          </button>
        </p>
      </div>
    </div>
  );
};