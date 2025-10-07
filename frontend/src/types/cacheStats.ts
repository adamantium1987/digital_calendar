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