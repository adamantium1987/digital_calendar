import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react';
import styles from './CalendarView.module.css';

export type ViewType = 'day' | 'week' | 'month';

interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  color?: string;
  all_day?: boolean;
}

interface CalendarViewProps {
  view: ViewType;
  currentDate: Date;
  events: CalendarEvent[];
  onDateChange: (date: Date) => void;
  onViewChange: (view: ViewType) => void;
  onEventClick?: (event: CalendarEvent) => void;
}

export const CalendarView: React.FC<CalendarViewProps> = ({
  view,
  currentDate,
  events,
  onDateChange,
  onViewChange,
  onEventClick,
}) => {
  const [direction, setDirection] = useState<'left' | 'right'>('right');

  const handlePrevious = () => {
    setDirection('left');
    const newDate = new Date(currentDate);
    if (view === 'day') {
      newDate.setDate(newDate.getDate() - 1);
    } else if (view === 'week') {
      newDate.setDate(newDate.getDate() - 7);
    } else {
      newDate.setMonth(newDate.getMonth() - 1);
    }
    onDateChange(newDate);
  };

  const handleNext = () => {
    setDirection('right');
    const newDate = new Date(currentDate);
    if (view === 'day') {
      newDate.setDate(newDate.getDate() + 1);
    } else if (view === 'week') {
      newDate.setDate(newDate.getDate() + 7);
    } else {
      newDate.setMonth(newDate.getMonth() + 1);
    }
    onDateChange(newDate);
  };

  const handleToday = () => {
    onDateChange(new Date());
  };

  const getHeaderText = () => {
    const options: Intl.DateTimeFormatOptions =
      view === 'day'
        ? { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
        : view === 'week'
        ? { year: 'numeric', month: 'long' }
        : { year: 'numeric', month: 'long' };
    return currentDate.toLocaleDateString('en-US', options);
  };

  const slideVariants = {
    enter: (direction: 'left' | 'right') => ({
      x: direction === 'right' ? 100 : -100,
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (direction: 'left' | 'right') => ({
      x: direction === 'right' ? -100 : 100,
      opacity: 0,
    }),
  };

  return (
    <div className={styles.calendarView}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <motion.button
            className={styles.todayButton}
            onClick={handleToday}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <CalendarIcon size={18} />
            Today
          </motion.button>
          <div className={styles.navigation}>
            <motion.button
              className={styles.navButton}
              onClick={handlePrevious}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <ChevronLeft size={20} />
            </motion.button>
            <motion.button
              className={styles.navButton}
              onClick={handleNext}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <ChevronRight size={20} />
            </motion.button>
          </div>
          <h2 className={styles.headerTitle}>{getHeaderText()}</h2>
        </div>

        {/* View Switcher */}
        <div className={styles.viewSwitcher}>
          {(['day', 'week', 'month'] as ViewType[]).map((viewType) => (
            <motion.button
              key={viewType}
              className={`${styles.viewButton} ${
                view === viewType ? styles.viewButtonActive : ''
              }`}
              onClick={() => onViewChange(viewType)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {viewType.charAt(0).toUpperCase() + viewType.slice(1)}
            </motion.button>
          ))}
        </div>
      </div>

      {/* Calendar Content */}
      <AnimatePresence mode="wait" custom={direction}>
        <motion.div
          key={`${view}-${currentDate.toISOString()}`}
          custom={direction}
          variants={slideVariants}
          initial="enter"
          animate="center"
          exit="exit"
          transition={{ duration: 0.3 }}
          className={styles.calendarContent}
        >
          {view === 'day' && (
            <DayView
              date={currentDate}
              events={events}
              onEventClick={onEventClick}
            />
          )}
          {view === 'week' && (
            <WeekView
              date={currentDate}
              events={events}
              onEventClick={onEventClick}
            />
          )}
          {view === 'month' && (
            <MonthView
              date={currentDate}
              events={events}
              onEventClick={onEventClick}
            />
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

// Day View Component
const DayView: React.FC<{
  date: Date;
  events: CalendarEvent[];
  onEventClick?: (event: CalendarEvent) => void;
}> = ({ date, events, onEventClick }) => {
  const hours = Array.from({ length: 24 }, (_, i) => i);

  const dayEvents = events.filter((event) => {
    const eventDate = new Date(event.start);
    return eventDate.toDateString() === date.toDateString();
  });

  return (
    <div className={styles.dayView}>
      <div className={styles.timeColumn}>
        {hours.map((hour) => (
          <div key={hour} className={styles.hourSlot}>
            <span className={styles.hourLabel}>
              {hour === 0 ? '12 AM' : hour < 12 ? `${hour} AM` : hour === 12 ? '12 PM' : `${hour - 12} PM`}
            </span>
          </div>
        ))}
      </div>
      <div className={styles.eventsColumn}>
        {dayEvents.map((event) => (
          <motion.div
            key={event.id}
            className={styles.dayEvent}
            style={{ backgroundColor: event.color || '#2196f3' }}
            onClick={() => onEventClick?.(event)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className={styles.eventTime}>
              {new Date(event.start).toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
              })}
            </div>
            <div className={styles.eventTitle}>{event.title}</div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

// Week View Component
const WeekView: React.FC<{
  date: Date;
  events: CalendarEvent[];
  onEventClick?: (event: CalendarEvent) => void;
}> = ({ date, events, onEventClick }) => {
  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const day = new Date(date);
    day.setDate(date.getDate() - date.getDay() + i);
    return day;
  });

  return (
    <div className={styles.weekView}>
      <div className={styles.weekHeader}>
        {weekDays.map((day) => (
          <div key={day.toISOString()} className={styles.weekDay}>
            <div className={styles.weekDayName}>
              {day.toLocaleDateString('en-US', { weekday: 'short' })}
            </div>
            <div className={styles.weekDayDate}>{day.getDate()}</div>
          </div>
        ))}
      </div>
      <div className={styles.weekGrid}>
        {weekDays.map((day) => {
          const dayEvents = events.filter((event) => {
            const eventDate = new Date(event.start);
            return eventDate.toDateString() === day.toDateString();
          });

          return (
            <div key={day.toISOString()} className={styles.weekColumn}>
              {dayEvents.map((event) => (
                <motion.div
                  key={event.id}
                  className={styles.weekEvent}
                  style={{ backgroundColor: event.color || '#2196f3' }}
                  onClick={() => onEventClick?.(event)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className={styles.eventTitle}>{event.title}</div>
                  <div className={styles.eventTime}>
                    {new Date(event.start).toLocaleTimeString('en-US', {
                      hour: 'numeric',
                      minute: '2-digit',
                    })}
                  </div>
                </motion.div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Month View Component
const MonthView: React.FC<{
  date: Date;
  events: CalendarEvent[];
  onEventClick?: (event: CalendarEvent) => void;
}> = ({ date, events, onEventClick }) => {
  const firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
  const lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
  const daysInMonth = lastDay.getDate();
  const startDay = firstDay.getDay();

  const days = Array.from({ length: 42 }, (_, i) => {
    const dayNumber = i - startDay + 1;
    if (dayNumber < 1 || dayNumber > daysInMonth) return null;
    const day = new Date(date.getFullYear(), date.getMonth(), dayNumber);
    return day;
  });

  return (
    <div className={styles.monthView}>
      <div className={styles.monthHeader}>
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
          <div key={day} className={styles.monthHeaderDay}>
            {day}
          </div>
        ))}
      </div>
      <div className={styles.monthGrid}>
        {days.map((day, index) => {
          if (!day) {
            return <div key={`empty-${index}`} className={styles.emptyDay} />;
          }

          const dayEvents = events.filter((event) => {
            const eventDate = new Date(event.start);
            return eventDate.toDateString() === day.toDateString();
          });

          const isToday = day.toDateString() === new Date().toDateString();

          return (
            <motion.div
              key={day.toISOString()}
              className={`${styles.monthDay} ${isToday ? styles.today : ''}`}
              whileHover={{ scale: 1.02 }}
            >
              <div className={styles.monthDayNumber}>{day.getDate()}</div>
              <div className={styles.monthDayEvents}>
                {dayEvents.slice(0, 3).map((event) => (
                  <motion.div
                    key={event.id}
                    className={styles.monthEvent}
                    style={{ backgroundColor: event.color || '#2196f3' }}
                    onClick={() => onEventClick?.(event)}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {event.title}
                  </motion.div>
                ))}
                {dayEvents.length > 3 && (
                  <div className={styles.moreEvents}>
                    +{dayEvents.length - 3} more
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default CalendarView;
