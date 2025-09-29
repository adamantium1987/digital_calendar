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
        background: `linear-gradient(135deg, ${event.color} 0%, ${event.color}dd 100%)`
      }}
    >
      <h3>{event.title}</h3>
      <div className="time">{timeStr}</div>
      {event.location && <div className="location">📍 {event.location}</div>}
    </div>
  );
};