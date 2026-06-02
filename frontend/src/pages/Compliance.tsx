import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { complianceAPI } from '../api/client';
import { AlertTriangle } from 'lucide-react';

interface Violation {
  aisle_id: string;
  shelf_id: string;
  violation_type: string;
  sku_id?: string;
  details: string;
}

interface ComplianceData {
  store_id: string;
  overall_score: number;
  grade: string;
  total_sections: number;
  correct_sections: number;
  violations: Violation[];
}

// Icons can be used here

export default function Compliance() {
  const { t } = useTranslation();
  const [data, setData] = useState<ComplianceData | null>(null);

  useEffect(() => {
    complianceAPI.get('STORE01').then(r => setData(r.data)).catch(() => {});
  }, []);

  if (!data) {
    return <div style={{ color: 'var(--text-muted)', padding: 40, textAlign: 'center' }}>{t('common.loading')}</div>;
  }

  const gradeClass = data.grade.startsWith('A') ? 'A' : data.grade.startsWith('B') ? 'B' : data.grade.startsWith('C') ? 'C' : 'D';
  const scoreColor = data.overall_score >= 90 ? 'var(--brand-success)' : data.overall_score >= 80 ? 'var(--brand-info)' : data.overall_score >= 70 ? 'var(--brand-warning)' : 'var(--brand-danger)';

  return (
    <div>
      <div className="grid-3" style={{ marginBottom: 24 }}>
        {/* Score Gauge */}
        <div className="card" style={{ textAlign: 'center' }}>
          <div className="gauge-container">
            <div className="gauge-label">Overall Score</div>
            <div className="gauge-value" style={{ color: scoreColor }}>
              {data.overall_score}%
            </div>
            <div className={`gauge-grade ${gradeClass}`}>{data.grade}</div>
          </div>
        </div>

        {/* Sections */}
        <div className="card" style={{ textAlign: 'center' }}>
          <div className="gauge-container">
            <div className="gauge-label">Sections Checked</div>
            <div className="gauge-value">{data.total_sections}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--brand-success)' }}>
              {data.correct_sections} correct
            </div>
          </div>
        </div>

        {/* Violations Count */}
        <div className="card" style={{ textAlign: 'center' }}>
          <div className="gauge-container">
            <div className="gauge-label">{t('compliance.violations')}</div>
            <div className="gauge-value negative">{data.violations.length}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--brand-warning)' }}>
              needs attention
            </div>
          </div>
        </div>
      </div>

      {/* Compliance Ring */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="card-header">
            <span className="card-title">Compliance Breakdown</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', padding: 20 }}>
            <svg width={200} height={200} viewBox="0 0 200 200">
              {/* Background ring */}
              <circle cx={100} cy={100} r={80} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={16} />
              {/* Progress ring */}
              <circle
                cx={100} cy={100} r={80} fill="none"
                stroke={scoreColor} strokeWidth={16}
                strokeDasharray={`${(data.overall_score / 100) * 502} 502`}
                strokeDashoffset={0}
                strokeLinecap="round"
                transform="rotate(-90 100 100)"
                style={{ transition: 'stroke-dasharray 1s ease' }}
              />
              <text x={100} y={92} textAnchor="middle" fill="var(--text-primary)" fontSize={32} fontWeight={800}>
                {data.overall_score}%
              </text>
              <text x={100} y={118} textAnchor="middle" fill="var(--text-muted)" fontSize={12}>
                {data.grade}
              </text>
            </svg>
          </div>
        </div>

        {/* Violation List */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Active {t('compliance.violations')}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {data.violations.map((v, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '12px 14px', borderRadius: 8,
                background: 'var(--bg-secondary)', border: '1px solid var(--border-subtle)',
              }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 8, display: 'flex',
                  alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem',
                  background: 'rgba(253,203,110,0.1)',
                }}>
                  <AlertTriangle size={16} color="var(--brand-warning)" />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                    {v.violation_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                    {v.details}
                  </div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 2 }}>
                    {v.aisle_id} / {v.shelf_id} {v.sku_id && `/ ${v.sku_id}`}
                  </div>
                </div>
              </div>
            ))}
            {data.violations.length === 0 && (
              <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 20 }}>
                No violations - perfect compliance!
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
