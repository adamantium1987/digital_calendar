// File: ChoreChartDisplay.tsx
import React, { useEffect, useState } from 'react';

const DAYS = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday'] as const;
type DayName = (typeof DAYS)[number];

// Updated interface for individual chore-day records
interface ChoreDayRecord {
  chore_id: number;
  child_name: string;
  task: string;
  day_name: DayName;
  completed: boolean;
  week_start: string;
}

// For grouped view (original format)
interface Chore {
  id: string;
  child_name: string;
  task: string;
  days: DayName[];
  completed: boolean;
  week_start: string;
}

type Toast = { type: 'success' | 'error' | 'info'; message: string } | null;

export default function ChoreChartDisplay(): JSX.Element {
  const [choreDays, setChoreDays] = useState<ChoreDayRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [loadModalOpen, setLoadModalOpen] = useState(false);
  const [loadPayload, setLoadPayload] = useState('');
  const [filterChild, setFilterChild] = useState('');
  const [filterDay, setFilterDay] = useState('');
  const [weekStart, setWeekStart] = useState<string>(() => getIsoWeekStart(new Date()));
  const [toast, setToast] = useState<Toast>(null);
  const [uploadingCsv, setUploadingCsv] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);

  useEffect(() => {
    void fetchChores();
  }, [weekStart, filterChild, filterDay]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3500);
    return () => clearTimeout(t);
  }, [toast]);

  async function fetchChores(): Promise<void> {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterChild) params.set('child', filterChild);
      if (filterDay) params.set('day', filterDay);
      if (weekStart) params.set('week', weekStart);
      // Use individual format to get per-day records
      params.set('format', 'individual');

      const res = await fetch(`/api/chores?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setChoreDays(Array.isArray(data.chore_days) ? data.chore_days : []);
    } catch (err) {
      console.error('fetchChores error', err);
      setToast({ type: 'error', message: 'Failed to fetch chores' });
    } finally {
      setLoading(false);
    }
  }

  function getIsoWeekStart(d: Date): string {
    const copy = new Date(d);
    const day = copy.getDay(); // 0 = Sunday
    copy.setDate(copy.getDate() - day); // Go back to Sunday
    return copy.toISOString().slice(0, 10);
  }

  function prevWeek(): void {
    const d = new Date(weekStart);
    d.setDate(d.getDate() - 7);
    setWeekStart(getIsoWeekStart(d));
  }

  function nextWeek(): void {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + 7);
    setWeekStart(getIsoWeekStart(d));
  }

  function dayLabel(day: string): string {
    return day.slice(0, 3).toUpperCase();
  }

  // Group chore days by child and task for display
  function groupChoresByTask(): Array<{
    child_name: string;
    task: string;
    chore_id: number;
    days_data: Record<DayName, { available: boolean; completed: boolean }>;
  }> {
    const grouped: Record<string, {
      child_name: string;
      task: string;
      chore_id: number;
      days_data: Record<DayName, { available: boolean; completed: boolean }>;
    }> = {};

    // Initialize all days as unavailable
    const initDaysData = (): Record<DayName, { available: boolean; completed: boolean }> => {
      const data = {} as Record<DayName, { available: boolean; completed: boolean }>;
      DAYS.forEach(day => {
        data[day] = { available: false, completed: false };
      });
      return data;
    };

    choreDays.forEach(record => {
      const key = `${record.child_name}_${record.task}`;

      if (!grouped[key]) {
        grouped[key] = {
          child_name: record.child_name,
          task: record.task,
          chore_id: record.chore_id,
          days_data: initDaysData()
        };
      }

      // Mark this day as available and set completion status
      grouped[key].days_data[record.day_name] = {
        available: true,
        completed: record.completed
      };
    });

    return Object.values(grouped);
  }

  async function toggleComplete(chore_id: number, day: DayName, checked: boolean): Promise<void> {
    try {
      const res = await fetch(`/api/chores/${chore_id}/${day}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed: checked })
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || `HTTP ${res.status}`);
      }
      const json = await res.json();
      setToast({ type: 'success', message: json.message || 'Updated chore' });
      void fetchChores();
    } catch (err) {
      console.error('toggleComplete error', err);
      setToast({ type: 'error', message: 'Failed to update chore' });
    }
  }

  async function handleSync(): Promise<void> {
    setSyncing(true);
    try {
      const res = await fetch('/api/chores/sync', { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setToast({ type: 'success', message: json.message || 'Sync complete' });
      void fetchChores();
    } catch (err) {
      console.error('sync error', err);
      setToast({ type: 'error', message: 'Sync failed' });
    } finally {
      setSyncing(false);
    }
  }

  async function handleLoadFromJSON(): Promise<void> {
    try {
      const payload = loadPayload.trim();
      if (!payload) return setToast({ type: 'error', message: 'Paste JSON payload first' });
      const parsed = JSON.parse(payload);
      const res = await fetch('/api/chores/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsed)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setToast({ type: 'success', message: json.message || 'Loaded chores' });
      setLoadModalOpen(false);
      setLoadPayload('');
      void fetchChores();
    } catch (err: any) {
      console.error('load error', err);
      setToast({ type: 'error', message: 'Load failed: ' + (err?.message || '') });
    }
  }

  // CSV load handler (no file upload needed - just triggers CSV sync)
  async function handleCsvLoad(): Promise<void> {
    setUploadingCsv(true);
    try {
      const res = await fetch('/api/chores/load', { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setToast({ type: 'success', message: json.message || 'CSV loaded' });
      setLoadModalOpen(false);
      void fetchChores();
    } catch (err) {
      console.error('csv load error', err);
      setToast({ type: 'error', message: 'CSV load failed' });
    } finally {
      setUploadingCsv(false);
    }
  }

  function openLoadModal(): void {
    setLoadModalOpen(true);
  }
  function closeLoadModal(): void {
    setLoadModalOpen(false);
    setCsvFile(null);
    setLoadPayload('');
  }

  const groupedChores = groupChoresByTask();

  return (
    <div className="container">
      {/* Week navigation */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
        <button className="nav-btn" onClick={prevWeek}>← Previous Week</button>
        <span>Week of {weekStart}</span>
        <button className="nav-btn" onClick={nextWeek}>Next Week →</button>
        <div style={{ flex: 1 }} />
        <button className="btn" onClick={() => void handleSync()} disabled={syncing}>
          {syncing ? 'Syncing...' : 'Sync CSV'}
        </button>
        <button className="btn" onClick={openLoadModal}>Load Chores</button>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <input
          type="text"
          placeholder="Filter by child..."
          value={filterChild}
          onChange={e => setFilterChild(e.target.value)}
          style={{ padding: 8, borderRadius: 4, border: '1px solid var(--neutral-300)' }}
        />
        <select
          value={filterDay}
          onChange={e => setFilterDay(e.target.value)}
          style={{ padding: 8, borderRadius: 4, border: '1px solid var(--neutral-300)' }}
        >
          <option value="">All days</option>
          {DAYS.map(day => (
            <option key={day} value={day}>{day}</option>
          ))}
        </select>
      </div>

      <div className="status-grid">
        <div className="card">
          <h2>Chore Chart Grid</h2>
          {loading ? (
            <div className="loading">Loading chores...</div>
          ) : groupedChores.length === 0 ? (
            <div className="no-events">No chores for this week.</div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '8px' }}>Child</th>
                    <th style={{ textAlign: 'left', padding: '8px' }}>Task</th>
                    {DAYS.map(d => (
                      <th key={d} style={{ padding: '8px', textAlign: 'center' }}>{dayLabel(d)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {groupedChores.map(chore => (
                    <tr key={`${chore.child_name}_${chore.task}`} style={{ borderTop: '1px solid var(--neutral-200)' }}>
                      <td style={{ padding: '8px' }}>{chore.child_name}</td>
                      <td style={{ padding: '8px' }}>{chore.task}</td>
                      {DAYS.map(day => {
                        const dayData = chore.days_data[day];
                        return (
                          <td key={day} style={{ padding: '8px', textAlign: 'center' }}>
                            {dayData.available ? (
                              <input
                                aria-label={`Complete ${chore.task} for ${chore.child_name} on ${day}`}
                                type="checkbox"
                                checked={dayData.completed}
                                onChange={e => void toggleComplete(chore.chore_id, day, e.target.checked)}
                              />
                            ) : (
                              <span style={{ opacity: 0.25 }}>—</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Load modal */}
      {loadModalOpen && (
        <div style={{ position: 'fixed', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1200 }}>
          <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.4)' }} onClick={closeLoadModal}></div>
          <div className="card" style={{ width: 800, maxWidth: '95%', zIndex: 1201 }}>
            <h3>Load Chores (JSON or CSV)</h3>
            <p>Load from CSV file (chore_chart.csv) or paste JSON data.</p>

            <div style={{ marginBottom: 12 }}>
              <textarea value={loadPayload} onChange={e => setLoadPayload(e.target.value)} rows={6} style={{ width: '100%', padding: 12, borderRadius: 8, border: '1px solid var(--neutral-300)' }} placeholder='{ "chores": [{ "child_name":"Joe", "task":"Feed Dogs", "days":"sunday|monday|tuesday" }] }' />
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 8 }}>
                <button className="nav-btn" onClick={() => setLoadPayload('')}>Clear JSON</button>
                <button className="btn" onClick={() => void handleLoadFromJSON()}>Load JSON</button>
              </div>
            </div>

            <hr />

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <button className="btn" onClick={() => void handleCsvLoad()} disabled={uploadingCsv}>
                {uploadingCsv ? 'Loading...' : 'Load from CSV File'}
              </button>
              <span style={{ fontSize: '0.9em', color: 'var(--neutral-600)' }}>
                Reads from ~/.pi_calendar/chore_chart.csv
              </span>
              <div style={{ flex: 1 }} />
              <button className="nav-btn" onClick={closeLoadModal} type="button">Close</button>
            </div>

          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={`toast ${toast.type === 'success' ? 'toast-success' : toast.type === 'error' ? 'toast-error' : 'toast-info'}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}