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

type Toast = { type: 'success' | 'error' | 'info'; message: string } | null;

// Dynamic member colors - will be populated based on actual data
const MEMBER_COLORS = {
  'Dad': { bg: 'rgba(34, 197, 94, 0.1)', border: 'rgb(34, 197, 94)', text: 'rgb(22, 163, 74)' },
  'Ella': { bg: 'rgba(251, 113, 133, 0.1)', border: 'rgb(251, 113, 133)', text: 'rgb(225, 29, 72)' },
  'Harper': { bg: 'rgba(147, 51, 234, 0.1)', border: 'rgb(147, 51, 234)', text: 'rgb(126, 34, 206)' },
  'Mom': { bg: 'rgba(239, 68, 68, 0.1)', border: 'rgb(239, 68, 68)', text: 'rgb(220, 38, 38)' },
} as const;

export default function ChoreChartDisplay(): JSX.Element {
  const [choreDays, setChoreDays] = useState<ChoreDayRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [loadModalOpen, setLoadModalOpen] = useState(false);
  const [loadPayload, setLoadPayload] = useState('');
  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [toast, setToast] = useState<Toast>(null);
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

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3500);
    return () => clearTimeout(t);
  }, [toast]);

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

  return (
    <div style={{
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      backgroundColor: '#f8fafc',
      minHeight: '100vh',
      padding: '16px'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '24px',
        backgroundColor: 'white',
        padding: '16px 24px',
        borderRadius: '12px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={prevDay}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '18px',
                cursor: 'pointer',
                padding: '4px 8px',
                borderRadius: '6px',
                color: '#64748b'
              }}
            >
              ←
            </button>
            <div>
              <div style={{
                fontSize: '18px',
                fontWeight: '600',
                color: '#1e293b',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                {formatDate(currentDate)}
                {isToday(currentDate) && (
                  <span style={{
                    fontSize: '12px',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    fontWeight: '500'
                  }}>
                    TODAY
                  </span>
                )}
              </div>
              <div style={{ fontSize: '14px', color: '#64748b' }}>
                {formatTime()} • {completedChores} of {totalChores} chores completed
              </div>
            </div>
            <button
              onClick={nextDay}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '18px',
                cursor: 'pointer',
                padding: '4px 8px',
                borderRadius: '6px',
                color: '#64748b'
              }}
            >
              →
            </button>
          </div>

          {!isToday(currentDate) && (
            <button
              onClick={goToToday}
              style={{
                padding: '6px 12px',
                backgroundColor: '#f1f5f9',
                color: '#475569',
                border: 'none',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              Go to Today
            </button>
          )}
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={() => void handleSync()}
            disabled={syncing}
            style={{
              padding: '8px 16px',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: syncing ? 'not-allowed' : 'pointer',
              opacity: syncing ? 0.6 : 1
            }}
          >
            {syncing ? 'Syncing...' : 'Sync CSV'}
          </button>
          <button
            onClick={openLoadModal}
            style={{
              padding: '8px 16px',
              backgroundColor: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer'
            }}
          >
            Load Chores
          </button>
        </div>
      </div>

      {/* Day Summary */}
      {totalChores > 0 && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '16px 24px',
          marginBottom: '20px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <div style={{ fontSize: '16px', fontWeight: '600', color: '#1e293b' }}>
              {currentDayName.charAt(0).toUpperCase() + currentDayName.slice(1)} Chores
            </div>
            <div style={{ fontSize: '14px', color: '#64748b' }}>
              {Object.keys(groupedChores).length} family members with chores today
            </div>
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <div style={{
              width: '100px',
              height: '8px',
              backgroundColor: '#e2e8f0',
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${totalChores > 0 ? (completedChores / totalChores) * 100 : 0}%`,
                height: '100%',
                backgroundColor: '#3b82f6',
                transition: 'width 0.3s ease'
              }} />
            </div>
            <div style={{
              fontSize: '14px',
              fontWeight: '600',
              color: completedChores === totalChores ? '#059669' : '#64748b'
            }}>
              {Math.round(totalChores > 0 ? (completedChores / totalChores) * 100 : 0)}%
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '200px',
          fontSize: '16px',
          color: '#64748b'
        }}>
          Loading chores for {currentDayName}...
        </div>
      )}

      {/* No Chores Message */}
      {!loading && totalChores === 0 && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '40px 24px',
          textAlign: 'center',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <div style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b', marginBottom: '8px' }}>
            No chores scheduled for {currentDayName}
          </div>
          <div style={{ fontSize: '14px', color: '#64748b' }}>
            Enjoy your free day! 🎉
          </div>
        </div>
      )}

      {/* Main Content - Card Layout */}
      {!loading && totalChores > 0 && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '20px',
          maxWidth: '1400px',
          margin: '0 auto'
        }}>
          {Object.entries(groupedChores).map(([childName, chores]) => {
            const colors = MEMBER_COLORS[childName as keyof typeof MEMBER_COLORS] || MEMBER_COLORS.Dad;

            return (
              <div key={childName} style={{
                backgroundColor: 'white',
                borderRadius: '16px',
                overflow: 'hidden',
                boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                border: `2px solid ${colors.border}`
              }}>
                {/* Header */}
                <div style={{
                  backgroundColor: colors.bg,
                  padding: '16px 20px',
                  borderBottom: `1px solid ${colors.border}`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px'
                }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    backgroundColor: colors.border,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontWeight: '600',
                    fontSize: '16px'
                  }}>
                    {childName.charAt(0)}
                  </div>
                  <div>
                    <div style={{
                      fontSize: '18px',
                      fontWeight: '600',
                      color: colors.text
                    }}>
                      {childName}
                    </div>
                    <div style={{
                      fontSize: '12px',
                      color: '#64748b',
                      opacity: 0.8
                    }}>
                      {chores.filter(c => c.completed).length} of {chores.length} completed
                    </div>
                  </div>
                </div>

                {/* Chore List */}
                <div style={{ padding: '12px' }}>
                  {chores.map((chore) => (
                    <div
                      key={`${chore.chore_id}-${chore.day_name}`}
                      onClick={() => toggleComplete(chore.chore_id, chore.day_name, !chore.completed)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        padding: '12px',
                        margin: '4px 0',
                        backgroundColor: chore.completed ? colors.bg : '#f8fafc',
                        borderRadius: '12px',
                        cursor: 'pointer',
                        border: `1px solid ${chore.completed ? colors.border : '#e2e8f0'}`,
                        transition: 'all 0.2s ease',
                        opacity: chore.completed ? 0.8 : 1
                      }}
                    >
                      <div style={{
                        width: '20px',
                        height: '20px',
                        borderRadius: '50%',
                        backgroundColor: chore.completed ? colors.border : 'transparent',
                        border: chore.completed ? 'none' : `2px solid #cbd5e1`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0
                      }}>
                        {chore.completed && (
                          <div style={{
                            color: 'white',
                            fontSize: '12px',
                            fontWeight: 'bold'
                          }}>
                            ✓
                          </div>
                        )}
                      </div>

                      <div style={{ flex: 1 }}>
                        <div style={{
                          fontSize: '14px',
                          fontWeight: '500',
                          color: chore.completed ? colors.text : '#1e293b',
                          textDecoration: chore.completed ? 'line-through' : 'none'
                        }}>
                          {chore.task}
                        </div>
                      </div>

                      <div style={{
                        fontSize: '12px',
                        fontWeight: '500',
                        color: chore.completed ? colors.text : '#64748b',
                        backgroundColor: chore.completed ? 'transparent' : '#f1f5f9',
                        padding: '4px 8px',
                        borderRadius: '6px'
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

      {/* Load modal */}
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
          <div style={{
            backgroundColor: 'white',
            borderRadius: '16px',
            padding: '24px',
            width: '800px',
            maxWidth: '95%',
            zIndex: 1201,
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '20px', fontWeight: '600' }}>
              Load Chores (JSON or CSV)
            </h3>
            <p style={{ margin: '0 0 20px 0', color: '#64748b' }}>
              Load from CSV file (chore_chart.csv) or paste JSON data.
            </p>

            <div style={{ marginBottom: '20px' }}>
              <textarea
                value={loadPayload}
                onChange={e => setLoadPayload(e.target.value)}
                rows={6}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '8px',
                  border: '1px solid #cbd5e1',
                  fontSize: '14px',
                  fontFamily: 'monospace'
                }}
                placeholder='{ "chores": [{ "child_name":"Joe", "task":"Feed Dogs", "days":"sunday|monday|tuesday" }] }'
              />
              <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '8px' }}>
                <button
                  onClick={() => setLoadPayload('')}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#f1f5f9',
                    color: '#475569',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '14px',
                    cursor: 'pointer'
                  }}
                >
                  Clear JSON
                </button>
                <button
                  onClick={() => void handleLoadFromJSON()}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '14px',
                    cursor: 'pointer'
                  }}
                >
                  Load JSON
                </button>
              </div>
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid #e2e8f0', margin: '20px 0' }} />

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <button
                onClick={() => void handleCsvLoad()}
                disabled={uploadingCsv}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  cursor: uploadingCsv ? 'not-allowed' : 'pointer',
                  opacity: uploadingCsv ? 0.6 : 1
                }}
              >
                {uploadingCsv ? 'Loading...' : 'Load from CSV File'}
              </button>
              <span style={{ fontSize: '14px', color: '#64748b', flex: 1 }}>
                Reads from ~/.pi_calendar/chore_chart.csv
              </span>
              <button
                onClick={closeLoadModal}
                type="button"
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#f1f5f9',
                  color: '#475569',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  cursor: 'pointer'
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          padding: '12px 20px',
          borderRadius: '8px',
          backgroundColor: toast.type === 'success' ? '#059669' : toast.type === 'error' ? '#dc2626' : '#3b82f6',
          color: 'white',
          fontSize: '14px',
          fontWeight: '500',
          zIndex: 1000,
          boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'
        }}>
          {toast.message}
        </div>
      )}
    </div>
  );
}