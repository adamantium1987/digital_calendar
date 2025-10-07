// src/components/calendar/NoEventsMessage.tsx
import React from "react";

interface NoEventsMessageProps {
  message?: string;
  compact?: boolean;
}

export const NoEventsMessage: React.FC<NoEventsMessageProps> = ({
  message,
  compact = false
}) => {
  return (
    <div className={compact ? "no-events-compact" : "no-events"}>
      {message || (compact ? "No events" : "No events scheduled")}
    </div>
  );
};
