// src/components/calendar/EventList.tsx
import React from "react";
import {CalendarEvent} from "../../types/calendarEvent";
import { EventItem } from "./EventItem";
import { NoEventsMessage } from "./NoEventsMessage";

interface EventListProps {
  events: CalendarEvent[];
  onItemClick?: (event: CalendarEvent) => void;
  compact?: boolean;
  maxTitleLength?: number;
}

export const EventList: React.FC<EventListProps> = ({
  events,
  onItemClick,
  compact = false,
  maxTitleLength
}) => {
  if (events.length === 0) {
    return <NoEventsMessage compact={compact} />;
  }

  return (
    <>
      {events.map(event => (
        <EventItem
          key={event.id}
          event={event}
          compact={compact}
          maxTitleLength={maxTitleLength}
          onClick={() => onItemClick?.(event)}
        />
      ))}
    </>
  );
};
