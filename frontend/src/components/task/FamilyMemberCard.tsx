// src/components/FamilyMemberCard.tsx
import React from "react";
import TaskItem from "./TaskItem";
import {TaskDayRecord, DayName, MemberColors} from "../../types/tasks";
import ProgressBar from "../global/ProgressBar";

export interface FamilyMemberCardProps {
  name: string;
  tasks: TaskDayRecord[];
  colors: MemberColors;
  onToggle: (task_id: number, day: DayName, checked: boolean) => void;
}

const FamilyMemberCard: React.FC<FamilyMemberCardProps> = ({ name, tasks, colors, onToggle }) => {
  // Split tasks by type
  const choreTasks = React.useMemo(() => tasks.filter(t => t.type === 'chore'), [tasks]);
  const hygieneTasks = React.useMemo(() => tasks.filter(t => t.type === 'hygiene'), [tasks]);

  const completedTasksCount = React.useMemo(() => tasks.filter(c => c.completed).length, [tasks]);
  const totalTaskCount = tasks.length;

  const isParents = name === "Parents";

  return (
    <div className="card">
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 'var(--space-4)',
        paddingBottom: 'var(--space-3)',
        borderBottom: `2px solid ${colors.border}`
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            backgroundColor: colors.border,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 600,
            fontSize: '1rem'
          }}>
            {name.charAt(0)}
          </div>

          <div>
            <h3 className="mb-0" style={{ color: colors.text }}>{name}</h3>
            <p className="text-sm mb-0">
              {completedTasksCount} of {totalTaskCount} completed
            </p>
          </div>
        </div>

        <ProgressBar
          completed={completedTasksCount}
          total={totalTaskCount}
          width="100px"
          height="8px"
        />
      </div>

      {/* Chores Section */}
      {choreTasks.length > 0 && (
        <div style={{ marginBottom: isParents ? 0 : 'var(--space-4)' }}>
          <h4 style={{
            fontSize: '0.875rem',
            fontWeight: 600,
            marginBottom: 'var(--space-2)',
            color: 'var(--text-secondary)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            Chores
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {choreTasks.map(task => (
              <TaskItem
                key={`${task.task_id}-${task.day_name}`}
                task_id={task.task_id}
                task={task.task}
                day_name={task.day_name}
                completed={task.completed}
                onToggle={onToggle}
                bg={colors.bg}
                border={colors.border}
                textColor={colors.text}
              />
            ))}
          </div>
        </div>
      )}

      {/* Hygiene Section - Only show if NOT Parents */}
      {!isParents && hygieneTasks.length > 0 && (
        <div>
          <h4 style={{
            fontSize: '0.875rem',
            fontWeight: 600,
            marginBottom: 'var(--space-2)',
            color: 'var(--text-secondary)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            Hygiene
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {hygieneTasks.map(task => (
              <TaskItem
                key={`${task.task_id}-${task.day_name}`}
                task_id={task.task_id}
                task={task.task}
                day_name={task.day_name}
                completed={task.completed}
                onToggle={onToggle}
                bg={colors.bg}
                border={colors.border}
                textColor={colors.text}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default React.memo(FamilyMemberCard);