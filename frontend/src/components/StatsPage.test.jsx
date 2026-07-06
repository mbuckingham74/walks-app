import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { StatsPage } from './StatsPage';

const mockUseDetailedStats = vi.fn();
const mockUseTheme = vi.fn();

vi.mock('../hooks/useDetailedStats', () => ({
  useDetailedStats: (...args) => mockUseDetailedStats(...args),
}));

vi.mock('../hooks/useTheme', () => ({
  useTheme: () => mockUseTheme(),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <StatsPage />
    </MemoryRouter>
  );
}

const baseStats = {
  year: 2026,
  top_days: [
    { rank: 1, date: '2026-05-10', day_of_week: 'Sunday', steps: 25000, miles: 13.51 },
    { rank: 2, date: '2026-05-03', day_of_week: 'Sunday', steps: 22000, miles: 11.89 },
  ],
  top_weeks: [
    { rank: 1, year: 2026, week: 19, start_date: '2026-05-04', end_date: '2026-05-10', total_steps: 120000, avg_steps: 17142 },
  ],
  top_months: [
    { rank: 1, year: 2026, month: 5, month_name: 'May', total_steps: 500000, avg_steps: 16129, days_tracked: 31 },
  ],
  best_day_of_week: { day: 'Saturday', day_index: 5, total_steps: 180000, count: 12, avg_steps: 15000 },
  day_of_week_breakdown: [
    { day: 'Monday', day_index: 0, total_steps: 100000, count: 10, avg_steps: 10000 },
    { day: 'Saturday', day_index: 5, total_steps: 180000, count: 12, avg_steps: 15000 },
  ],
  peak_month: { year: 2026, month: 5, month_name: 'May', total_steps: 500000, avg_steps: 16129, days_tracked: 31 },
  longest_streak: { length: 10, start_date: '2026-05-01', end_date: '2026-05-10' },
  current_year_longest_streak: { length: 10, start_date: '2026-05-01', end_date: '2026-05-10' },
  consistency: { days_tracked: 120, days_in_period: 130, percentage: 92.3 },
  steps_distribution: [
    { label: '0–5k', count: 5, percentage: 4.2, color: '#9ca3af' },
    { label: '15–20k', count: 80, percentage: 66.7, color: '#22c55e' },
  ],
  monthly_totals: [
    { year: 2026, month: 1, month_name: 'January', total_steps: 300000, avg_steps: 9677, days_tracked: 31, goal_met_days: 20 },
  ],
  cumulative_data: [
    { date: '2026-01-01', steps: 10000, cumulative_steps: 10000, cumulative_miles: 5.41 },
    { date: '2026-01-02', steps: 15000, cumulative_steps: 25000, cumulative_miles: 13.51 },
  ],
  year_summary: {
    year: 2026,
    total_steps: 2000000,
    total_miles: 1081.08,
    avg_daily_steps: 15384,
    best_single_day_steps: 25000,
    best_single_day_date: '2026-05-10',
    goal_met_days: 110,
    goal_met_percentage: 84.6,
  },
};

describe('StatsPage', () => {
  beforeEach(() => {
    mockUseTheme.mockReturnValue({ isDark: false, toggle: vi.fn() });
  });

  it('shows loading state', () => {
    mockUseDetailedStats.mockReturnValue({ stats: null, loading: true, error: null, refetch: vi.fn() });
    renderPage();
    expect(screen.getByText('Loading detailed stats...')).toBeInTheDocument();
  });

  it('shows error state without data', () => {
    const refetch = vi.fn();
    mockUseDetailedStats.mockReturnValue({ stats: null, loading: false, error: 'Network error', refetch });
    renderPage();
    expect(screen.getByText(/Couldn't load stats/i)).toBeInTheDocument();
    expect(screen.getByText('Network error')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Try again/i }));
    expect(refetch).toHaveBeenCalled();
  });

  it('renders summary cards with data', () => {
    mockUseDetailedStats.mockReturnValue({ stats: baseStats, loading: false, error: null, refetch: vi.fn() });
    renderPage();
    expect(screen.getByText('Total Steps')).toBeInTheDocument();
    expect(screen.getByText('2,000,000')).toBeInTheDocument();
    expect(screen.getByText('Daily Average')).toBeInTheDocument();
    expect(screen.getByText('15,384')).toBeInTheDocument();
  });

  it('renders top days table', () => {
    mockUseDetailedStats.mockReturnValue({ stats: baseStats, loading: false, error: null, refetch: vi.fn() });
    renderPage();
    expect(screen.getByText('Top 10 Days')).toBeInTheDocument();
    // The best single day value also appears in summary; target the table row cell.
    const stepsCells = screen.getAllByText('25,000');
    expect(stepsCells.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('May 10')).toBeInTheDocument();
  });

  it('renders longest streak', () => {
    mockUseDetailedStats.mockReturnValue({ stats: baseStats, loading: false, error: null, refetch: vi.fn() });
    renderPage();
    expect(screen.getByText('Longest Streak')).toBeInTheDocument();
    expect(screen.getByText('10 days')).toBeInTheDocument();
  });

  it('renders consistency progress', () => {
    mockUseDetailedStats.mockReturnValue({ stats: baseStats, loading: false, error: null, refetch: vi.fn() });
    renderPage();
    expect(screen.getByText('Consistency')).toBeInTheDocument();
    expect(screen.getByText('92.3%')).toBeInTheDocument();
  });

  it('renders empty state when no data', () => {
    const emptyStats = {
      ...baseStats,
      top_days: [],
      top_weeks: [],
      top_months: [],
      best_day_of_week: null,
      day_of_week_breakdown: [],
      peak_month: null,
      longest_streak: null,
      current_year_longest_streak: null,
      steps_distribution: [],
      monthly_totals: [],
      cumulative_data: [],
      year_summary: {
        year: 2026,
        total_steps: 0,
        total_miles: 0,
        avg_daily_steps: 0,
        best_single_day_steps: 0,
        best_single_day_date: null,
        goal_met_days: 0,
        goal_met_percentage: 0,
      },
    };
    mockUseDetailedStats.mockReturnValue({ stats: emptyStats, loading: false, error: null, refetch: vi.fn() });
    renderPage();
    expect(screen.getAllByText('No data available').length).toBeGreaterThan(0);
    expect(screen.getByText('No step data recorded yet.')).toBeInTheDocument();
  });
});
