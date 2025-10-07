// Optimized version of TaskItem with React.memo
import React, { memo, useCallback } from 'react';

interface TaskItemProps {
  id: string;
  name: string;
  task: string;
  completed: boolean;
  onToggle: (id: string, completed: boolean) => void;
}

/**
 * Memoized TaskItem component
 * Prevents re-renders when parent updates other tasks
 */
export const TaskItem: React.FC<TaskItemProps> = memo(
  ({ id, name, task, completed, onToggle }) => {
    // Memoize the toggle handler
    const handleToggle = useCallback(() => {
      onToggle(id, !completed);
    }, [id, completed, onToggle]);

    return (
      <div className={`task-item ${completed ? 'completed' : ''}`}>
        <input
          type="checkbox"
          checked={completed}
          onChange={handleToggle}
          aria-label={`Mark ${task} as ${completed ? 'incomplete' : 'complete'}`}
        />
        <div className="task-content">
          <span className="task-name">{name}</span>
          <span className="task-description">{task}</span>
        </div>
      </div>
    );
  },
  // Only re-render if these props change
  (prevProps, nextProps) => {
    return (
      prevProps.id === nextProps.id &&
      prevProps.completed === nextProps.completed &&
      prevProps.task === nextProps.task &&
      prevProps.name === nextProps.name
    );
  }
);

TaskItem.displayName = 'TaskItem';
