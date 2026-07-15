import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { ActivityCalendar } from './ActivityCalendar';

const data = {
  days: [
    { date: '2026-01-01', steps: 18000, goal_met: true, intensity: 3 },
    { date: '2026-01-02', steps: 5000, goal_met: false, intensity: 2 },
  ],
};

describe('ActivityCalendar', () => {
  it('shows the daily step total when a square is hovered', () => {
    render(<ActivityCalendar data={data} dailyGoal={15000} />);
    const day = screen.getByRole('button', { name: 'Jan 1: 18,000 steps (goal met)' });

    fireEvent.mouseEnter(day);

    expect(screen.getByRole('tooltip')).toHaveTextContent('Jan 1: 18,000 steps');
    expect(screen.getByRole('tooltip')).toHaveTextContent('Goal met');

    fireEvent.mouseLeave(day);
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
  });

  it('also shows the daily step total when a square receives keyboard focus', () => {
    render(<ActivityCalendar data={data} dailyGoal={15000} />);
    const day = screen.getByRole('button', { name: 'Jan 2: 5,000 steps' });

    fireEvent.focus(day);

    expect(screen.getByRole('tooltip')).toHaveTextContent('Jan 2: 5,000 steps');
  });
});
