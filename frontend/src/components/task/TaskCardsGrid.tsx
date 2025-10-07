// src/components/TaskCardsGrid.tsx
import React, { FC } from "react";
import FamilyMemberCard from "./FamilyMemberCard";
import {TaskDayRecord, DayName, MemberColors} from "../../types/tasks";


interface TaskCardsGridProps {
  groupedTasks: Record<string, TaskDayRecord[]>;
  onToggle: (task_id: number, day: DayName, checked: boolean) => void; // <--- use DayName
  memberColors: Record<string, MemberColors>;
}

const TaskCardsGrid: FC<TaskCardsGridProps> = ({ groupedTasks, onToggle, memberColors }) => {
  return (
    <div className="grid grid-responsive">
      {Object.entries(groupedTasks).map(([childName, tasks]) => {
        const colors: MemberColors =
          memberColors[childName] || memberColors["Rachel/Adam"];
        return (
          <FamilyMemberCard
            key={childName}
            name={childName}
            tasks={tasks}
            colors={colors}
            onToggle={onToggle}
          />
        );
      })}
    </div>
  );
};

export default TaskCardsGrid;
