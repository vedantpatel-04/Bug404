import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { forecastAPI } from '../api/client';
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

interface ForecastPoint {
  date: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
}

interface FestivalAnnotation {
  event_name: string;
  event_type: string;
  predicted_lift_pct: number;
}

export default function Forecast() {
  const { t } = useTranslation();
  const [data, setData] = useState<ForecastPoint[]>([]);
  const [annotations, setAnnotations] = useState<FestivalAnnotation[]>([]);
  const [sku, setSku] = useState('SKU001');
  const [loading, setLoading] = useState(false);

  const loadForecast = async (skuId: string) => {
    setLoading(true);
    try {
      const res = await forecastAPI.get(skuId);
      setData(res.data.data || []);
      setAnnotations(res.data.festival_annotations || []);
    } catch { /* noop */ }
    setLoading(false);
  };

  useEffect(() => { loadForecast(sku); }, [sku]);

  const skuOptions = ['SKU001', 'SKU002', 'SKU003', 'SKU005', 'SKU007', 'SKU010'];

  return (
    <div>
      {/* Controls */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24, alignItems: 'center' }}>
        <div style={{
          display: 'flex', gap: 6, padding: 4, borderRadius: 8,
          background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)',
        }}>
          {skuOptions.map(s => (
            <button
              key={s}
              className={`btn btn-sm ${sku === s ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setSku(s)}
              style={{ border: 'none' }}
            >
              {s}
            </button>
          ))}
        </div>
        {loading && <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{t('common.loading')}</span>}
      </div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Forecast Chart */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div className="card-header">
            <span className="card-title">{t('forecast.title')} - {sku}</span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              {data.length} data points
            </span>
          </div>
          {data.length > 0 ? (
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="gradForecast" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6C5CE7" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6C5CE7" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradBounds" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00CEC9" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#00CEC9" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
                <XAxis
                  dataKey="date" tick={{ fontSize: 10, fill: '#6B6B8D' }}
                  tickFormatter={(v) => v.substring(5)}
                  interval={Math.floor(data.length / 8)}
                />
                <YAxis tick={{ fontSize: 10, fill: '#6B6B8D' }} width={40} />
                <Tooltip
                  contentStyle={{
                    background: '#1E1E3A', border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 8, fontSize: '0.75rem',
                  }}
                  labelStyle={{ color: '#FAFAFA' }}
                />
                <Area type="monotone" dataKey="yhat_upper" stroke="none" fill="url(#gradBounds)" />
                <Area type="monotone" dataKey="yhat_lower" stroke="none" fill="transparent" />
                <Area
                  type="monotone" dataKey="yhat" stroke="#6C5CE7" strokeWidth={2}
                  fill="url(#gradForecast)" dot={false}
                />
                <Line type="monotone" dataKey="yhat_upper" stroke="#00CEC9" strokeWidth={1} strokeDasharray="4 4" dot={false} />
                <Line type="monotone" dataKey="yhat_lower" stroke="#00CEC9" strokeWidth={1} strokeDasharray="4 4" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 350, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              {loading ? t('common.loading') : t('common.no_data')}
            </div>
          )}
        </div>
      </div>

      {/* Festival Impact Cards */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">{t('forecast.festival_impact')}</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
          {annotations.map((ann, i) => (
            <div key={i} style={{
              padding: 14, borderRadius: 10, background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              transition: 'all 200ms ease',
            }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                {ann.event_name}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className={`risk-badge ${ann.predicted_lift_pct > 30 ? 'red' : ann.predicted_lift_pct > 15 ? 'amber' : 'green'}`}>
                  +{ann.predicted_lift_pct}%
                </span>
                <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{ann.event_type}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
