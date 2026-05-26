import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { analyticsAPI } from '../api/client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

export default function Analytics() {
  const { t } = useTranslation();
  const [revenueData, setRevenueData] = useState<Array<{ date: string; revenue_lost: number; revenue_recovered: number }>>([]);
  const [summary, setSummary] = useState({ total_lost: 0, total_recovered: 0, recovery_rate: 0 });

  useEffect(() => {
    analyticsAPI.revenueRecovery().then(r => {
      setRevenueData(r.data.daily_data || []);
      setSummary({
        total_lost: r.data.total_revenue_lost || 0,
        total_recovered: r.data.total_revenue_recovered || 0,
        recovery_rate: r.data.recovery_rate || 0,
      });
    }).catch(() => {});
  }, []);

  return (
    <div>
      {/* Revenue KPIs */}
      <div className="kpi-grid" style={{ marginBottom: 24 }}>
        <div className="kpi-card">
          <span className="kpi-label">Revenue Lost (30d)</span>
          <span className="kpi-value negative">
            {'\u20B9'}{(summary.total_lost / 1000).toFixed(0)}K
          </span>
          <span className="kpi-trend down">from stockouts</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Revenue Recovered</span>
          <span className="kpi-value positive">
            {'\u20B9'}{(summary.total_recovered / 1000).toFixed(0)}K
          </span>
          <span className="kpi-trend up">via ShelfIQ alerts</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Recovery Rate</span>
          <span className="kpi-value" style={{ color: summary.recovery_rate > 60 ? 'var(--brand-success)' : 'var(--brand-warning)' }}>
            {summary.recovery_rate}%
          </span>
          <span className="kpi-trend up">target: 70%</span>
        </div>
      </div>

      {/* Revenue Recovery Chart */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <span className="card-title">Revenue Recovery Trend (30d)</span>
        </div>
        {revenueData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={revenueData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
              <XAxis
                dataKey="date" tick={{ fontSize: 10, fill: '#6B6B8D' }}
                tickFormatter={(v) => v.substring(8)}
                interval={2}
              />
              <YAxis tick={{ fontSize: 10, fill: '#6B6B8D' }} width={50}
                tickFormatter={(v) => `${(v/1000).toFixed(0)}K`}
              />
              <Tooltip
                contentStyle={{
                  background: '#1E1E3A', border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 8, fontSize: '0.75rem',
                }}
                formatter={(value: number) => [`\u20B9${value.toLocaleString('en-IN')}`, '']}
              />
              <Bar dataKey="revenue_lost" fill="rgba(225,112,85,0.6)" radius={[4,4,0,0]} name="Lost" />
              <Bar dataKey="revenue_recovered" fill="rgba(0,184,148,0.6)" radius={[4,4,0,0]} name="Recovered" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            {t('common.loading')}
          </div>
        )}
      </div>

      {/* Recovery Rate Over Time */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Daily Recovery Rate (%)</span>
        </div>
        {revenueData.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={revenueData.map(d => ({
              date: d.date,
              rate: d.revenue_lost > 0 ? Math.round(d.revenue_recovered / d.revenue_lost * 100) : 0,
            }))} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="gradRate" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00CEC9" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00CEC9" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6B6B8D' }} tickFormatter={(v) => v.substring(8)} interval={2} />
              <YAxis tick={{ fontSize: 10, fill: '#6B6B8D' }} width={40} domain={[0, 100]} />
              <Tooltip contentStyle={{ background: '#1E1E3A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: '0.75rem' }} />
              <Area type="monotone" dataKey="rate" stroke="#00CEC9" fill="url(#gradRate)" strokeWidth={2} dot={false} name="Recovery %" />
            </AreaChart>
          </ResponsiveContainer>
        ) : null}
      </div>
    </div>
  );
}
