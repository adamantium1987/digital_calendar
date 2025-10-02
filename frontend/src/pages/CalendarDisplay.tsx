import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import { EventCard } from '../components/EventCard';
import { DarkModeToggle } from '../components/DarkModeToggle';
import { CalendarEvent, ViewType } from '../types';

export const CalendarDisplay: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewType>('month');
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
        view: currentView  // Add this line
      });

      console.log('Loading events with params:', params.toString()); // Add this debug
      const response = await api.get<any>(`/events?${params}`);

      console.log('API response:', response);
      console.log('Events array:', response.events);
      console.log('Number of events:', response.events.length);
      console.log('Sample event:', response.events[0]);

      console.log('All events being processed:', events);
      events.forEach((event, index) => {
        console.log(`Event ${index}:`, {
          title: event.title,
          start: event.start_time,
          date: new Date(event.start_time)
        });
      });

      setEvents(response.events || []);
      setLoading(false);
    } catch (error) {
      console.error('Error loading events:', error);
      setLoading(false);
    }
  };

  const navigateDate = (direction: number) => {
    const newDate = new Date(currentDate);
    if (currentView === 'day') {
      newDate.setDate(newDate.getDate() + direction);
    } else if (currentView === 'week') {
      newDate.setDate(newDate.getDate() + (direction * 7));
    } else if (currentView === 'month') {
      newDate.setMonth(newDate.getMonth() + direction);
    }
    setCurrentDate(newDate);
  };

  const goToToday = () => setCurrentDate(new Date());

  const goToDate = (year: number, month: number, day: number) => {
    setCurrentDate(new Date(year, month, day));
    setCurrentView('day');
  };

  const formatTime = (dateStr: string): string => {
    return new Date(dateStr).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const isSameDay = (date1: Date, date2: Date): boolean => {
    return date1.getFullYear() === date2.getFullYear() &&
           date1.getMonth() === date2.getMonth() &&
           date1.getDate() === date2.getDate();
  };

  const getEventsForDate = (date: Date): CalendarEvent[] => {
    return events.filter(e => isSameDay(new Date(e.start_time), date));
  };

  const getPeriodText = (): string => {
    if (currentView === 'day') {
      return currentDate.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      });
    } else if (currentView === 'week') {
      const monday = new Date(currentDate);
      const day = monday.getDay();
      const diff = monday.getDate() - day + (day === 0 ? -6 : 1);
      monday.setDate(diff);
      const sunday = new Date(monday);
      sunday.setDate(sunday.getDate() + 6);

      const startMonth = monday.toLocaleDateString('en-US', { month: 'long' });
      const endMonth = sunday.toLocaleDateString('en-US', { month: 'long' });
      const year = sunday.getFullYear();

      if (startMonth === endMonth) {
        return `${startMonth} ${monday.getDate()}-${sunday.getDate()}, ${year}`;
      }
      return `${startMonth} ${monday.getDate()} - ${endMonth} ${sunday.getDate()}, ${year}`;
    } else {
      return currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    }
  };

  const renderDayView = () => {
    const dayEvents = getEventsForDate(currentDate);
    const dayName = currentDate.toLocaleDateString('en-US', { weekday: 'long' });
    const dayNum = currentDate.getDate();
    const monthYear = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

    return (
      <div className="day-view">
        <div className="day-header">
          <div className="day-circle">{dayNum}</div>
          <div className="day-info">
            <h2>{dayName}</h2>
            <p>{monthYear}</p>
          </div>
        </div>
        {dayEvents.length === 0 ? (
          <div className="no-events">No events scheduled for this day</div>
        ) : (
          dayEvents.map(event => <EventCard key={event.id} event={event} />)
        )}
      </div>
    );
  };

  const renderWeekView = () => {
    const monday = new Date(currentDate);
    const day = monday.getDay();
    const diff = monday.getDate() - day + (day === 0 ? -6 : 1);
    monday.setDate(diff);

    const today = new Date();
    const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const days = [];

    for (let i = 0; i < 7; i++) {
      const date = new Date(monday);
      date.setDate(date.getDate() + i);
      const isToday = isSameDay(date, today);
      const dayEvents = getEventsForDate(date);

      days.push(
        <div key={i} className={`day-column ${isToday ? 'today' : ''}`}>
          <div className="day-header">
            <div className="day-name">{dayNames[i]}</div>
            <div className={`day-number ${isToday ? 'today' : ''}`}>{date.getDate()}</div>
          </div>
          {dayEvents.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '2rem 0.5rem',
              color: 'var(--text-muted)',
              fontSize: '0.75rem'
            }}>
              No events
            </div>
          ) : (
            dayEvents.map(event => (
              <div
                key={event.id}
                className="compact-event"
                style={{ background: event.color || 'var(--primary-500)' }}
                onClick={() => goToDate(date.getFullYear(), date.getMonth(), date.getDate())}
              >
                <div className="title">
                  {event.title.substring(0, 20)}{event.title.length > 20 ? '...' : ''}
                </div>
                {!event.all_day && <div className="time">{formatTime(event.start_time)}</div>}
              </div>
            ))
          )}
        </div>
      );
    }

    return (
      <div className="week-view">
        <div className="week-grid">{days}</div>
      </div>
    );
  };

  const renderMonthView = () => {
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startingDayOfWeek = firstDay.getDay(); // Remove the adjustment - use raw getDay()
  const today = new Date();

  const cells = [];
  const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']; // Sunday first

  dayHeaders.forEach(day => {
    cells.push(<div key={`header-${day}`} className="weekday-header">{day}</div>);
  });

  // Add empty cells for days before the first day of the month
  for (let i = 0; i < startingDayOfWeek; i++) {
    cells.push(<div key={`empty-${i}`} className="month-cell"></div>);
  }

  // Add cells for each day of the month
  for (let day = 1; day <= lastDay.getDate(); day++) {
    const cellDate = new Date(year, month, day);
    const isToday = isSameDay(cellDate, today);
    const dayEvents = getEventsForDate(cellDate);

    cells.push(
      <div
        key={day}
        className={`month-cell ${isToday ? 'today' : ''}`}
        onClick={() => goToDate(year, month, day)}
      >
        <div className="month-date">
          <span className={`date-number ${isToday ? 'today' : ''}`}>{day}</span>
        </div>
        {dayEvents.slice(0, 3).map((event, idx) => (
          <div
            key={idx}
            className="month-event"
            style={{ background: event.color || 'var(--primary-500)' }}
          >
            {event.title.length > 25 ? event.title.substring(0, 25) + '...' : event.title}
          </div>
        ))}
        {dayEvents.length > 3 && (
          <div className="more-events">+{dayEvents.length - 3} more</div>
        )}
      </div>
    );
  }

  return (
    <div className="month-view">
      <div className="month-grid">{cells}</div>
    </div>
  );
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
      <div className="header">
        <h1>Calendar</h1>
        <div className="header-controls">
          <div className="view-controls">
            <button
              className={`view-btn ${currentView === 'day' ? 'active' : ''}`}
              onClick={() => setCurrentView('day')}
            >
              Day
            </button>
            <button
              className={`view-btn ${currentView === 'week' ? 'active' : ''}`}
              onClick={() => setCurrentView('week')}
            >
              Week
            </button>
            <button
              className={`view-btn ${currentView === 'month' ? 'active' : ''}`}
              onClick={() => setCurrentView('month')}
            >
              Month
            </button>
          </div>
          <DarkModeToggle />
        </div>
      </div>

      <div className="nav-controls">
        <button className="nav-btn" onClick={() => navigateDate(-1)}>← Prev</button>
        <span className="current-period">{getPeriodText()}</span>
        <button className="nav-btn" onClick={() => navigateDate(1)}>Next →</button>
        <button className="nav-btn" onClick={goToToday}>Today</button>
      </div>

      <div id="calendarContent">
        {currentView === 'day' && renderDayView()}
        {currentView === 'week' && renderWeekView()}
        {currentView === 'month' && renderMonthView()}
      </div>
    </div>
  );
};