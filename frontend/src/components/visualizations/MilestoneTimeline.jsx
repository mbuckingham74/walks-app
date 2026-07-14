import { useMemo } from 'react';
import { MapPin, Check, Circle, Flag } from 'lucide-react';
import { Panel } from './Panel';
import { formatMediumDate, formatNumber } from '../../lib/stats';

export function MilestoneTimeline({ data }) {
  const { milestones, crossings, nextMilestone } = useMemo(() => {
    const all = data?.milestones ?? [];
    const next = all.find((m) => !m.reached) ?? null;
    return {
      milestones: all,
      crossings: data?.crossings_completed ?? 0,
      nextMilestone: next,
    };
  }, [data]);

  const hasData = milestones.length > 0;

  return (
    <Panel
      title="Milestone Timeline"
      subtitle={
        crossings > 0
          ? `${crossings} ${crossings === 1 ? 'crossing' : 'crossings'} completed · journey history`
          : 'Cities reached and upcoming waypoints'
      }
      icon={MapPin}
    >
      {!hasData ? (
        <div className="text-sm text-gray-500 dark:text-gray-400 py-4">No route data available.</div>
      ) : (
        <div className="space-y-3">
          {nextMilestone && (
            <div className="flex items-center gap-3 rounded-lg bg-cyan-50 dark:bg-cyan-900/20 p-3 border border-cyan-100 dark:border-cyan-800/40">
              <Flag className="w-5 h-5 text-cyan-600 dark:text-cyan-400 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Next: {nextMilestone.city}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {formatNumber(nextMilestone.miles_from_start)} miles from Seattle
                </p>
              </div>
            </div>
          )}

          <div className="max-h-72 overflow-y-auto pr-1">
            <ol className="relative border-l border-gray-200 dark:border-gray-700 ml-2">
              {milestones.map((m, i) => (
                <li key={i} className="mb-3 ml-5">
                  <span
                    className={`absolute -left-[9px] flex items-center justify-center w-4 h-4 rounded-full ring-2 ring-white dark:ring-gray-800 ${
                      m.reached ? 'bg-primary-500' : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    {m.reached ? (
                      <Check className="w-2.5 h-2.5 text-white" />
                    ) : (
                      <Circle className="w-2 h-2 text-gray-500 dark:text-gray-400" />
                    )}
                  </span>
                  <div className="flex items-baseline justify-between gap-2">
                    <p
                      className={`text-sm ${
                        m.reached
                          ? 'font-medium text-gray-900 dark:text-white'
                          : 'text-gray-500 dark:text-gray-400'
                      }`}
                    >
                      {m.city}
                    </p>
                    <span className="text-xs text-gray-400 dark:text-gray-500 flex-shrink-0">
                      {formatNumber(m.miles_from_start)} mi
                    </span>
                  </div>
                  {m.reached && m.date_reached && (
                    <p className="text-xs text-primary-600 dark:text-primary-400 mt-0.5">
                      Reached {formatMediumDate(m.date_reached)}
                    </p>
                  )}
                </li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </Panel>
  );
}
