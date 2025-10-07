// src/types/tasks.ts

import {DAYS} from "../constants/days";

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
