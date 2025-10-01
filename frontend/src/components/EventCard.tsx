import React from 'react';
import { CalendarEvent } from '../types';

interface EventCardProps {
  event: CalendarEvent;
}

export const EventCard: React.FC<EventCardProps> = ({ event }) => {
  const formatTime = (dateStr: string): string => {
    return new Date(dateStr).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const timeStr = event.all_day
    ? 'All day'
    : `${formatTime(event.start_time)} - ${formatTime(event.end_time)}`;

  return (
    <div
      className="event-card"
      style={{
        background: event.color || '#667eea'
      }}
    >
      <h3>{event.title}</h3>
      <div className="time">{timeStr}</div>
      {event.location && (
        <div className="location">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
            <circle cx="12" cy="10" r="3"></circle>
          </svg>
          {event.location}
        </div>
      )}
    </div>
  );
};