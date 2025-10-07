// src/components/calendar/MonthView.tsx
import React from "react";

import { EventList } from "./EventList";
import {CalendarEvent} from "../../types/calendarEvent";

interface MonthViewProps {
  year: number;
  month: number;
  events: CalendarEvent[];
  isSameDay: (d1: Date, d2: Date) => boolean;
  goToDate: (year: number, month: number, day: number) => void;
}

export const MonthView: React.FC<MonthViewProps> = ({ year, month, events, isSameDay, goToDate }) => {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startingDayOfWeek = firstDay.getDay();
  const today = new Date();

  const cells = [];
  const dayHeaders = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  dayHeaders.forEach(day => cells.push(<div key={`header-${day}`} className="weekday-header">{day}</div>));

  for (let i = 0; i < startingDayOfWeek; i++) cells.push(<div key={`empty-${i}`} className="month-cell"></div>);

  for (let day = 1; day <= lastDay.getDate(); day++) {
    const cellDate = new Date(year, month, day);
    const dayEvents = events.filter(e => isSameDay(new Date(e.start_time), cellDate));
    const isToday = isSameDay(cellDate, today);

    cells.push(
      <div key={day} className={`month-cell ${isToday ? "today" : ""}`} onClick={() => goToDate(year, month, day)}>
        <div className="month-date"><span className={`date-number ${isToday ? "today" : ""}`}>{day}</span></div>
        <EventList events={dayEvents.slice(0, 3)} compact maxTitleLength={25} />
        {dayEvents.length > 3 && <div className="more-events">+{dayEvents.length - 3} more</div>}
      </div>
    );
  }

  return <div className="month-view"><div className="month-grid">{cells}</div></div>;
};
