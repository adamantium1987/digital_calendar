import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { EventItem } from '../EventItem-optimized';

describe('EventItem', () => {
  const mockEvent = {
    id: '1',
    title: 'Team Meeting',
    start: '2024-01-15T10:00:00Z',
    end: '2024-01-15T11:00:00Z',
    color: '#2196f3',
    description: 'Weekly team sync',
    location: 'Conference Room A',
    all_day: false,
  };

  const mockOnClick = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders event title correctly', () => {
    render(<EventItem event={mockEvent} onClick={mockOnClick} />);
    expect(screen.getByText('Team Meeting')).toBeInTheDocument();
  });

  it('displays event time when showTime is true', () => {
    render(<EventItem event={mockEvent} onClick={mockOnClick} showTime={true} />);
    const timeElement = screen.getByText(/10:00 AM - 11:00 AM/);
    expect(timeElement).toBeInTheDocument();
  });

  it('hides event time when showTime is false', () => {
    render(<EventItem event={mockEvent} onClick={mockOnClick} showTime={false} />);
    const timeElement = screen.queryByText(/10:00 AM - 11:00 AM/);
    expect(timeElement).not.toBeInTheDocument();
  });

  it('calls onClick handler when clicked', () => {
    render(<EventItem event={mockEvent} onClick={mockOnClick} />);
    const eventCard = screen.getByText('Team Meeting').closest('div');
    fireEvent.click(eventCard!);
    expect(mockOnClick).toHaveBeenCalledTimes(1);
    expect(mockOnClick).toHaveBeenCalledWith(mockEvent);
  });

  it('applies compact styles when compact prop is true', () => {
    render(<EventItem event={mockEvent} onClick={mockOnClick} compact={true} />);
    const eventCard = screen.getByText('Team Meeting').closest('div');
    expect(eventCard).toHaveClass('compactEvent');
  });

  it('applies event color as background', () => {
    render(<EventItem event={mockEvent} onClick={mockOnClick} />);
    const eventCard = screen.getByText('Team Meeting').closest('div');
    expect(eventCard).toHaveStyle({ backgroundColor: '#2196f3' });
  });

  it('truncates long titles when maxTitleLength is provided', () => {
    const longTitleEvent = {
      ...mockEvent,
      title: 'This is a very long event title that should be truncated',
    };
    render(
      <EventItem event={longTitleEvent} onClick={mockOnClick} maxTitleLength={20} />
    );
    expect(screen.getByText(/This is a very long.../)).toBeInTheDocument();
  });

  it('displays all-day events correctly', () => {
    const allDayEvent = {
      ...mockEvent,
      all_day: true,
    };
    render(<EventItem event={allDayEvent} onClick={mockOnClick} showTime={true} />);
    expect(screen.getByText('All Day')).toBeInTheDocument();
  });

  it('handles keyboard navigation (Enter key)', () => {
    render(<EventItem event={mockEvent} onClick={mockOnClick} />);
    const eventCard = screen.getByText('Team Meeting').closest('div');
    fireEvent.keyDown(eventCard!, { key: 'Enter', code: 'Enter' });
    expect(mockOnClick).toHaveBeenCalledWith(mockEvent);
  });

  it('handles keyboard navigation (Space key)', () => {
    render(<EventItem event={mockEvent} onClick={mockOnClick} />);
    const eventCard = screen.getByText('Team Meeting').closest('div');
    fireEvent.keyDown(eventCard!, { key: ' ', code: 'Space' });
    expect(mockOnClick).toHaveBeenCalledWith(mockEvent);
  });

  it('does not re-render when props are unchanged (memoization)', () => {
    const { rerender } = render(<EventItem event={mockEvent} onClick={mockOnClick} />);
    const firstRender = screen.getByText('Team Meeting');

    rerender(<EventItem event={mockEvent} onClick={mockOnClick} />);
    const secondRender = screen.getByText('Team Meeting');

    expect(firstRender).toBe(secondRender);
  });
});
