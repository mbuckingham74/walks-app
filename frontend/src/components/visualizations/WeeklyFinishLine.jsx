import { Flag, CalendarRange } from 'lucide-react';
import { formatNumber, formatShortDate } from '../../lib/stats';
import { parseLocalDate } from '../../lib/dates';

export function WeeklyFinishLine({ data }) {
  const wfl = data ?? {};
  const current = wfl.current_steps ?? 0;
  const goal = wfl.weekly_goal ?? 105000;
  const required = wfl.required_daily_avg ?? 0;
  const remaining = wfl.days_remaining ?? 0;
  const pct = goal > 0 ? Math.min(100, (current / goal) * 100) : 0;

  const onTrack = current >= goal || remaining === 0;
  const weekStart = wfl.week_start ? parseLocalDate(wfl.week_start) : null;
  const weekEnd = wfl.week_end ? parseLocalDate(wfl.week_end) : null;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200 h-full">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 rounded-lg bg-cyan-500">
          <Flag className="w-5 h-5 text-white" />
        </div>
        <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Weekly Finish Line</span>
      </div>

      <div className="flex items-baseline justify-between mb-2">
        <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
          {formatNumber(current)}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          / {formatNumber(goal)}
        </p>
      </div>

      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden mb-3">
        <div
          className="bg-cyan-500 h-2.5 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>

      {weekStart && weekEnd && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 flex items-center gap-1">
          <CalendarRange className="w-3.5 h-3.5" />
          {formatShortDate(wfl.week_start)} – {formatShortDate(wfl.week_end)}
        </p>
      )}

      {onTrack ? (
        <p className="text-sm text-emerald-600 dark:text-emerald-400 font-medium">
          {remaining === 0 ? 'Week complete' : 'Goal reached!'}
        </p>
      ) : (
        <p className="text-sm text-gray-600 dark:text-gray-300">
          Need <span className="font-semibold text-gray-900 dark:text-white">{formatNumber(required)}/day</span> for {remaining} more {remaining === 1 ? 'day' : 'days'}
        </p>
      )}
    </div>
  );
}
