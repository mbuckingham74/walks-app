import { Percent } from 'lucide-react';
import { formatNumber, formatMediumDate } from '../../lib/stats';

export function DayPercentile({ data }) {
  const pct = data ?? null;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200 h-full">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 rounded-lg bg-indigo-500">
          <Percent className="w-5 h-5 text-white" />
        </div>
        <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Day Percentile</span>
      </div>
      {pct ? (
        <div>
          <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
            Better than {pct.percentile}% <span className="text-base font-normal text-gray-500 dark:text-gray-400">of days</span>
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {formatNumber(pct.steps)} steps
            {pct.date && ` · ${formatMediumDate(pct.date)}`}
          </p>
        </div>
      ) : (
        <p className="text-sm text-gray-400 dark:text-gray-500 py-2">No data yet</p>
      )}
    </div>
  );
}
