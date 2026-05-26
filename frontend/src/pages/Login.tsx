import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '../api/client';
import { useAuthStore } from '../store/authStore';

export default function Login() {
  const [email, setEmail] = useState('owner@rajesh-supermart.in');
  const [password, setPassword] = useState('owner123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await authAPI.login(email, password);
      login(res.data.access_token, res.data.user);
      navigate('/');
    } catch {
      setError('Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg-primary)',
    }}>
      <div style={{
        width: 400, padding: 40, borderRadius: 16,
        background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
        boxShadow: 'var(--shadow-lg)',
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 14, margin: '0 auto 16px',
            background: 'linear-gradient(135deg, #6C5CE7, #00CEC9)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.5rem', fontWeight: 800, color: '#fff',
          }}>S</div>
          <h1 style={{
            fontSize: '1.5rem', fontWeight: 800,
            background: 'linear-gradient(135deg, #6C5CE7, #00CEC9)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>ShelfIQ</h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 4 }}>
            India's Shelf Intelligence Platform
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
              Email
            </label>
            <input
              type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              style={{
                width: '100%', padding: '10px 14px', borderRadius: 8,
                background: 'var(--bg-secondary)', border: '1px solid var(--border-medium)',
                color: 'var(--text-primary)', fontSize: '0.875rem',
                fontFamily: 'var(--font-sans)', outline: 'none',
              }}
            />
          </div>
          <div style={{ marginBottom: 24 }}>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6 }}>
              Password
            </label>
            <input
              type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%', padding: '10px 14px', borderRadius: 8,
                background: 'var(--bg-secondary)', border: '1px solid var(--border-medium)',
                color: 'var(--text-primary)', fontSize: '0.875rem',
                fontFamily: 'var(--font-sans)', outline: 'none',
              }}
            />
          </div>
          {error && <p style={{ color: 'var(--brand-danger)', fontSize: '0.8rem', marginBottom: 16 }}>{error}</p>}
          <button className="btn btn-primary" type="submit" disabled={loading}
            style={{ width: '100%', padding: '12px', fontSize: '0.9rem' }}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p style={{ textAlign: 'center', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 24 }}>
          Demo: owner@rajesh-supermart.in / owner123
        </p>
      </div>
    </div>
  );
}
