import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { eventsAPI } from '../api/client';
import { CalendarDays, TrendingUp, AlertTriangle } from 'lucide-react';

interface Event {
  id: number;
  event_name: string;
  event_type: string;
  start_date: string;
  end_date: string;
  magnitude: number;
  days_until: number;
  demand_categories: string[];
  predicted_impact: string;
}

// Static Indian events when API returns empty
const demoEvents: Event[] = [
  { id: 1, event_name: 'Navratri', event_type: 'festival', start_date: '2026-10-01', end_date: '2026-10-09', magnitude: 3, days_until: 128, demand_categories: ['Snacks', 'Dairy', 'Beverages'], predicted_impact: 'High' },
  { id: 3, event_name: 'Diwali', event_type: 'festival', start_date: '2026-10-29', end_date: '2026-11-02', magnitude: 3, days_until: 156, demand_categories: ['Snacks', 'Dairy', 'Bakery', 'Household'], predicted_impact: 'High' },
  { id: 9, event_name: 'Janmashtami', event_type: 'festival', start_date: '2026-08-25', end_date: '2026-08-25', magnitude: 2, days_until: 91, demand_categories: ['Dairy', 'Sweets'], predicted_impact: 'Medium' },
  { id: 10, event_name: 'Ganesh Chaturthi', event_type: 'festival', start_date: '2026-09-07', end_date: '2026-09-17', magnitude: 2, days_until: 104, demand_categories: ['Sweets', 'Dairy'], predicted_impact: 'Medium' },
  { id: 14, event_name: 'Raksha Bandhan', event_type: 'festival', start_date: '2026-08-08', end_date: '2026-08-08', magnitude: 2, days_until: 74, demand_categories: ['Sweets', 'Gifting'], predicted_impact: 'Medium' },
  { id: 8, event_name: 'IPL Season', event_type: 'cricket', start_date: '2027-03-22', end_date: '2027-05-30', magnitude: 2, days_until: 300, demand_categories: ['Beverages', 'Snacks', 'Frozen Foods'], predicted_impact: 'Medium' },
];

const typeColors: Record<string, string> = {
  festival: '#FDCB6E',
  cricket: '#55EFC4',
  holiday: '#74B9FF',
  sale_event: '#E17055',
};

export default function FestivalDashboard() {
  const { t } = useTranslation();
  const [events, setEvents] = useState<Event[]>(demoEvents);

  useEffect(() => {
    eventsAPI.upcoming().then(r => {
      if (r.data.events?.length > 0) setEvents(r.data.events);
    }).catch(() => {});
  }, []);

  const urgentEvents = events.filter(e => e.days_until <= 30);
  const upcomingEvents = events.filter(e => e.days_until > 30 && e.days_until <= 90);
  const futureEvents = events.filter(e => e.days_until > 90);

  return (
    <div>
      {/* Summary Cards */}
      <div className="kpi-grid" style={{ marginBottom: 24 }}>
        <div className="kpi-card">
          <span className="kpi-label">Next Event</span>
          <span className="kpi-value" style={{ fontSize: '1.4rem', color: 'var(--brand-warning)' }}>
            {events[0]?.event_name || 'None'}
          </span>
          <span className="kpi-trend up">
            <CalendarDays size={12} /> {events[0]?.days_until || 0} {t('forecast.days_away')}
          </span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">High Impact Events</span>
          <span className="kpi-value negative">{events.filter(e => e.predicted_impact === 'High').length}</span>
          <span className="kpi-trend down"><AlertTriangle size={12} /> Needs prep</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Categories At Risk</span>
          <span className="kpi-value" style={{ fontSize: '1.4rem' }}>
            {[...new Set(events.flatMap(e => e.demand_categories))].length}
          </span>
          <span className="kpi-trend up"><TrendingUp size={12} /> Demand surge</span>
        </div>
        <div className="kpi-card">
          <span className="kpi-label">Total Events Tracked</span>
          <span className="kpi-value">{events.length}</span>
          <span className="kpi-trend up">Indian calendar</span>
        </div>
      </div>

      {/* Urgent Events */}
      {urgentEvents.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: 12, color: 'var(--brand-danger)' }}>
            Urgent (Next 30 Days)
          </h3>
          <div className="grid-auto">
            {urgentEvents.map(evt => <EventCard key={evt.id} event={evt} />)}
          </div>
        </div>
      )}

      {/* Upcoming */}
      <div style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: 12, color: 'var(--brand-warning)' }}>
          Upcoming (30-90 Days)
        </h3>
        <div className="grid-auto">
          {upcomingEvents.length > 0 ? upcomingEvents.map(evt => <EventCard key={evt.id} event={evt} />) :
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No events in this window</p>
          }
        </div>
      </div>

      {/* Future */}
      <div>
        <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: 12, color: 'var(--text-secondary)' }}>
          Future (90+ Days)
        </h3>
        <div className="grid-auto">
          {futureEvents.map(evt => <EventCard key={evt.id} event={evt} />)}
        </div>
      </div>
    </div>
  );
}

function EventCard({ event }: { event: Event }) {
  const { t } = useTranslation();
  const borderColor = typeColors[event.event_type] || '#6C5CE7';

  return (
    <div className="card" style={{ borderLeft: `4px solid ${borderColor}`, cursor: 'pointer' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
        <div>
          <div style={{ fontSize: '1rem', fontWeight: 700 }}>{event.event_name}</div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 2 }}>
            {event.start_date} {event.start_date !== event.end_date && `to ${event.end_date}`}
          </div>
        </div>
        <span className={`festival-badge ${event.predicted_impact === 'High' ? 'high-impact' : ''}`}>
          {event.predicted_impact}
        </span>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
        {event.demand_categories.map((cat, i) => (
          <span key={i} style={{
            padding: '2px 8px', borderRadius: 12, fontSize: '0.65rem', fontWeight: 600,
            background: 'var(--bg-elevated)', color: 'var(--text-secondary)',
          }}>{cat}</span>
        ))}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {event.days_until} {t('forecast.days_away')}
        </span>
        <button className="btn btn-sm btn-ghost">{t('forecast.reorder_now')}</button>
      </div>
    </div>
  );
}
