// src/components/calendar/DayView.tsx
import React from "react";
import {CalendarEvent} from "../../types/calendarEvent";
import { EventList } from "./EventList";

interface DayViewProps {
  date: Date;
  events: CalendarEvent[];
  goToDate?: (year: number, month: number, day: number) => void;
  formatTime: (dateStr: string) => string;
}

export const DayView: React.FC<DayViewProps> = ({ date, events, goToDate, formatTime }) => {
  const dayName = date.toLocaleDateString("en-US", { weekday: "long" });
  const monthYear = date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
  const dayNum = date.getDate();

  return (
    <div className="day-view">
      <div className="day-header">
        <div className="day-circle">{dayNum}</div>
        <div className="day-info">
          <h2>{dayName}</h2>
          <p>{monthYear}</p>
        </div>
      </div>
      <EventList events={events} onItemClick={(e) => goToDate?.(date.getFullYear(), date.getMonth(), date.getDate())} />
    </div>
  );
};
