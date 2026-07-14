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
import { Activity } from 'lucide-react';
import { Panel } from './Panel';
import { formatNumber, getChartColors, formatMediumDate } from '../../lib/stats';
import { parseLocalDate } from '../../lib/dates';

export function Momentum({ data, isDark }) {
  const colors = getChartColors(isDark);
  const avg7Color = '#3b82f6';
  const avg28Color = '#8b5cf6';
  const stepsColor = isDark ? '#4b5563' : '#d1d5db';

  const chartData = useMemo(() => {
    const items = data ?? [];
    return items.map((p) => ({
      date: p.date,
      steps: p.steps ?? 0,
      avg_7: p.avg_7,
      avg_28: p.avg_28,
    }));
  }, [data]);

  const hasData = chartData.length > 0;

  return (
    <Panel
      title="Momentum"
      subtitle="Daily steps with 7-day and 28-day rolling averages"
      icon={Activity}
    >
      <div className="h-72">
        {!hasData ? (
          <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
            No momentum data yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: colors.axis }}
                tickLine={false}
                axisLine={{ stroke: colors.grid }}
                minTickGap={32}
                tickFormatter={(v) => {
                  const d = parseLocalDate(v);
                  return d ? d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
                }}
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
                        {formatMediumDate(label)}
                      </p>
                      {payload.map((p, i) => (
                        p.value !== null && p.value !== undefined && (
                          <p key={i} style={{ color: p.color }} className="text-sm">
                            {p.name === 'steps' ? 'Steps' : p.name === 'avg_7' ? '7-day avg' : '28-day avg'}: {formatNumber(p.value)}
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
                    {value === 'steps' ? 'Daily' : value === 'avg_7' ? '7-day avg' : '28-day avg'}
                  </span>
                )}
              />
              <Line type="monotone" dataKey="steps" name="steps" stroke={stepsColor} strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="avg_7" name="avg_7" stroke={avg7Color} strokeWidth={2} dot={false} connectNulls />
              <Line type="monotone" dataKey="avg_28" name="avg_28" stroke={avg28Color} strokeWidth={2.5} dot={false} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </Panel>
  );
}
