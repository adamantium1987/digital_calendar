import React, { useEffect, useState } from 'react';
import {Header} from "../components/Header";
import {Toast} from "../components/Toast";

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

// Dynamic member colors - will be populated based on actual data
const MEMBER_COLORS = {
  'Rachel/Adam': { bg: 'rgba(34, 197, 94, 0.1)', border: 'rgb(34, 197, 94)', text: 'rgb(22, 163, 74)' },
  'Mason': { bg: 'rgba(251, 113, 133, 0.1)', border: 'rgb(251, 113, 133)', text: 'rgb(225, 29, 72)' },
  'Makenzie': { bg: 'rgba(147, 51, 234, 0.1)', border: 'rgb(147, 51, 234)', text: 'rgb(126, 34, 206)' }
  // 'Mom': { bg: 'rgba(239, 68, 68, 0.1)', border: 'rgb(239, 68, 68)', text: 'rgb(220, 38, 38)' },
} as const;

interface ChoreChartDisplayProps {
  navigate: (path: string) => void;
}

export const ChoreChartDisplay: React.FC<ChoreChartDisplayProps> = ({ navigate }) => {
  const [choreDays, setChoreDays] = useState<ChoreDayRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [loadModalOpen, setLoadModalOpen] = useState(false);
  const [loadPayload, setLoadPayload] = useState('');
  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [uploadingCsv, setUploadingCsv] = useState(false);

  // Get current day name and week start for the selected date
  const currentDayName = DAYS[currentDate.getDay()];
  const weekStart = getIsoWeekStart(currentDate);

  async function fetchChores(): Promise<void> {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      // Always filter by the current day
      params.set('day', currentDayName);
      params.set('week', weekStart);
      params.set('format', 'individual');

      console.log('Fetching chores with params:', params.toString());

      const res = await fetch(`/api/chores?${params.toString()}`, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const contentType = res.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Response is not JSON - check API endpoint routing');
      }

      const data = await res.json();
      console.log('Fetched chore data:', data);

      setChoreDays(Array.isArray(data.chore_days) ? data.chore_days : []);
    } catch (err) {
      console.error('fetchChores error', err);
      setToast({ type: 'error', message: `Failed to fetch chores: ${(err as Error).message}` });
      // Set empty array on error to prevent JSON display
      setChoreDays([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Load data immediately when component mounts or date changes
    void fetchChores();
  }, [currentDate]);

  // Separate effect to ensure we load data on mount
  useEffect(() => {
    // Force initial load after component mounts
    const timer = setTimeout(() => {
      void fetchChores();
    }, 100);

    return () => clearTimeout(timer);
  }, []);

  function getIsoWeekStart(d: Date): string {
    const copy = new Date(d);
    const day = copy.getDay();
    copy.setDate(copy.getDate() - day);
    return copy.toISOString().slice(0, 10);
  }

  function prevDay(): void {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() - 1);
    setCurrentDate(newDate);
  }

  function nextDay(): void {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + 1);
    setCurrentDate(newDate);
  }

  function goToToday(): void {
    setCurrentDate(new Date());
  }

  function formatDate(date: Date): string {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  }

  function formatTime(): string {
    const now = new Date();
    return now.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  }

  function isToday(date: Date): boolean {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  }

  // Group chores by child for the current day
  function groupChoresByChild(): Record<string, ChoreDayRecord[]> {
    const grouped: Record<string, ChoreDayRecord[]> = {};

    // Filter chores for the current day
    const todaysChores = choreDays.filter(chore => chore.day_name === currentDayName);

    todaysChores.forEach(chore => {
      if (!grouped[chore.child_name]) {
        grouped[chore.child_name] = [];
      }
      grouped[chore.child_name].push(chore);
    });

    return grouped;
  }

  function toggleComplete(chore_id: number, day: DayName, checked: boolean): void {
    setChoreDays(prev =>
      prev.map(chore =>
        chore.chore_id === chore_id && chore.day_name === day
          ? { ...chore, completed: checked }
          : chore
      )
    );

    // Show success toast
    setToast({ type: 'success', message: 'Chore updated!' });
  }

  async function handleSync(): Promise<void> {
    setSyncing(true);
    try {
      // Mock sync
      await new Promise(resolve => setTimeout(resolve, 1000));
      setToast({ type: 'success', message: 'Sync complete' });
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

      // Mock load
      setToast({ type: 'success', message: 'Loaded chores' });
      setLoadModalOpen(false);
      setLoadPayload('');
    } catch (err: any) {
      console.error('load error', err);
      setToast({ type: 'error', message: 'Load failed: ' + (err?.message || '') });
    }
  }

  async function handleCsvLoad(): Promise<void> {
    setUploadingCsv(true);
    try {
      // Mock CSV load
      await new Promise(resolve => setTimeout(resolve, 1000));
      setToast({ type: 'success', message: 'CSV loaded' });
      setLoadModalOpen(false);
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
    setLoadPayload('');
  }

  const groupedChores = groupChoresByChild();
  const totalChores = Object.values(groupedChores).flat().length;
  const completedChores = Object.values(groupedChores).flat().filter(c => c.completed).length;

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading">Loading chores for {currentDayName}...</div>
      </div>
    );
  }

  return (
    <div className="container">
      {/*<Header navigate={navigate} title="Chore Chart" />*/}

      {/* Date Navigation */}
      <div className="card card-compact">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={prevDay} className="btn btn-secondary btn-sm">
              ←
            </button>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="mb-0">{formatDate(currentDate)} Chores </h3>
                {isToday(currentDate) && (
                    <span className="status status-success">TODAY</span>
                )}
              </div>
              <p className="text-sm mb-0">
                {formatTime()} • {completedChores} of {totalChores} chores completed
              </p>
            </div>
            <button onClick={nextDay} className="btn btn-secondary btn-sm">
              →
            </button>
          </div>

          <div className="flex items-center gap-3">
            <div style={{
              width: '100px',
              height: '8px',
              backgroundColor: 'var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${totalChores > 0 ? (completedChores / totalChores) * 100 : 0}%`,
                height: '100%',
                backgroundColor: 'var(--primary-500)',
                transition: 'width var(--transition)'
              }}/>
            </div>
            <div className="text-sm" style={{
              fontWeight: '600',
              color: completedChores === totalChores ? 'var(--success-600)' : 'var(--text-secondary)'
            }}>
              {Math.round(totalChores > 0 ? (completedChores / totalChores) * 100 : 0)}%
            </div>
          </div>


          {!isToday(currentDate) && (
              <button onClick={goToToday} className="btn btn-secondary btn-sm">
                Go to Today
              </button>
          )}
        </div>
      </div>

      {/* No Chores Message */}
      {!loading && totalChores === 0 && (
          <div className="card">
            <div className="no-events">
              <h3>No chores scheduled for {currentDayName}</h3>
              <p>Enjoy your free day! 🎉</p>
            </div>
          </div>
      )}

      {/* Main Content - Card Layout */}
      {!loading && totalChores > 0 && (
          <div className="grid grid-responsive">
          {Object.entries(groupedChores).map(([childName, chores]) => {
            const colors = MEMBER_COLORS[childName as keyof typeof MEMBER_COLORS] || MEMBER_COLORS["Rachel/Adam"];

            return (
              <div key={childName} className="card" style={{
                border: `2px solid ${colors.border}`
              }}>
                {/* Header */}
                <div style={{
                  backgroundColor: colors.bg,
                  padding: 'var(--space-4)',
                  margin: 'calc(-1 * var(--space-6))',
                  marginBottom: 'var(--space-4)',
                  borderBottom: `1px solid ${colors.border}`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-3)'
                }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor: colors.border,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontWeight: '600',
                    fontSize: '1rem'
                  }}>
                    {childName.charAt(0)}
                  </div>
                  <div>
                    <h3 className="mb-0" style={{ color: colors.text }}>
                      {childName}
                    </h3>
                    <p className="text-sm mb-0" style={{ opacity: 0.8 }}>
                      {chores.filter(c => c.completed).length} of {chores.length} completed
                    </p>
                  </div>
                </div>

                {/* Chore List */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                  {chores.map((chore) => (
                    <div
                      key={`${chore.chore_id}-${chore.day_name}`}
                      onClick={() => toggleComplete(chore.chore_id, chore.day_name, !chore.completed)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--space-3)',
                        padding: 'var(--space-3)',
                        backgroundColor: chore.completed ? colors.bg : 'var(--bg-tertiary)',
                        borderRadius: 'var(--radius-lg)',
                        cursor: 'pointer',
                        border: `1px solid ${chore.completed ? colors.border : 'var(--border-color)'}`,
                        transition: 'var(--transition)',
                        opacity: chore.completed ? 0.8 : 1
                      }}
                    >
                      <div style={{
                        width: '20px',
                        height: '20px',
                        borderRadius: 'var(--radius-full)',
                        backgroundColor: chore.completed ? colors.border : 'transparent',
                        border: chore.completed ? 'none' : '2px solid var(--border-color)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0
                      }}>
                        {chore.completed && (
                          <span style={{
                            color: 'white',
                            fontSize: '0.75rem',
                            fontWeight: 'bold'
                          }}>
                            ✓
                          </span>
                        )}
                      </div>

                      <div style={{ flex: 1 }}>
                        <div style={{
                          fontSize: '0.875rem',
                          fontWeight: '500',
                          color: chore.completed ? colors.text : 'var(--text-primary)',
                          textDecoration: chore.completed ? 'line-through' : 'none'
                        }}>
                          {chore.task}
                        </div>
                      </div>

                      <div className="status" style={{
                        fontSize: '0.75rem',
                        backgroundColor: chore.completed ? 'transparent' : 'var(--bg-primary)',
                        color: chore.completed ? colors.text : 'var(--text-secondary)',
                        border: 'none'
                      }}>
                        {chore.completed ? '✓' : '○'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Load Modal */}
      {loadModalOpen && (
        <div style={{
          position: 'fixed',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1200,
          backgroundColor: 'rgba(0,0,0,0.4)'
        }}>
          <div className="card" style={{
            width: '800px',
            maxWidth: '95%',
            zIndex: 1201,
            boxShadow: 'var(--shadow-xl)'
          }}>
            <h3 className="mb-4">Load Chores (JSON or CSV)</h3>
            <p className="mb-4">Load from CSV file (chore_chart.csv) or paste JSON data.</p>

            <div className="form-group">
              <textarea
                value={loadPayload}
                onChange={e => setLoadPayload(e.target.value)}
                rows={6}
                style={{ fontFamily: 'var(--font-mono)' }}
                placeholder='{ "chores": [{ "child_name":"Joe", "task":"Feed Dogs", "days":"sunday|monday|tuesday" }] }'
              />
              <div className="flex gap-2 justify-end">
                <button onClick={() => setLoadPayload('')} className="btn btn-secondary btn-sm">
                  Clear JSON
                </button>
                <button onClick={() => void handleLoadFromJSON()} className="btn btn-sm">
                  Load JSON
                </button>
              </div>
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid var(--border-color)', margin: 'var(--space-4) 0' }} />

            <div className="flex items-center gap-3">
              <button
                onClick={() => void handleCsvLoad()}
                disabled={uploadingCsv}
                className="btn"
              >
                {uploadingCsv ? 'Loading...' : 'Load from CSV File'}
              </button>
              <span className="text-sm flex-1">
                Reads from ~/.pi_calendar/chore_chart.csv
              </span>
              <button onClick={closeLoadModal} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
    </div>
  );
};