export interface SyncStatus {
  currently_syncing: boolean;
  last_full_sync: string | null;
  total_events: number;
  total_calendars: number;
  errors: any[];
  sources: Record<string, any>;
}

