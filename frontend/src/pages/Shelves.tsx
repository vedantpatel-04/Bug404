import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { shelvesAPI } from '../api/client';
import { Eye, AlertTriangle, CheckCircle } from 'lucide-react';

interface ShelfState {
  shelf_id: string;
  aisle_id: string;
  status: string;
  health_score: number;
  last_scan: string;
  detections: number;
  stockouts: number;
}

const demoShelves: ShelfState[] = [
  { shelf_id: 'S01', aisle_id: 'A01', status: 'healthy', health_score: 92, last_scan: '2m ago', detections: 48, stockouts: 0 },
  { shelf_id: 'S02', aisle_id: 'A01', status: 'warning', health_score: 74, last_scan: '5m ago', detections: 35, stockouts: 2 },
  { shelf_id: 'S01', aisle_id: 'A02', status: 'critical', health_score: 45, last_scan: '1m ago', detections: 22, stockouts: 5 },
  { shelf_id: 'S02', aisle_id: 'A02', status: 'healthy', health_score: 88, last_scan: '3m ago', detections: 41, stockouts: 0 },
  { shelf_id: 'S03', aisle_id: 'A02', status: 'healthy', health_score: 95, last_scan: '4m ago', detections: 52, stockouts: 0 },
  { shelf_id: 'S01', aisle_id: 'A03', status: 'warning', health_score: 68, last_scan: '2m ago', detections: 30, stockouts: 3 },
  { shelf_id: 'S02', aisle_id: 'A03', status: 'healthy', health_score: 91, last_scan: '6m ago', detections: 44, stockouts: 0 },
  { shelf_id: 'S01', aisle_id: 'A04', status: 'healthy', health_score: 87, last_scan: '1m ago', detections: 39, stockouts: 1 },
  { shelf_id: 'S02', aisle_id: 'A04', status: 'critical', health_score: 52, last_scan: '3m ago', detections: 28, stockouts: 4 },
  { shelf_id: 'S01', aisle_id: 'A05', status: 'healthy', health_score: 96, last_scan: '2m ago', detections: 55, stockouts: 0 },
];

export default function Shelves() {
  const { t } = useTranslation();
  const [shelves, setShelves] = useState<ShelfState[]>(demoShelves);

  useEffect(() => {
    shelvesAPI.get('STORE01').then(r => {
      if (r.data.shelves?.length > 0) setShelves(r.data.shelves);
    }).catch(() => {});
  }, []);

  const healthy = shelves.filter(s => s.status === 'healthy').length;
  const warning = shelves.filter(s => s.status === 'warning').length;
  const critical = shelves.filter(s => s.status === 'critical').length;

  const statusColor = (s: string) => s === 'critical' ? 'var(--brand-danger)' : s === 'warning' ? 'var(--brand-warning)' : 'var(--brand-success)';

  return (
    <div>
      {/* Summary */}
      <div className="kpi-grid" style={{ marginBottom: 24 }}>
        <div className="kpi-card">
          <span className="kpi-label">Total Shelves</span>
          <span className="kpi-value">{shelves.length}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Healthy</span>
          <span className="kpi-value positive">{healthy}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Warning</span>
          <span className="kpi-value" style={{ color: 'var(--brand-warning)' }}>{warning}</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Critical</span>
          <span className="kpi-value negative">{critical}</span>
        </div>
      </div>

      {/* Shelf Grid */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">{t('nav.shelf_monitoring')} - STORE01</span>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Aisle / Shelf</th>
                <th>Status</th>
                <th>Health</th>
                <th>Detections</th>
                <th>Stockouts</th>
                <th>Last Scan</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {shelves.map((shelf, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{shelf.aisle_id} / {shelf.shelf_id}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span className={`status-dot ${shelf.status === 'critical' ? 'warning' : shelf.status === 'warning' ? 'warning' : 'online'}`} />
                      <span style={{ fontSize: '0.8rem', color: statusColor(shelf.status), fontWeight: 600, textTransform: 'capitalize' }}>
                        {shelf.status}
                      </span>
                    </div>
                  </td>
                  <td>
                    <div style={{
                      width: 80, height: 6, borderRadius: 3, background: 'rgba(255,255,255,0.06)',
                      position: 'relative', overflow: 'hidden',
                    }}>
                      <div style={{
                        width: `${shelf.health_score}%`, height: '100%', borderRadius: 3,
                        background: shelf.health_score >= 80 ? 'var(--brand-success)' : shelf.health_score >= 60 ? 'var(--brand-warning)' : 'var(--brand-danger)',
                        transition: 'width 0.5s ease',
                      }} />
                    </div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginLeft: 8 }}>{shelf.health_score}%</span>
                  </td>
                  <td>{shelf.detections}</td>
                  <td style={{ color: shelf.stockouts > 0 ? 'var(--brand-danger)' : 'var(--brand-success)', fontWeight: 600 }}>
                    {shelf.stockouts}
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{shelf.last_scan}</td>
                  <td>
                    <button className="btn btn-sm btn-ghost"><Eye size={12} /> View</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
