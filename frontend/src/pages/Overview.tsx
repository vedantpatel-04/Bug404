import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { TrendingUp, TrendingDown, AlertTriangle, Shield, IndianRupee, Clock } from 'lucide-react';
import { healthAPI, complianceAPI, eventsAPI, analyticsAPI } from '../api/client';

interface KPIData {
  health: number;
  alerts: number;
  compliance: number;
  revenue: number;
  stockouts: number;
  resolution: string;
}

interface EventData {
  event_name: string;
  event_type: string;
  days_until: number;
  predicted_impact: string;
  demand_categories: string[];
}

export default function Overview() {
  const { t } = useTranslation();
  const [kpi, setKpi] = useState<KPIData>({
    health: 87, alerts: 3, compliance: 85.2, revenue: 45200, stockouts: 12, resolution: '8m',
  });
  const [events, setEvents] = useState<EventData[]>([]);
  const [heatmapData, setHeatmapData] = useState<Array<{ aisle: string; hour: number; stockout_count: number; severity_avg: number }>>([]);
  const [systemStatus, setSystemStatus] = useState({ db: 'loading', ml: 'loading', redis: 'loading' });

  useEffect(() => {
    // Load real data
    healthAPI.check().then(r => {
      const d = r.data;
      setSystemStatus({ db: d.db, ml: d.ml_models, redis: d.redis });
    }).catch(() => {});

    complianceAPI.get('STORE01').then(r => {
      setKpi(prev => ({ ...prev, compliance: r.data.overall_score }));
    }).catch(() => {});

    eventsAPI.upcoming().then(r => {
      setEvents(r.data.events || []);
    }).catch(() => {});

    analyticsAPI.heatmap().then(r => {
      setHeatmapData(r.data.data || []);
    }).catch(() => {});
  }, []);

  const kpiCards = [
    { label: t('kpi.health_score'), value: `${kpi.health}%`, trend: '+2.3%', up: true, icon: <TrendingUp size={16} /> },
    { label: t('kpi.active_alerts'), value: kpi.alerts.toString(), trend: '-5 today', up: false, icon: <AlertTriangle size={16} />, negative: true },
    { label: t('kpi.compliance_score'), value: `${kpi.compliance}%`, trend: '+1.8%', up: true, icon: <Shield size={16} /> },
    { label: t('kpi.revenue_saved'), value: `₹${(kpi.revenue / 1000).toFixed(1)}K`, trend: '+₹8.2K', up: true, icon: <IndianRupee size={16} /> },
    { label: t('kpi.stockouts_prevented'), value: kpi.stockouts.toString(), trend: 'this week', up: true, icon: <TrendingDown size={16} /> },
    { label: t('kpi.avg_resolution'), value: kpi.resolution, trend: '-2m from avg', up: true, icon: <Clock size={16} /> },
  ];

  // Build heatmap grid
  const aisles = [...new Set(heatmapData.map(d => d.aisle))].sort();
  const hours = Array.from({ length: 14 }, (_, i) => i + 8);

  const getHeatmapColor = (count: number) => {
    if (count === 0) return 'rgba(255,255,255,0.03)';
    if (count <= 2) return 'rgba(0,184,148,0.3)';
    if (count <= 5) return 'rgba(253,203,110,0.4)';
    if (count <= 8) return 'rgba(225,112,85,0.5)';
    return 'rgba(225,112,85,0.8)';
  };

  const getHeatCount = (aisle: string, hour: number) => {
    const cell = heatmapData.find(d => d.aisle === aisle && d.hour === hour);
    return cell?.stockout_count || 0;
  };

  return (
    <div>
      {/* KPI Grid */}
      <div className="kpi-grid">
        {kpiCards.map((card, i) => (
          <div className="kpi-card" key={i}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="kpi-label">{card.label}</span>
              <span style={{ color: 'var(--text-muted)' }}>{card.icon}</span>
            </div>
            <span className={`kpi-value ${card.negative ? 'negative' : ''}`}>{card.value}</span>
            <span className={`kpi-trend ${card.up ? 'up' : 'down'}`}>
              {card.up ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {card.trend}
            </span>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Upcoming Festivals */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">{t('nav.festival')} - Upcoming Events</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {events.length === 0 && (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No upcoming events in the next 60 days</p>
            )}
            {events.slice(0, 5).map((evt, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '10px 14px', borderRadius: 8, background: 'var(--bg-secondary)',
                border: '1px solid var(--border-subtle)',
              }}>
                <div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{evt.event_name}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    {evt.demand_categories.join(', ')}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span className={`festival-badge ${evt.predicted_impact === 'High' ? 'high-impact' : ''}`}>
                    {evt.predicted_impact}
                  </span>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 4 }}>
                    {evt.days_until} {t('forecast.days_away')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* System Status */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">System Health</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[
              { label: 'Database', status: systemStatus.db },
              { label: 'ML Models', status: systemStatus.ml },
              { label: 'Cache', status: systemStatus.redis },
            ].map((item, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '10px 14px', borderRadius: 8, background: 'var(--bg-secondary)',
              }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>{item.label}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className={`status-dot ${item.status.includes('error') ? 'warning' : 'online'}`} />
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    {item.status === 'loading' ? '...' : item.status.substring(0, 30)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Stockout Heatmap */}
      {heatmapData.length > 0 && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Stockout Heatmap (Aisle x Hour)</span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <div style={{ display: 'grid', gridTemplateColumns: `60px repeat(${hours.length}, 1fr)`, gap: 2 }}>
              {/* Header */}
              <div />
              {hours.map(h => (
                <div key={h} style={{ textAlign: 'center', fontSize: '0.6rem', color: 'var(--text-muted)', padding: 4 }}>
                  {h}:00
                </div>
              ))}

              {/* Rows */}
              {aisles.map(aisle => (
                <>
                  <div key={`label-${aisle}`} style={{ fontSize: '0.7rem', fontWeight: 600, display: 'flex', alignItems: 'center', paddingLeft: 8 }}>
                    {aisle}
                  </div>
                  {hours.map(hour => {
                    const count = getHeatCount(aisle, hour);
                    return (
                      <div
                        key={`${aisle}-${hour}`}
                        title={`${aisle} @ ${hour}:00 — ${count} stockouts`}
                        style={{
                          height: 28, borderRadius: 4,
                          background: getHeatmapColor(count),
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '0.6rem', color: count > 0 ? 'var(--text-primary)' : 'transparent',
                          transition: 'all 150ms ease',
                          cursor: 'pointer',
                        }}
                      >
                        {count > 0 ? count : ''}
                      </div>
                    );
                  })}
                </>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
