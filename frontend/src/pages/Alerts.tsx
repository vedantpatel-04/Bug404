import { useEffect, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { alertsAPI } from '../api/client';
import { CheckCircle, Package, AlertTriangle, Tag } from 'lucide-react';

interface Alert {
  alert_id: number;
  alert_type: string;
  severity: number;
  store_id: string;
  aisle_id: string;
  shelf_id: string;
  sku_id: string;
  message: string;
  revenue_impact: number;
  suggested_action: string;
  acknowledged: boolean;
  created_at: string;
}

const SEVERITY_CLASS: Record<number, string> = { 5: 'critical', 4: 'critical', 3: 'high', 2: 'medium', 1: 'low' };
const SEVERITY_LABEL: Record<number, string> = { 5: 'CRITICAL', 4: 'CRITICAL', 3: 'HIGH', 2: 'MEDIUM', 1: 'LOW' };

const alertIcons: Record<string, ReactNode> = {
  stockout: <Package size={18} />,
  low_stock: <AlertTriangle size={18} />,
  planogram_violation: <Tag size={18} />,
};

// Demo alerts when backend has none
const demoAlerts: Alert[] = [
  { alert_id: 1, alert_type: 'stockout', severity: 5, store_id: 'STORE01', aisle_id: 'A02', shelf_id: 'S03', sku_id: 'SKU007', message: 'Amul Butter 500g out of stock - high demand item', revenue_impact: 2400, suggested_action: 'Replenish from backstore immediately', acknowledged: false, created_at: new Date(Date.now() - 300000).toISOString() },
  { alert_id: 2, alert_type: 'low_stock', severity: 3, store_id: 'STORE01', aisle_id: 'A04', shelf_id: 'S01', sku_id: 'SKU012', message: 'Parle-G biscuit stock below threshold (3 units remaining)', revenue_impact: 800, suggested_action: 'Reorder from distributor - lead time 24h', acknowledged: false, created_at: new Date(Date.now() - 1200000).toISOString() },
  { alert_id: 3, alert_type: 'planogram_violation', severity: 2, store_id: 'STORE01', aisle_id: 'A01', shelf_id: 'S02', sku_id: 'SKU003', message: 'Coca-Cola 2L placed in Snacks section instead of Beverages', revenue_impact: 0, suggested_action: 'Move to Beverages aisle A03, shelf S01', acknowledged: false, created_at: new Date(Date.now() - 3600000).toISOString() },
  { alert_id: 4, alert_type: 'stockout', severity: 4, store_id: 'STORE01', aisle_id: 'A05', shelf_id: 'S04', sku_id: 'SKU021', message: 'Maggi 2-Minute Noodles completely out - weekend surge expected', revenue_impact: 3200, suggested_action: 'Emergency reorder via WhatsApp quick-action', acknowledged: false, created_at: new Date(Date.now() - 600000).toISOString() },
  { alert_id: 5, alert_type: 'low_stock', severity: 2, store_id: 'STORE01', aisle_id: 'A03', shelf_id: 'S02', sku_id: 'SKU015', message: 'Haldiram Namkeen low stock ahead of Navratri', revenue_impact: 1500, suggested_action: 'Festival stock-up recommended - order 2x usual quantity', acknowledged: false, created_at: new Date(Date.now() - 7200000).toISOString() },
];

export default function Alerts() {
  const { t } = useTranslation();
  const [alerts, setAlerts] = useState<Alert[]>(demoAlerts);
  const [filter, setFilter] = useState('all');
  const [resolving, setResolving] = useState<number | null>(null);

  useEffect(() => {
    alertsAPI.list().then(r => {
      if (r.data.alerts?.length > 0) setAlerts(r.data.alerts);
    }).catch(() => {});
  }, []);

  const filtered = filter === 'all' ? alerts : alerts.filter(a => a.alert_type === filter);

  const handleResolve = async (id: number) => {
    setResolving(id);
    try {
      await alertsAPI.resolve(id, 'Resolved from dashboard');
      setAlerts(prev => prev.map(a => a.alert_id === id ? { ...a, acknowledged: true } : a));
    } catch { /* noop */ }
    setResolving(null);
  };

  const timeAgo = (iso: string) => {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  return (
    <div>
      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {['all', 'stockout', 'low_stock', 'planogram_violation'].map(f => (
          <button
            key={f}
            className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? 'All' : t(`alerts.${f}`)}
            {f !== 'all' && (
              <span style={{ marginLeft: 4, opacity: 0.7 }}>
                ({alerts.filter(a => a.alert_type === f).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Alert List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {filtered.map(alert => (
          <div
            key={alert.alert_id}
            className={`alert-card ${SEVERITY_CLASS[alert.severity]}`}
            style={{ opacity: alert.acknowledged ? 0.5 : 1 }}
          >
            <div className={`alert-avatar ${alert.alert_type.replace('_', '-')}`}>
              {alertIcons[alert.alert_type] || <AlertTriangle size={18} />}
            </div>
            <div className="alert-body">
              <div className="alert-title">
                {alert.message}
              </div>
              <div className="alert-message">
                {alert.suggested_action}
              </div>
              <div className="alert-meta">
                <span className={`risk-badge ${alert.severity >= 4 ? 'red' : alert.severity >= 3 ? 'amber' : 'green'}`}>
                  {SEVERITY_LABEL[alert.severity]}
                </span>
                <span>{alert.aisle_id} / {alert.shelf_id}</span>
                <span>{alert.sku_id}</span>
                {alert.revenue_impact > 0 && (
                  <span style={{ color: 'var(--brand-danger)' }}>
                    -{'\u20B9'}{alert.revenue_impact.toLocaleString('en-IN')}
                  </span>
                )}
                <span>{timeAgo(alert.created_at)}</span>
              </div>
              {!alert.acknowledged && (
                <div className="alert-actions">
                  <button
                    className="btn btn-sm btn-success"
                    onClick={() => handleResolve(alert.alert_id)}
                    disabled={resolving === alert.alert_id}
                  >
                    <CheckCircle size={12} />
                    {resolving === alert.alert_id ? 'Resolving...' : t('alerts.mark_resolved')}
                  </button>
                  <button className="btn btn-sm btn-ghost">
                    {t('alerts.reassign')}
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
