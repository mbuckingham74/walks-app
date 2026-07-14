import { RotateCcw } from 'lucide-react';
import { formatNumber } from '../../lib/stats';

export function ComebackScore({ data }) {
  const cb = data ?? { attempts: 0, successes: 0, score: null };
  const score = cb.score;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200 h-full">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 rounded-lg bg-orange-500">
          <RotateCcw className="w-5 h-5 text-white" />
        </div>
        <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Comeback Score</span>
      </div>
      {score !== null && score !== undefined ? (
        <div>
          <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
            {score}%
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Met the goal {formatNumber(cb.successes)} of {formatNumber(cb.attempts)} times after a miss
          </p>
        </div>
      ) : (
        <p className="text-sm text-gray-400 dark:text-gray-500 py-2">
          {cb.attempts === 0 ? 'No misses to bounce back from yet' : 'No data yet'}
        </p>
      )}
    </div>
  );
}
