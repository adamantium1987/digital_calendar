export interface SyncStatus {
  currently_syncing: boolean;
  last_full_sync: string | null;
  total_events: number;
  total_calendars: number;
  errors: any[];
  sources: Record<string, any>;
}

export interface CacheStats {
  total_events: number;
  total_calendars: number;
  events_by_account: Record<string, number>;
  calendars_by_account: Record<string, number>;
  date_range: {
    earliest: string | null;
    latest: string | null;
  };
}

export interface Account {
  id: string;
  display_name: string;
  username?: string;
  authenticated?: boolean;
  sync_status?: string;
}

export interface Accounts {
  google: Account[];
  apple: Account[];
}

export interface CalendarEvent {
  id: string;
  title: string;
  description: string;
  start_time: string;
  end_time: string;
  all_day: boolean;
  location: string;
  calendar_id: string;
  account_id: string;
  color: string;
  attendees: string[];
}

export interface ToastProps {
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  onClose: () => void;
}

export type ViewType = 'day' | 'week' | 'month';