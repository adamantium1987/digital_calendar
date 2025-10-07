import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TaskItem } from '../TaskItem-optimized';

describe('TaskItem', () => {
  const mockTask = {
    id: '1',
    title: 'Complete project documentation',
    completed: false,
    due_date: '2024-01-20T17:00:00Z',
    priority: 'high' as const,
    description: 'Write comprehensive docs',
  };

  const mockOnToggle = jest.fn();
  const mockOnClick = jest.fn();
  const mockOnDelete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders task title correctly', () => {
    render(
      <TaskItem
        task={mockTask}
        onToggle={mockOnToggle}
        onClick={mockOnClick}
      />
    );
    expect(screen.getByText('Complete project documentation')).toBeInTheDocument();
  });

  it('displays unchecked checkbox for incomplete tasks', () => {
    render(
      <TaskItem
        task={mockTask}
        onToggle={mockOnToggle}
        onClick={mockOnClick}
      />
    );
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).not.toBeChecked();
  });

  it('displays checked checkbox for completed tasks', () => {
    const completedTask = { ...mockTask, completed: true };
    render(
      <TaskItem
        task={completedTask}
        onToggle={mockOnToggle}
        onClick={mockOnClick}
      />
    );
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).toBeChecked();
  });

  it('calls onToggle when checkbox is clicked', () => {
    render(
      <TaskItem
        task={mockTask}
        onToggle={mockOnToggle}
        onClick={mockOnClick}
      />
    );
    const checkbox = screen.getByRole('checkbox');
    fireEvent.click(checkbox);
    expect(mockOnToggle).toHaveBeenCalledTimes(1);
    expect(mockOnToggle).toHaveBeenCalledWith(mockTask.id);
  });

  it('calls onClick when task is clicked', () => {
    render(
      <TaskItem
        task={mockTask}
        onToggle={mockOnToggle}
        onClick={mockOnClick}
      />
    );
    const taskTitle = screen.getByText('Complete project documentation');
    fireEvent.click(taskTitle);
    expect(mockOnClick).toHaveBeenCalledTimes(1);
    expect(mockOnClick).toHaveBeenCalledWith(mockTask);
  });

  it('displays due date when provided', () => {
    render(
      <TaskItem
        task={mockTask}
        onToggle={mockOnToggle}
        onClick={mockOnClick}
      />
    );
    expect(screen.getByText(/Due:/)).toBeInTheDocument();
  });

  it('displays priority badge for high priority tasks', () => {
    render(
      <TaskItem
        task={mockTask}
        onToggle={mockOnToggle}
        onClick={mockOnClick}
      />
    );
    expect(screen.getByText('High')).toBeInTheDocument();
  });

  it('applies strikethrough style to completed tasks', () => {
    const completedTask = { ...mockTask, completed: true };
    render(
      <TaskItem
        task={completedTask}
        onToggle={mockOnToggle}
        onClick={mockOnClick}
      />
    );
    const taskTitle = screen.getByText('Complete project documentation');
    expect(taskTitle).toHaveStyle({ textDecoration: 'line-through' });
  });

  it('shows delete button when onDelete is provided', () => {
    render(
      <TaskItem
        task={mockTask}
        onToggle={mockOnToggle}
        onClick={mockOnClick}
        onDelete={mockOnDelete}
      />
    );
    const deleteButton = screen.getByLabelText(/delete/i);
    expect(deleteButton).toBeInTheDocument();
  });

  it('calls onDelete when delete button is clicked', () => {
    render(
      <TaskItem
        task={mockTask}
        onToggle={mockOnToggle}
        onClick={mockOnClick}
        onDelete={mockOnDelete}
      />
    );
    const deleteButton = screen.getByLabelText(/delete/i);
    fireEvent.click(deleteButton);
    expect(mockOnDelete).toHaveBeenCalledTimes(1);
    expect(mockOnDelete).toHaveBeenCalledWith(mockTask.id);
  });

  it('does not show delete button when onDelete is not provided', () => {
    render(
      <TaskItem
        task={mockTask}
        onToggle={mockOnToggle}
        onClick={mockOnClick}
      />
    );
    const deleteButton = screen.queryByLabelText(/delete/i);
    expect(deleteButton).not.toBeInTheDocument();
  });

  it('handles overdue tasks with warning styling', () => {
    const overdueTask = {
      ...mockTask,
      due_date: '2020-01-01T17:00:00Z', // Past date
    };
    render(
      <TaskItem
        task={overdueTask}
        onToggle={mockOnToggle}
        onClick={mockOnClick}
      />
    );
    const taskContainer = screen.getByText('Complete project documentation').closest('div');
    expect(taskContainer).toHaveClass('overdue');
  });

  it('memoizes correctly and does not re-render with same props', () => {
    const { rerender } = render(
      <TaskItem
        task={mockTask}
        onToggle={mockOnToggle}
        onClick={mockOnClick}
      />
    );
    const firstRender = screen.getByText('Complete project documentation');

    rerender(
      <TaskItem
        task={mockTask}
        onToggle={mockOnToggle}
        onClick={mockOnClick}
      />
    );
    const secondRender = screen.getByText('Complete project documentation');

    expect(firstRender).toBe(secondRender);
  });
});
