import { FC } from "react";
import { DarkModeToggle } from "../global/DarkModeToggle";

interface CalendarHeaderProps {
  currentView: "day" | "week" | "month";
  onChangeView: (view: "day" | "week" | "month") => void;
}

export const CalendarHeader: FC<CalendarHeaderProps> = ({ currentView, onChangeView }) => {
  return (
    <div className="header">
      <h1>Calendar</h1>
      <div className="header-controls">
        <div className="view-controls">
          {["day", "week", "month"].map(view => (
            <button
              key={view}
              className={`view-btn ${currentView === view ? "active" : ""}`}
              onClick={() => onChangeView(view as any)}
            >
              {view.charAt(0).toUpperCase() + view.slice(1)}
            </button>
          ))}
        </div>
        <DarkModeToggle />
      </div>
    </div>
  );
};
