import { describe, it, expect } from 'vitest';
import {
  formatNumber,
  formatShortDate,
  formatMediumDate,
  formatMonthYear,
  getChartColors,
  emptyDetailedStats,
} from './stats';

describe('formatNumber', () => {
  it('formats integers with commas', () => {
    expect(formatNumber(1234567)).toBe('1,234,567');
  });

  it('rounds decimals', () => {
    expect(formatNumber(1234.56)).toBe('1,235');
  });

  it('returns dash for null/undefined/NaN', () => {
    expect(formatNumber(null)).toBe('—');
    expect(formatNumber(undefined)).toBe('—');
    expect(formatNumber(NaN)).toBe('—');
  });
});

describe('formatShortDate', () => {
  it('formats a date string', () => {
    expect(formatShortDate('2026-05-10')).toBe('May 10');
  });

  it('returns dash for missing input', () => {
    expect(formatShortDate(null)).toBe('—');
    expect(formatShortDate('')).toBe('—');
  });
});

describe('formatMediumDate', () => {
  it('includes weekday', () => {
    expect(formatMediumDate('2026-05-10')).toBe('Sun, May 10');
  });

  it('returns dash for missing input', () => {
    expect(formatMediumDate(null)).toBe('—');
  });
});

describe('formatMonthYear', () => {
  it('formats month and year', () => {
    expect(formatMonthYear(5, 2026)).toBe('May 2026');
  });
});

describe('getChartColors', () => {
  it('returns primary color', () => {
    expect(getChartColors().primary).toBe('#16a34a');
  });

  it('adjusts grid color for dark mode', () => {
    expect(getChartColors(true).grid).toBe('#374151');
    expect(getChartColors(false).grid).toBe('#e5e7eb');
  });
});

describe('emptyDetailedStats', () => {
  it('returns a valid empty shape', () => {
    const empty = emptyDetailedStats(2026);
    expect(empty.year).toBe(2026);
    expect(empty.top_days).toEqual([]);
    expect(empty.year_summary.total_steps).toBe(0);
  });
});
