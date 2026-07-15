import { useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { Calendar } from 'lucide-react';
import { Panel } from './Panel';
import { parseLocalDate } from '../../lib/dates';
import { formatNumber } from '../../lib/stats';

const WEEKDAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const MONTH_LABELS = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
];

const INTENSITY_CLASSES = [
  'bg-gray-100 dark:bg-gray-700/50',
  'bg-primary-100 dark:bg-primary-900/40',
  'bg-primary-300 dark:bg-primary-700',
  'bg-primary-500 dark:bg-primary-600',
  'bg-primary-600 dark:bg-primary-400',
];

function toMonFirstWeekday(date) {
  return (date.getDay() + 6) % 7;
}

function getDayLabel(day) {
  const date = parseLocalDate(day.date);
  const dateLabel = date
    ? date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    : day.date;

  return `${dateLabel}: ${formatNumber(day.steps)} steps${day.goal_met ? ' (goal met)' : ''}`;
}

export function ActivityCalendar({ data, dailyGoal }) {
  const [tooltip, setTooltip] = useState(null);

  const { grid, monthLabels, totals } = useMemo(() => {
    const days = data?.days ?? [];
    if (days.length === 0) {
      return { grid: [], monthLabels: [], totals: { tracked: 0, goalMet: 0 } };
    }

    const firstDate = parseLocalDate(days[0].date);
    const firstWeekday = toMonFirstWeekday(firstDate);
    const weeks = [];
    let tracked = 0;
    let goalMet = 0;

    days.forEach((d, idx) => {
      const date = parseLocalDate(d.date);
      const weekIndex = Math.floor((idx + firstWeekday) / 7);
      const row = toMonFirstWeekday(date);
      if (!weeks[weekIndex]) weeks[weekIndex] = Array(7).fill(null);
      weeks[weekIndex][row] = d;
      if (d.steps > 0) tracked += 1;
      if (d.goal_met) goalMet += 1;
    });

    const labels = [];
    let lastMonth = -1;
    weeks.forEach((week) => {
      const firstDay = week.find((d) => d);
      if (firstDay) {
        const m = parseLocalDate(firstDay.date).getMonth();
        if (m !== lastMonth) {
          labels.push({ month: m, label: MONTH_LABELS[m] });
          lastMonth = m;
        } else {
          labels.push({ month: m, label: '' });
        }
      } else {
        labels.push({ month: -1, label: '' });
      }
    });

    return { grid: weeks, monthLabels: labels, totals: { tracked, goalMet } };
  }, [data]);

  const hasData = grid.length > 0;

  const showTooltip = (element, day) => {
    const rect = element.getBoundingClientRect();
    const placement = rect.top > 72 ? 'above' : 'below';
    const viewportWidth = globalThis.innerWidth;

    setTooltip({
      day,
      left: Math.min(Math.max(rect.left + rect.width / 2, 96), viewportWidth - 96),
      top: placement === 'above' ? rect.top - 8 : rect.bottom + 8,
      placement,
    });
  };

  return (
    <>
      <Panel
        title="Activity Calendar"
        subtitle="Daily consistency, colored by goal progress"
        icon={Calendar}
      >
        {!hasData ? (
          <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400 text-sm py-8">
            No step data recorded yet.
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
              <span>{totals.tracked} active days</span>
              <span>{totals.goalMet} goals met</span>
              <span className="hidden sm:inline">Goal: {formatNumber(dailyGoal)} steps</span>
            </div>

            <div className="overflow-x-auto pb-1">
              <div className="inline-flex flex-col gap-1 min-w-max">
                <div className="flex gap-1 pl-8">
                  {monthLabels.map((m, i) => (
                    <div
                      key={i}
                      className="w-3 text-[10px] text-gray-400 dark:text-gray-500 leading-none"
                    >
                      {m.label}
                    </div>
                  ))}
                </div>
                <div className="flex gap-1">
                  <div className="flex flex-col gap-1 justify-around pr-1 text-[10px] text-gray-400 dark:text-gray-500">
                    {WEEKDAY_LABELS.map((label, i) => (
                      <div key={label} className="h-3 leading-3">
                        {i % 2 === 0 ? label : ''}
                      </div>
                    ))}
                  </div>
                  {grid.map((week, wi) => (
                    <div key={wi} className="flex flex-col gap-1">
                      {week.map((day, di) =>
                        day ? (
                          <button
                            key={di}
                            type="button"
                            className={`w-3 h-3 rounded-sm ${INTENSITY_CLASSES[day.intensity]} focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-400 focus-visible:ring-offset-1 dark:focus-visible:ring-offset-gray-800`}
                            aria-label={getDayLabel(day)}
                            aria-describedby={
                              tooltip?.day.date === day.date
                                ? 'activity-calendar-tooltip'
                                : undefined
                            }
                            onMouseEnter={(event) => showTooltip(event.currentTarget, day)}
                            onMouseLeave={() => setTooltip(null)}
                            onFocus={(event) => showTooltip(event.currentTarget, day)}
                            onBlur={() => setTooltip(null)}
                          />
                        ) : (
                          <div key={di} className="w-3 h-3 rounded-sm bg-transparent" />
                        ),
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
              <span>Less</span>
              {INTENSITY_CLASSES.map((cls, i) => (
                <div key={i} className={`w-3 h-3 rounded-sm ${cls}`} />
              ))}
              <span>More</span>
            </div>
          </div>
        )}
      </Panel>

      {tooltip &&
        createPortal(
          <div
            id="activity-calendar-tooltip"
            role="tooltip"
            className="fixed z-[100] pointer-events-none whitespace-nowrap rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-xs text-gray-900 shadow-lg dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
            style={{
              left: tooltip.left,
              top: tooltip.top,
              transform:
                tooltip.placement === 'above' ? 'translate(-50%, -100%)' : 'translate(-50%, 0)',
            }}
          >
            <span className="font-medium">
              {parseLocalDate(tooltip.day.date)?.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
              })}
            </span>
            <span>: {formatNumber(tooltip.day.steps)} steps</span>
            {tooltip.day.goal_met && (
              <span className="ml-1 text-primary-600 dark:text-primary-400">Goal met</span>
            )}
          </div>,
          globalThis.document.body,
        )}
    </>
  );
}
