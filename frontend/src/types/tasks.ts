// src/types/tasks.ts

export const DAYS = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday'] as const;
export type DayName = (typeof DAYS)[number];

export type TaskType = 'chore' | 'hygiene';

export interface TaskDayRecord {
  task_id: number;
  task: string;
  day_name: DayName;
  name: string;
  completed: boolean;
  type: TaskType;
}
export interface MemberColors {
  bg: string;
  border: string;
  text: string;
}
