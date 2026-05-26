import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../store/authStore';
import { Shield, Globe, Bell, Palette } from 'lucide-react';

export default function Settings() {
  const { t, i18n } = useTranslation();
  const user = useAuthStore((s) => s.user);

  return (
    <div style={{ maxWidth: 700 }}>
      {/* Profile */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <span className="card-title">Profile</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
          <div style={{
            width: 56, height: 56, borderRadius: '50%',
            background: 'linear-gradient(135deg, #6C5CE7, #00CEC9)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.3rem', fontWeight: 700, color: '#fff',
          }}>{user?.name?.charAt(0) || 'U'}</div>
          <div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{user?.name || 'User'}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{user?.email}</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-accent)', marginTop: 2 }}>{user?.role}</div>
          </div>
        </div>
      </div>

      {/* Language */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <span className="card-title"><Globe size={14} style={{ display: 'inline', marginRight: 6 }} />Language / Bhasha</span>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          {[
            { code: 'en', label: 'English', native: 'English' },
            { code: 'hi', label: 'Hindi', native: 'हिन्दी' },
            { code: 'gu', label: 'Gujarati', native: 'ગુજરાતી' },
          ].map(lang => (
            <button
              key={lang.code}
              className={`btn ${i18n.language === lang.code ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => i18n.changeLanguage(lang.code)}
              style={{ flex: 1, flexDirection: 'column', gap: 2, padding: '12px 16px' }}
            >
              <span style={{ fontWeight: 700 }}>{lang.native}</span>
              <span style={{ fontSize: '0.65rem', opacity: 0.7 }}>{lang.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Notifications */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <span className="card-title"><Bell size={14} style={{ display: 'inline', marginRight: 6 }} />Notification Preferences</span>
        </div>
        {[
          { label: 'WhatsApp Alerts', desc: 'Stockout alerts via WhatsApp Business', enabled: true },
          { label: 'Email Digest', desc: 'Daily summary at 6 PM IST', enabled: true },
          { label: 'Push Notifications', desc: 'Browser push for critical alerts', enabled: false },
          { label: 'SMS Backup', desc: 'SMS fallback when WhatsApp unavailable', enabled: false },
        ].map((pref, i) => (
          <div key={i} style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '12px 0', borderBottom: i < 3 ? '1px solid var(--border-subtle)' : 'none',
          }}>
            <div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{pref.label}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{pref.desc}</div>
            </div>
            <div style={{
              width: 40, height: 22, borderRadius: 11, padding: 2,
              background: pref.enabled ? 'var(--brand-success)' : 'var(--bg-elevated)',
              cursor: 'pointer', transition: 'all 200ms ease',
            }}>
              <div style={{
                width: 18, height: 18, borderRadius: '50%', background: 'white',
                transform: pref.enabled ? 'translateX(18px)' : 'translateX(0)',
                transition: 'transform 200ms ease',
              }} />
            </div>
          </div>
        ))}
      </div>

      {/* Security */}
      <div className="card">
        <div className="card-header">
          <span className="card-title"><Shield size={14} style={{ display: 'inline', marginRight: 6 }} />Security</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '10px 14px', borderRadius: 8, background: 'var(--bg-secondary)',
          }}>
            <div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>Data Encryption</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>AES-256-CBC field-level</div>
            </div>
            <span className="risk-badge green">Active</span>
          </div>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '10px 14px', borderRadius: 8, background: 'var(--bg-secondary)',
          }}>
            <div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>JWT Authentication</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>HS256, 1h access / 7d refresh</div>
            </div>
            <span className="risk-badge green">Active</span>
          </div>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '10px 14px', borderRadius: 8, background: 'var(--bg-secondary)',
          }}>
            <div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>RBAC</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>5-level role hierarchy</div>
            </div>
            <span className="risk-badge green">Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}
