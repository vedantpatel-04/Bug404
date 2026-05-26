import { useTranslation } from 'react-i18next';
import { Bell, Search } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

export default function Topbar({ title }: { title: string }) {
  const { i18n } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const lang = i18n.language;

  const setLang = (l: string) => i18n.changeLanguage(l);

  return (
    <header className="topbar">
      <div className="topbar-left">
        <h2>{title}</h2>
      </div>

      <div className="topbar-right">
        {/* Search */}
        <button className="btn-icon" title="Search">
          <Search size={16} />
        </button>

        {/* Notifications */}
        <button className="btn-icon" title="Notifications" style={{ position: 'relative' }}>
          <Bell size={16} />
          <span style={{
            position: 'absolute', top: -2, right: -2,
            width: 8, height: 8, borderRadius: '50%',
            background: '#E17055',
          }} />
        </button>

        {/* Language Toggle */}
        <div className="lang-toggle">
          <button className={lang === 'en' ? 'active' : ''} onClick={() => setLang('en')}>EN</button>
          <button className={lang === 'hi' ? 'active' : ''} onClick={() => setLang('hi')}>HI</button>
          <button className={lang === 'gu' ? 'active' : ''} onClick={() => setLang('gu')}>GU</button>
        </div>

        {/* User Avatar */}
        {user && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '4px 12px', borderRadius: 8,
            background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%',
              background: 'linear-gradient(135deg, #6C5CE7, #00CEC9)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '0.7rem', fontWeight: 700, color: '#fff',
            }}>
              {user.name.charAt(0)}
            </div>
            <div style={{ lineHeight: 1.2 }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600 }}>{user.name}</div>
              <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>{user.role}</div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
