import React, { FC } from "react";

interface CalendarNavProps {
  periodText: string;
  onPrev: () => void;
  onNext: () => void;
  onToday: () => void;
}

export const CalendarNav: FC<CalendarNavProps> = ({ periodText, onPrev, onNext, onToday }) => {
  return (
    <div className="nav-controls">
      <button className="nav-btn" onClick={onPrev}>← Prev</button>
      <span className="current-period">{periodText}</span>
      <button className="nav-btn" onClick={onNext}>Next →</button>
      <button className="nav-btn" onClick={onToday}>Today</button>
    </div>
  );
};
