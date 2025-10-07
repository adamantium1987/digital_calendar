// src/types/calendarEvent.ts

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