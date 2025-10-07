// src/components/HygieneItem.tsx
import React from "react";
import {DayName} from "../../types/tasks";

export interface HygieneItemProps {
  hygiene_id: number;
  task: string;
  day_name: DayName;
  completed: boolean;
  onToggle: (task_id: number, day: DayName, checked: boolean) => void;
  bg: string;
  border: string;
  textColor: string;
  onEdit?: (task_id: number, newTask: string) => void; // optional
}

const HygieneItem: React.FC<HygieneItemProps> = ({
  hygiene_id, task, day_name, completed, onToggle, bg, border, textColor, onEdit
}) => {
  const handleEdit = () => {
    if (!onEdit) return;
    const newTask = prompt("Edit Hygiene Item:", task);
    if (newTask && newTask !== task) {
      onEdit(hygiene_id, newTask);
    }
  };

  return (
    <div
      onClick={() => onToggle(hygiene_id, day_name, !completed)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-3)',
        padding: 'var(--space-3)',
        backgroundColor: completed ? bg : 'var(--bg-tertiary)',
        borderRadius: 'var(--radius-lg)',
        cursor: 'pointer',
        border: `1px solid ${completed ? border : 'var(--border-color)'}`,
        transition: 'var(--transition)',
        opacity: completed ? 0.8 : 1
      }}
    >
      <div style={{
        width: '20px',
        height: '20px',
        borderRadius: '50%',
        backgroundColor: completed ? border : 'transparent',
        border: completed ? 'none' : '2px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0
      }}>
        {completed && <span style={{ color: 'white', fontSize: '0.75rem', fontWeight: 'bold' }}>✓</span>}
      </div>

      <div style={{ flex: 1 }}>
        <div
          style={{
            fontSize: '0.875rem',
            fontWeight: 500,
            color: completed ? textColor : 'var(--text-primary)',
            textDecoration: completed ? 'line-through' : 'none'
          }}
        >
          {task}
        </div>
      </div>

      {onEdit && (
        <button
          onClick={(e) => { e.stopPropagation(); handleEdit(); }}
          style={{ fontSize: '0.75rem', border: 'none', background: 'none', cursor: 'pointer' }}
          aria-label="Edit task"
        >
          ✎
        </button>
      )}
    </div>
  );
};

export default React.memo(HygieneItem);
