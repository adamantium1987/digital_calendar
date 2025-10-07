// src/components/TaskChartDisplay.tsx
import React, { useState, useEffect, useMemo } from "react";
import { TaskDayRecord, DayName } from "../types/tasks";
import {Toast} from "../components/global/Toast";
import TaskDateNav from "../components/task/TaskDateNav";
import EmptyTasksMessage from "../components/task/EmptyTaskMessage";
import TaskCardsGrid from "../components/task/TaskCardsGrid";
import {useSwipeNavigation} from "../hooks/useSwipeNavigation";
import { MEMBER_COLORS } from "../constants/memberColors";
import { DAYS } from "../constants/days";
import {useNavigate} from "react-router-dom";

export const TaskChartDisplay: React.FC = () => {
  const navigate = useNavigate();
  useSwipeNavigation({
    onSwipeLeft: () => navigate('/display'),
    onSwipeRight: () => navigate('/dashboard'),
    minSwipeDistance: 75
  });

  const [taskDays, setTaskDays] = useState<TaskDayRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null);
  const [currentDate, setCurrentDate] = useState<Date>(new Date());

  const currentDayName: DayName = DAYS[currentDate.getDay()];

  // Fetch tasks from API
  const fetchTasks = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        day: currentDayName,
        week: getIsoWeekStart(currentDate),
        format: "individual",
      });

      const res = await fetch(`/api/tasks?${params.toString()}`);

      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const data = await res.json();
      console.log(data)
      setTaskDays(Array.isArray(data.task_days) ? data.task_days : []);
    } catch (err: any) {
      console.error("fetchTasks error", err);
      setToast({ type: "error", message: `Failed to fetch tasks: ${err?.message}` });
      setTaskDays([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchTasks();
  }, [currentDate]);

  // Helpers
  const getIsoWeekStart = (d: Date) => {
    const copy = new Date(d);
    copy.setDate(copy.getDate() - copy.getDay());
    return copy.toISOString().slice(0, 10);
  };

  const toggleComplete = (task_id: number, day: DayName, checked: boolean) => {
    setTaskDays(prev =>
      prev.map(task =>
        task.task_id === task_id && task.day_name === day ? { ...task, completed: checked } : task
      )
    );
    setToast({ type: "success", message: "Task updated!" });
  };

  // Group tasks by child
  const groupedTasks = useMemo(() => {
    const grouped: Record<string, TaskDayRecord[]> = {};
    taskDays.filter(c => c.day_name === currentDayName).forEach(c => {
      if (!grouped[c.name]) grouped[c.name] = [];
      grouped[c.name].push(c);
    });
    return grouped;
  }, [taskDays, currentDayName]);

  const totalTasks = Object.values(groupedTasks).flat().length;
  const completedTasks = Object.values(groupedTasks).flat().filter(c => c.completed).length;

  // Date navigation
  const prevDay = () => setCurrentDate(d => { const nd = new Date(d); nd.setDate(nd.getDate() - 1); return nd; });
  const nextDay = () => setCurrentDate(d => { const nd = new Date(d); nd.setDate(nd.getDate() + 1); return nd; });
  const goToToday = () => setCurrentDate(new Date());

  if (loading) return <div className="loading-container"><div className="loading">Loading tasks...</div></div>;

  return (
    <div className="container">
      {/* Date Navigation */}
      <TaskDateNav
        currentDate={currentDate}
        completedTasks={completedTasks}
        totalTasks={totalTasks}
        onPrev={prevDay}
        onNext={nextDay}
        onGoToToday={goToToday}
      />
      {/* Task Cards */}
      {totalTasks === 0 && <EmptyTasksMessage dayName={currentDayName} />}
      {totalTasks > 0 && (
        <TaskCardsGrid
          groupedTasks={groupedTasks}
          onToggle={toggleComplete}
          memberColors={MEMBER_COLORS}
        />
      )}
      {/* Toast */}
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
    </div>
  );
};
