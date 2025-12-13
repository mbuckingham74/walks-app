import { MapPin, ArrowRight } from 'lucide-react';

export function ProgressCard({ currentPosition }) {
  if (!currentPosition) return null;

  const { current_waypoint, next_waypoint, miles_to_next, percent_complete } = currentPosition;

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
      <h3 className="text-sm font-medium text-gray-500 mb-4">Current Progress</h3>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-primary-500 rounded-full transition-all duration-500"
            style={{ width: `${percent_complete}%` }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {percent_complete.toFixed(1)}% of the way across America
        </p>
      </div>

      {/* Current location */}
      <div className="flex items-center gap-3 mb-3">
        <div className="bg-primary-100 p-2 rounded-lg">
          <MapPin className="w-4 h-4 text-primary-600" />
        </div>
        <div>
          <p className="text-xs text-gray-500">Currently near</p>
          <p className="font-medium text-gray-900">{current_waypoint?.city}</p>
        </div>
      </div>

      {/* Next waypoint */}
      {next_waypoint && (
        <div className="flex items-center gap-3 pl-2 border-l-2 border-gray-200 ml-4">
          <ArrowRight className="w-4 h-4 text-gray-400" />
          <div>
            <p className="text-xs text-gray-500">Next stop</p>
            <p className="text-sm text-gray-700">
              {next_waypoint.city}
              <span className="text-gray-400 ml-1">
                ({miles_to_next.toFixed(0)} mi)
              </span>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
