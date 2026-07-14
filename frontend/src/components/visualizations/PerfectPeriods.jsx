import { Sparkles, CalendarCheck, CalendarHeart } from 'lucide-react';
import { formatMonthYear } from '../../lib/stats';

export function PerfectPeriods({ data }) {
  const pp = data ?? { perfect_weeks: 0, best_goal_met_month: null, longest_5_of_7_run: 0 };

  const bestMonth = pp.best_goal_met_month;
  const bestMonthPct =
    bestMonth && bestMonth.days_tracked > 0
      ? Math.round((bestMonth.goal_met_days / bestMonth.days_tracked) * 100)
      : 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200 h-full">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 rounded-lg bg-emerald-500">
            <CalendarCheck className="w-5 h-5 text-white" />
          </div>
          <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Perfect Weeks</span>
        </div>
        <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
          {pp.perfect_weeks ?? 0}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Weeks where you met the goal all 7 days
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200 h-full">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 rounded-lg bg-amber-500">
            <CalendarHeart className="w-5 h-5 text-white" />
          </div>
          <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Best Goal Month</span>
        </div>
        {bestMonth ? (
          <div>
            <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
              {bestMonth.goal_met_days}
              <span className="text-base font-normal text-gray-500 dark:text-gray-400"> / {bestMonth.days_tracked}</span>
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {formatMonthYear(bestMonth.month, bestMonth.year)} · {bestMonthPct}% met
            </p>
          </div>
        ) : (
          <p className="text-sm text-gray-400 dark:text-gray-500 py-2">No data yet</p>
        )}
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200 h-full">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 rounded-lg bg-violet-500">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="text-sm font-medium text-gray-500 dark:text-gray-400">5-of-7 Streak</span>
        </div>
        <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
          {pp.longest_5_of_7_run ?? 0} <span className="text-base font-normal text-gray-500 dark:text-gray-400">weeks</span>
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Longest run of weeks hitting the goal 5+ days
        </p>
      </div>
    </div>
  );
}
