// src/components/TaskDateNav.tsx
import { FC } from "react";
import ProgressBar from "../global/ProgressBar";


export interface TaskDateNavProps {
  currentDate: Date;
  completedTasks: number;
  totalTasks: number;
  onPrev: () => void;
  onNext: () => void;
  onGoToToday?: () => void;
  /**
   * Format the display date (e.g. "Tue, Jul 1")
   * Default: uses toLocaleDateString with medium options.
   */
  formatDate?: (d: Date) => string;
  /**
   * Format the display time string (e.g. "10:32 AM")
   * Default: uses current time in locale format.
   */
  formatTime?: () => string;
  /**
   * Return true if the provided date is "today".
   * Default: compares year/month/date against today.
   */
  isToday?: (d: Date) => boolean;
  className?: string;
}

export const TaskDateNav: FC<TaskDateNavProps> = ({
  currentDate,
  completedTasks,
  totalTasks,
  onPrev,
  onNext,
  onGoToToday,
  formatDate,
  formatTime,
  isToday,
  className,
}) => {
  // defaults
  const _formatDate = formatDate ?? ((d: Date) =>
    d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })
  );

  const _formatTime = formatTime ?? (() =>
    new Date().toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })
  );

  const _isToday = isToday ?? ((d: Date) => {
    const today = new Date();
    return (
      d.getFullYear() === today.getFullYear() &&
      d.getMonth() === today.getMonth() &&
      d.getDate() === today.getDate()
    );
  });

  return (
    <div className={`card card-compact ${className ?? ""}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onPrev}
            className="btn btn-secondary btn-sm"
            aria-label="Previous day"
            type="button"
          >
            ←
          </button>

          <div>
            <div className="flex items-center gap-2">
              <h3 className="mb-0">{_formatDate(currentDate)} Tasks</h3>
              {_isToday(currentDate) && <span className="status status-success">TODAY</span>}
            </div>

            <p className="text-sm mb-0">
              {_formatTime()} • {completedTasks} of {totalTasks} tasks completed
            </p>
          </div>

          <button
            onClick={onNext}
            className="btn btn-secondary btn-sm"
            aria-label="Next day"
            type="button"
          >
            →
          </button>
        </div>

        <ProgressBar
          completed={completedTasks}
          total={totalTasks}
          width="100px"
          height="8px"
        />

        {!_isToday(currentDate) && onGoToToday && (
          <button
            onClick={onGoToToday}
            className="btn btn-secondary btn-sm"
            aria-label="Go to today"
            type="button"
          >
            Go to Today
          </button>
        )}
      </div>
    </div>
  );
};

export default TaskDateNav;
