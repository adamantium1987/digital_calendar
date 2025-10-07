// src/components/calendar/WeekView.tsx
import React from "react";
import {CalendarEvent} from "../../types/calendarEvent";
import { EventList } from "./EventList";

interface WeekViewProps {
  startDate: Date;
  events: CalendarEvent[];
  isSameDay: (d1: Date, d2: Date) => boolean;
  goToDate: (year: number, month: number, day: number) => void;
  formatTime: (dateStr: string) => string;
}

export const WeekView: React.FC<WeekViewProps> = ({ startDate, events, isSameDay, goToDate }) => {
  const monday = new Date(startDate);
  const day = monday.getDay();
  const diff = monday.getDate() - day + (day === 0 ? -6 : 1);
  monday.setDate(diff);

  const today = new Date();
  const dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const days = [];

  for (let i = 0; i < 7; i++) {
    const date = new Date(monday);
    date.setDate(date.getDate() + i);
    const dayEvents = events.filter(e => isSameDay(new Date(e.start_time), date));
    const isToday = isSameDay(date, today);

    days.push(
      <div key={i} className={`day-column ${isToday ? "today" : ""}`}>
        <div className="day-header">
          <div className="day-name">{dayNames[i]}</div>
          <div className={`day-number ${isToday ? "today" : ""}`}>{date.getDate()}</div>
        </div>
        <EventList events={dayEvents} compact onItemClick={() => goToDate(date.getFullYear(), date.getMonth(), date.getDate())} maxTitleLength={20} />
      </div>
    );
  }

  return <div className="week-view"><div className="week-grid">{days}</div></div>;
};
