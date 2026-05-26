import { useTranslation } from 'react-i18next';
import { useLocation, Link } from 'react-router-dom';
import {
  LayoutDashboard, Eye, ClipboardCheck, TrendingUp,
  Bell, BarChart3, CalendarDays, Settings, LogOut,
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

const navItems = [
  { key: 'overview', path: '/', icon: LayoutDashboard },
  { key: 'shelf_monitoring', path: '/shelves', icon: Eye },
  { key: 'compliance', path: '/compliance', icon: ClipboardCheck },
  { key: 'forecast', path: '/forecast', icon: TrendingUp },
  { key: 'alerts', path: '/alerts', icon: Bell, badge: 3 },
  { key: 'analytics', path: '/analytics', icon: BarChart3 },
  { key: 'festival', path: '/festival', icon: CalendarDays },
  { key: 'settings', path: '/settings', icon: Settings },
];

export default function Sidebar() {
  const { t } = useTranslation();
  const location = useLocation();
  const logout = useAuthStore((s) => s.logout);

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div style={{
          width: 36, height: 36, borderRadius: 8,
          background: 'linear-gradient(135deg, #6C5CE7, #00CEC9)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 800, fontSize: '1rem', color: '#fff',
        }}>
          S
        </div>
        <div>
          <h1>{t('app_name')}</h1>
        </div>
        <span className="version">v3.0</span>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section">
          <div className="sidebar-section-label">Main</div>
          {navItems.slice(0, 4).map((item) => (
            <Link
              key={item.key}
              to={item.path}
              className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
            >
              <item.icon />
              <span>{t(`nav.${item.key}`)}</span>
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </Link>
          ))}
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-label">Intelligence</div>
          {navItems.slice(4, 7).map((item) => (
            <Link
              key={item.key}
              to={item.path}
              className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
            >
              <item.icon />
              <span>{t(`nav.${item.key}`)}</span>
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </Link>
          ))}
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-label">System</div>
          {navItems.slice(7).map((item) => (
            <Link
              key={item.key}
              to={item.path}
              className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
            >
              <item.icon />
              <span>{t(`nav.${item.key}`)}</span>
            </Link>
          ))}
          <button className="nav-link" onClick={logout}>
            <LogOut />
            <span>{t('common.logout')}</span>
          </button>
        </div>
      </nav>
    </aside>
  );
}
