// GoogleSetup.tsx - Using CSS classes
import React, { useState } from 'react';
import { api } from '../utils/api';
import { Header } from '../components/global/Header';
import {useNavigate} from "react-router-dom";


export const GoogleSetup: React.FC = () => {
  const navigate = useNavigate();
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
      <Header navigate={navigate} title="Google Calendar Setup" />

      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: 'linear-gradient(135deg, #4285f4, #34a853)',
            borderRadius: 'var(--radius-lg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '1.5rem',
            fontWeight: '700'
          }}>
            G
          </div>
          <div>
            <h2 style={{ margin: 0, marginBottom: 'var(--space-1)' }}>Google Calendar Setup</h2>
            <p style={{ margin: 0, fontSize: '0.875rem' }}>Connect your Google Calendar account</p>
          </div>
        </div>

        {error && (
          <div className="error">{error}</div>
        )}

        <div className="instructions">
          <h3>Setup Instructions</h3>
          <ol>
            <li>Go to <a href="https://console.cloud.google.com" target="_blank" rel="noopener noreferrer">Google Cloud Console</a></li>
            <li>Create a new project or select an existing project</li>
            <li>Enable the Google Calendar API</li>
            <li>Create OAuth 2.0 Client ID credentials</li>
            <li>Add redirect URI: <code>http://localhost:5000/callback</code></li>
            <li>Copy the Client ID and Client Secret below</li>
          </ol>
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
              placeholder="e.g., Personal Gmail"
            />
          </div>

          <div className="form-group">
            <label htmlFor="client_id">Google Client ID</label>
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
            <label htmlFor="client_secret">Google Client Secret</label>
            <input
              type="password"
              id="client_secret"
              required
              value={formData.client_secret}
              onChange={(e) => setFormData({...formData, client_secret: e.target.value})}
              placeholder="GOCSPX-..."
            />
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
            <button type="submit" disabled={submitting} className="btn" style={{ flex: 1 }}>
              {submitting ? 'Adding Account...' : 'Add Google Account'}
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
      </div>
    </div>
  );
};
