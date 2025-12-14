import { MapPin, ArrowRight } from 'lucide-react';

export function ProgressCard({ currentPosition }) {
  if (!currentPosition) return null;

  const { current_waypoint, next_waypoint, miles_to_next, percent_complete } = currentPosition;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200">
      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-4">Current Progress</h3>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary-500 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(0, percent_complete ?? 0))}%` }}
          />
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {percent_complete?.toFixed(1) ?? '0.0'}% of the way across America
        </p>
      </div>

      {/* Current location */}
      <div className="flex items-center gap-3 mb-3">
        <div className="bg-primary-100 dark:bg-primary-900/30 p-2 rounded-lg">
          <MapPin className="w-4 h-4 text-primary-600 dark:text-primary-400" />
        </div>
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400">Currently near</p>
          <p className="font-medium text-gray-900 dark:text-white">{current_waypoint?.city}</p>
        </div>
      </div>

      {/* Next waypoint */}
      {next_waypoint && (
        <div className="flex items-center gap-3 pl-2 border-l-2 border-gray-200 dark:border-gray-600 ml-4">
          <ArrowRight className="w-4 h-4 text-gray-400 dark:text-gray-500" />
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Next stop</p>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {next_waypoint.city}
              <span className="text-gray-400 dark:text-gray-500 ml-1">
                ({miles_to_next?.toFixed(0) ?? '—'} mi)
              </span>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
