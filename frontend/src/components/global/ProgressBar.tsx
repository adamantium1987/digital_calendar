// src/components/ProgressBar.tsx
import React, { FC, useMemo } from "react";

export interface ProgressBarProps {
  completed: number;
  total: number;
  /**
   * Visual width of the progress bar container (CSS value).
   * Default: '100px'
   */
  width?: string;
  /**
   * Visual height of the progress bar (CSS value).
   * Default: '8px'
   */
  height?: string;
  /**
   * Whether to show numeric percent label next to the bar.
   * Default: true
   */
  showPercent?: boolean;
  /**
   * CSS class to apply to the outer container.
   */
  className?: string;
}

/**
 * Small reusable progress bar with percentage calculation.
 */
export const ProgressBar: FC<ProgressBarProps> = ({
  completed,
  total,
  width = "100px",
  height = "8px",
  showPercent = true,
  className = "",
}) => {
  const percent = useMemo<number>(() => {
    if (total <= 0) return 0;
    return Math.round((completed / total) * 100);
  }, [completed, total]);

  const progressWidth = useMemo<string>(() => {
    return `${total > 0 ? (completed / total) * 100 : 0}%`;
  }, [completed, total]);

  const percentColor = percent === 100 ? "var(--success-600)" : "var(--text-secondary)";

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div
        style={{
          width,
          height,
          backgroundColor: "var(--border-color)",
          borderRadius: "var(--radius-sm)",
          overflow: "hidden",
        }}
        aria-hidden
      >
        <div
          style={{
            width: progressWidth,
            height: "100%",
            backgroundColor: "var(--primary-500)",
            transition: "width var(--transition)",
          }}
        />
      </div>

      {showPercent && (
        <div
          className="text-sm"
          style={{
            fontWeight: 600,
            color: percentColor,
            minWidth: 36,
            textAlign: "right",
          }}
          aria-live="polite"
        >
          {percent}%
        </div>
      )}
    </div>
  );
};

export default ProgressBar;
