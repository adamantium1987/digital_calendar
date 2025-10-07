// src/components/EmptyTasksMessage.tsx
import { FC } from "react";

interface EmptyTasksMessageProps {
  dayName: string;
}

const EmptyTasksMessage: FC<EmptyTasksMessageProps> = ({ dayName }) => {
  return (
    <div className="card">
      <div className="no-events">
        <h3>No tasks scheduled for {dayName}</h3>
        <p>Enjoy your free day! 🎉</p>
      </div>
    </div>
  );
};

export default EmptyTasksMessage;
