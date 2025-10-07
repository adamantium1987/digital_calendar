// Optimized version of EventItem with React.memo
import React, { memo } from 'react';
import { CalendarEvent } from '../../types/calendarEvent';

interface EventItemProps {
  event: CalendarEvent;
  onClick?: () => void;
  compact?: boolean;
  showTime?: boolean;
  maxTitleLength?: number;
}

/**
 * Memoized EventItem component
 * Only re-renders when props change
 */
export const EventItem: React.FC<EventItemProps> = memo(
  ({ event, onClick, compact = false, showTime = true, maxTitleLength }) => {
    const title =
      maxTitleLength && event.title.length > maxTitleLength
        ? event.title.substring(0, maxTitleLength) + '...'
        : event.title;

    const formattedTime = React.useMemo(() => {
      if (!showTime || event.all_day) return null;
      return new Date(event.start_time).toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      });
    }, [event.start_time, event.all_day, showTime]);

    return (
      <div
        className={compact ? 'compact-event' : 'event-card'}
        style={{ background: event.color || 'var(--primary-500)' }}
        onClick={onClick}
      >
        <div className="title">{title}</div>
        {!compact && formattedTime && <div className="time">{formattedTime}</div>}
      </div>
    );
  },
  // Custom comparison function
  (prevProps, nextProps) => {
    return (
      prevProps.event.id === nextProps.event.id &&
      prevProps.compact === nextProps.compact &&
      prevProps.showTime === nextProps.showTime &&
      prevProps.maxTitleLength === nextProps.maxTitleLength
    );
  }
);

EventItem.displayName = 'EventItem';
