import { Award } from 'lucide-react';
import { formatNumber, formatShortDate } from '../../lib/stats';

function RecordCard({ label, record }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200 h-full">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 rounded-lg bg-primary-500">
          <Award className="w-5 h-5 text-white" />
        </div>
        <span className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</span>
      </div>
      {record ? (
        <div>
          <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
            {formatNumber(record.total_steps)}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {formatNumber(record.avg_steps)}/day avg
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {formatShortDate(record.start_date)} – {formatShortDate(record.end_date)}
          </p>
        </div>
      ) : (
        <p className="text-sm text-gray-400 dark:text-gray-500 py-2">Not enough data yet</p>
      )}
    </div>
  );
}

export function RollingRecords({ data }) {
  const records = data ?? { best_7: null, best_14: null, best_30: null };
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <RecordCard label="Best 7 days" record={records.best_7} />
      <RecordCard label="Best 14 days" record={records.best_14} />
      <RecordCard label="Best 30 days" record={records.best_30} />
    </div>
  );
}
