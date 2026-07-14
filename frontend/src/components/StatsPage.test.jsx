import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { StatsPage } from './StatsPage';

const mockUseDetailedStats = vi.fn();
const mockUseTheme = vi.fn();
const mockUseConfig = vi.fn();

vi.mock('../hooks/useDetailedStats', () => ({
  useDetailedStats: (...args) => mockUseDetailedStats(...args),
}));

vi.mock('../hooks/useTheme', () => ({
  useTheme: () => mockUseTheme(),
}));

vi.mock('../hooks/useConfig', () => ({
  useConfig: () => mockUseConfig(),
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
  activity_calendar: {
    days: [
      { date: '2026-01-01', steps: 18000, goal_met: true, intensity: 3 },
      { date: '2026-01-02', steps: 5000, goal_met: false, intensity: 2 },
    ],
  },
  year_race: {
    current_year: 2026,
    previous_year: 2025,
    goal_daily: 15000,
    current: [{ day_of_year: 1, cumulative_steps: 18000 }],
    previous: [{ day_of_year: 1, cumulative_steps: 12000 }],
  },
  momentum: [
    { date: '2026-01-07', steps: 18000, avg_7: 16000, avg_28: null },
  ],
  record_chase: { today_steps: 18000, today_date: '2026-05-10', top_10_threshold: 25000, steps_to_top_10: 7001, in_top_10: false },
  weekly_finish_line: { week_start: '2026-05-04', week_end: '2026-05-10', current_steps: 60000, weekly_goal: 105000, days_elapsed: 7, days_remaining: 0, required_daily_avg: 0 },
  goal_surplus: [
    { date: '2026-01-01', surplus: 3000 },
    { date: '2026-01-02', surplus: -10000 },
  ],
  rolling_records: {
    best_7: { total_steps: 120000, avg_steps: 17142, start_date: '2026-05-04', end_date: '2026-05-10' },
    best_14: { total_steps: 220000, avg_steps: 15714, start_date: '2026-05-04', end_date: '2026-05-17' },
    best_30: { total_steps: 450000, avg_steps: 15000, start_date: '2026-05-04', end_date: '2026-06-02' },
  },
  day_percentile: { steps: 18000, date: '2026-05-10', percentile: 82.0 },
  milestone_timeline: {
    crossings_completed: 0,
    milestones: [
      { city: 'Seattle, WA', miles_from_start: 0, reached: true, date_reached: '2026-01-01' },
      { city: 'Ellensburg, WA', miles_from_start: 107, reached: false, date_reached: null },
    ],
  },
  perfect_periods: { perfect_weeks: 5, best_goal_met_month: { year: 2026, month: 5, month_name: 'May', total_steps: 500000, avg_steps: 16129, days_tracked: 31, goal_met_days: 28 }, longest_5_of_7_run: 8 },
  comeback_score: { attempts: 20, successes: 14, score: 70.0 },
};

describe('StatsPage', () => {
  beforeEach(() => {
    mockUseTheme.mockReturnValue({ isDark: false, toggle: vi.fn() });
    mockUseConfig.mockReturnValue({ config: { steps_per_mile: 1850, daily_goal: 15000 }, loading: false, error: null });
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
