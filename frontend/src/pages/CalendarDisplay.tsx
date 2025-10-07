// src/components/calendar/CalendarDisplay.tsx
import React, { useState, useEffect } from "react";
import {CalendarHeader} from "../components/calendar/CalendarHeader";
import {CalendarNav} from "../components/calendar/CalendarNav";
import {DayView} from "../components/calendar/DayView";
import {WeekView} from "../components/calendar/WeekView";
import {MonthView} from "../components/calendar/MonthView";
import {api} from "../utils/api";
import {CalendarEvent} from "../types/calendarEvent";
import {ViewType} from "../types/viewType";
import {useSwipeNavigation} from "../hooks/useSwipeNavigation";

interface CalendarProps {
  navigate: (path: string) => void;
}

export const CalendarDisplay: React.FC<CalendarProps> = ({ navigate }) => {
  useSwipeNavigation({
    onSwipeLeft: () => navigate('/tasks'), // Swipe left goes to Calendar
    onSwipeRight: () => {}, // Already at first page, do nothing
    minSwipeDistance: 75
  });
  const [currentView, setCurrentView] = useState<ViewType>("month");
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadEvents();
    const interval = setInterval(loadEvents, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const loadEvents = async () => {
    try {
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - 60);
      const endDate = new Date();
      endDate.setDate(endDate.getDate() + 120);

      const params = new URLSearchParams({
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        view: currentView
      });

      const response = await api.get<any>(`/events?${params}`);
      setEvents(response.events || []);
      setLoading(false);
    } catch (error) {
      console.error("Error loading events:", error);
      setLoading(false);
    }
  };

  const navigateDate = (direction: number) => {
    const newDate = new Date(currentDate);
    if (currentView === "day") newDate.setDate(newDate.getDate() + direction);
    else if (currentView === "week") newDate.setDate(newDate.getDate() + direction * 7);
    else if (currentView === "month") newDate.setMonth(newDate.getMonth() + direction);
    setCurrentDate(newDate);
  };

  const goToToday = () => setCurrentDate(new Date());

  const goToDate = (year: number, month: number, day: number) => {
    setCurrentDate(new Date(year, month, day));
    setCurrentView("day");
  };

  const formatTime = (dateStr: string) =>
    new Date(dateStr).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });

  const isSameDay = (d1: Date, d2: Date) =>
    d1.getFullYear() === d2.getFullYear() &&
    d1.getMonth() === d2.getMonth() &&
    d1.getDate() === d2.getDate();

  const getEventsForDate = (date: Date) => events.filter(e => isSameDay(new Date(e.start_time), date));

  const getPeriodText = () => {
    if (currentView === "day") {
      return currentDate.toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric"
      });
    } else if (currentView === "week") {
      const monday = new Date(currentDate);
      const day = monday.getDay();
      const diff = monday.getDate() - day + (day === 0 ? -6 : 1);
      monday.setDate(diff);
      const sunday = new Date(monday);
      sunday.setDate(sunday.getDate() + 6);

      const startMonth = monday.toLocaleDateString("en-US", { month: "long" });
      const endMonth = sunday.toLocaleDateString("en-US", { month: "long" });
      const year = sunday.getFullYear();

      if (startMonth === endMonth) return `${startMonth} ${monday.getDate()}-${sunday.getDate()}, ${year}`;
      return `${startMonth} ${monday.getDate()} - ${endMonth} ${sunday.getDate()}, ${year}`;
    } else {
      return currentDate.toLocaleDateString("en-US", { month: "long", year: "numeric" });
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading">Loading events...</div>
      </div>
    );
  }

  return (
    <div className="container">
      {/* Header + View Toggle */}
      <CalendarHeader currentView={currentView} onChangeView={setCurrentView} />

      {/* Navigation Controls */}
      <CalendarNav
        periodText={getPeriodText()}
        onPrev={() => navigateDate(-1)}
        onNext={() => navigateDate(1)}
        onToday={goToToday}
      />

      {/* Render the correct view */}
      <div id="calendarContent">
        {currentView === "day" && (
          <DayView
            date={currentDate}
            events={getEventsForDate(currentDate)}
            goToDate={goToDate}
            formatTime={formatTime}
          />
        )}
        {currentView === "week" && (
          <WeekView
            startDate={currentDate}
            events={events}
            isSameDay={isSameDay}
            goToDate={goToDate}
            formatTime={formatTime}
          />
        )}
        {currentView === "month" && (
          <MonthView
            year={currentDate.getFullYear()}
            month={currentDate.getMonth()}
            events={events}
            isSameDay={isSameDay}
            goToDate={goToDate}
          />
        )}
      </div>
    </div>
  );
};

export default CalendarDisplay;
