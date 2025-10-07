// src/components/calendar/EventItem.tsx
import React from "react";
import {CalendarEvent} from "../../types/calendarEvent";

interface EventItemProps {
  event: CalendarEvent;
  onClick?: () => void;
  compact?: boolean;
  showTime?: boolean;
  maxTitleLength?: number;
}

export const EventItem: React.FC<EventItemProps> = ({
  event,
  onClick,
  compact = false,
  showTime = true,
  maxTitleLength
}) => {
  const title = maxTitleLength && event.title.length > maxTitleLength
    ? event.title.substring(0, maxTitleLength) + "..."
    : event.title;

  return (
    <div
      className={compact ? "compact-event" : "event-card"}
      style={{ background: event.color || "var(--primary-500)" }}
      onClick={onClick}
    >
      <div className="title">{title}</div>
      {!compact && showTime && !event.all_day && (
        <div className="time">{new Date(event.start_time).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true })}</div>
      )}
    </div>
  );
};
