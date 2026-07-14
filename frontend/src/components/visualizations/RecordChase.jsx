import { Trophy, Target } from 'lucide-react';
import { formatNumber, formatMediumDate } from '../../lib/stats';

export function RecordChase({ data }) {
  const chase = data ?? {};
  const inTop10 = chase.in_top_10;
  const todaySteps = chase.today_steps ?? 0;
  const toTop10 = chase.steps_to_top_10 ?? 0;
  const threshold = chase.top_10_threshold ?? 0;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200 h-full">
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg ${inTop10 ? 'bg-amber-500' : 'bg-violet-500'}`}>
          {inTop10 ? <Trophy className="w-5 h-5 text-white" /> : <Target className="w-5 h-5 text-white" />}
        </div>
        <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Record Chase</span>
      </div>
      {inTop10 ? (
        <div>
          <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
            Top 10 today!
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {formatNumber(todaySteps)} steps — you&apos;re among your best days
            {chase.today_date && ` (${formatMediumDate(chase.today_date)})`}
          </p>
        </div>
      ) : (
        <div>
          <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
            {formatNumber(toTop10)} <span className="text-base font-normal text-gray-500 dark:text-gray-400">to go</span>
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {formatNumber(todaySteps)} today · beat {formatNumber(threshold)} to reach your top 10
          </p>
        </div>
      )}
    </div>
  );
}
