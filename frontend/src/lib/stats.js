import { parseLocalDate } from './dates';

/**
 * Format a number with commas.
 * @param {number} value
 * @returns {string}
 */
export function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return Math.round(value).toLocaleString();
}

/**
 * Format a date string as a short local date.
 * @param {string} dateStr
 * @returns {string}
 */
export function formatShortDate(dateStr) {
  if (!dateStr) return '—';
  const date = parseLocalDate(dateStr);
  if (!date) return '—';
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/**
 * Format a date string as a medium local date.
 * @param {string} dateStr
 * @returns {string}
 */
export function formatMediumDate(dateStr) {
  if (!dateStr) return '—';
  const date = parseLocalDate(dateStr);
  if (!date) return '—';
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format a month number and year as a label.
 * @param {number} month
 * @param {number} year
 * @returns {string}
 */
export function formatMonthYear(month, year) {
  const date = new Date(year, month - 1, 1);
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
}

/**
 * Compute chart colors based on dark mode and Tailwind palette.
 * @param {boolean} isDark
 * @returns {object}
 */
export function getChartColors(isDark = false) {
  return {
    primary: '#16a34a',
    primaryFill: '#22c55e',
    grid: isDark ? '#374151' : '#e5e7eb',
    axis: isDark ? '#9ca3af' : '#6b7280',
    tooltipBg: isDark ? '#1f2937' : '#ffffff',
    tooltipBorder: isDark ? '#374151' : '#e5e7eb',
    tooltipText: isDark ? '#f9fafb' : '#111827',
  };
}

/**
 * Build empty detailed stats payload for loading/skeleton states.
 * @returns {object}
 */
export function emptyDetailedStats(year) {
  return {
    year,
    top_days: [],
    top_weeks: [],
    top_months: [],
    best_day_of_week: null,
    day_of_week_breakdown: [],
    peak_month: null,
    longest_streak: null,
    current_year_longest_streak: null,
    consistency: { days_tracked: 0, days_in_period: 0, percentage: 0 },
    steps_distribution: [],
    monthly_totals: [],
    cumulative_data: [],
    year_summary: {
      year,
      total_steps: 0,
      total_miles: 0,
      avg_daily_steps: 0,
      best_single_day_steps: 0,
      best_single_day_date: null,
      goal_met_days: 0,
      goal_met_percentage: 0,
    },
  };
}
