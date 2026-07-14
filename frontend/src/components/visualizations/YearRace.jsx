import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { GitCompare } from 'lucide-react';
import { Panel } from './Panel';
import { formatNumber, getChartColors } from '../../lib/stats';

function dayOfYearToDate(day, year) {
  const d = new Date(year, 0, day);
  return d.toLocaleDateString('en-US', { month: 'short' });
}

export function YearRace({ data, isDark }) {
  const colors = getChartColors(isDark);
  const previousColor = '#f59e0b';
  const goalColor = isDark ? '#6b7280' : '#9ca3af';

  const { chartData, currentYear, previousYear } = useMemo(() => {
    const current = data?.current ?? [];
    const previous = data?.previous ?? [];
    const goalDaily = data?.goal_daily ?? 15000;
    const cy = data?.current_year ?? new Date().getFullYear();
    const py = data?.previous_year ?? cy - 1;

    const currentMap = new Map(current.map((p) => [p.day_of_year, p.cumulative_steps]));
    const previousMap = new Map(previous.map((p) => [p.day_of_year, p.cumulative_steps]));
    const maxDay = Math.max(
      current.length ? current[current.length - 1].day_of_year : 0,
      previous.length ? previous[previous.length - 1].day_of_year : 0
    );

    const merged = [];
    for (let day = 1; day <= maxDay; day += 1) {
      merged.push({
        day,
        current: currentMap.has(day) ? currentMap.get(day) : undefined,
        previous: previousMap.has(day) ? previousMap.get(day) : undefined,
        goal: goalDaily * day,
      });
    }
    return { chartData: merged, currentYear: cy, previousYear: py };
  }, [data]);

  const hasData = chartData.length > 0;

  return (
    <Panel
      title="Year Race"
      subtitle="Cumulative steps: this year vs last year vs goal pace"
      icon={GitCompare}
    >
      <div className="h-80">
        {!hasData ? (
          <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
            Not enough data for a comparison yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
              <XAxis
                dataKey="day"
                tick={{ fontSize: 12, fill: colors.axis }}
                tickLine={false}
                axisLine={{ stroke: colors.grid }}
                tickFormatter={(v) => dayOfYearToDate(v, currentYear)}
              />
              <YAxis
                tick={{ fontSize: 12, fill: colors.axis }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (!active || !payload) return null;
                  return (
                    <div
                      className="p-3 rounded-lg shadow-lg border"
                      style={{ backgroundColor: colors.tooltipBg, borderColor: colors.tooltipBorder }}
                    >
                      <p style={{ color: colors.tooltipText }} className="text-sm font-medium">
                        {dayOfYearToDate(label, currentYear)} (day {label})
                      </p>
                      {payload.map((p, i) => (
                        p.value !== undefined && (
                          <p key={i} style={{ color: p.color }} className="text-sm">
                            {p.name}: {formatNumber(p.value)}
                          </p>
                        )
                      ))}
                    </div>
                  );
                }}
              />
              <Legend
                formatter={(value) => (
                  <span className="text-xs text-gray-600 dark:text-gray-400">
                    {value === 'current' ? currentYear : value === 'previous' ? previousYear : 'Goal pace'}
                  </span>
                )}
              />
              <Line
                type="monotone"
                dataKey="goal"
                name="goal"
                stroke={goalColor}
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="previous"
                name="previous"
                stroke={previousColor}
                strokeWidth={2}
                dot={false}
                connectNulls
              />
              <Line
                type="monotone"
                dataKey="current"
                name="current"
                stroke={colors.primary}
                strokeWidth={3}
                dot={false}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </Panel>
  );
}
