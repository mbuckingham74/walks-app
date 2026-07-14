import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import { BarChart3 } from 'lucide-react';
import { Panel } from './Panel';
import { formatNumber, getChartColors } from '../../lib/stats';
import { parseLocalDate } from '../../lib/dates';

const POSITIVE_COLOR = '#16a34a';
const NEGATIVE_COLOR = '#ef4444';
const WINDOW = 30;

export function GoalSurplus({ data, isDark }) {
  const colors = getChartColors(isDark);

  const chartData = useMemo(() => {
    const items = (data ?? []).slice(-WINDOW);
    return items.map((p) => ({
      date: p.date,
      surplus: p.surplus,
    }));
  }, [data]);

  const hasData = chartData.length > 0;
  const maxAbs = useMemo(
    () => Math.max(1000, ...chartData.map((d) => Math.abs(d.surplus))),
    [chartData]
  );

  return (
    <Panel
      title="Goal Surplus"
      subtitle="Steps above (green) or below (red) the daily goal"
      icon={BarChart3}
    >
      <div className="h-72">
        {!hasData ? (
          <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
            No surplus data yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fill: colors.axis }}
                tickLine={false}
                axisLine={{ stroke: colors.grid }}
                minTickGap={20}
                tickFormatter={(v) => {
                  const d = parseLocalDate(v);
                  return d ? d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
                }}
              />
              <YAxis
                tick={{ fontSize: 11, fill: colors.axis }}
                tickLine={false}
                axisLine={false}
                domain={[-maxAbs, maxAbs]}
                tickFormatter={(v) => `${v >= 0 ? '+' : ''}${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (!active || !payload || !payload.length) return null;
                  const v = payload[0].value;
                  return (
                    <div
                      className="p-3 rounded-lg shadow-lg border"
                      style={{ backgroundColor: colors.tooltipBg, borderColor: colors.tooltipBorder }}
                    >
                      <p style={{ color: colors.tooltipText }} className="text-sm font-medium">
                        {parseLocalDate(label)?.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </p>
                      <p style={{ color: v >= 0 ? POSITIVE_COLOR : NEGATIVE_COLOR }} className="text-sm">
                        {v >= 0 ? '+' : ''}{formatNumber(v)} steps vs goal
                      </p>
                    </div>
                  );
                }}
              />
              <ReferenceLine y={0} stroke={colors.axis} strokeWidth={1} />
              <Bar dataKey="surplus" radius={[2, 2, 0, 0]}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={entry.surplus >= 0 ? POSITIVE_COLOR : NEGATIVE_COLOR} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
      {chartData.length < (data?.length ?? 0) && (
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
          Showing the most recent {WINDOW} days
        </p>
      )}
    </Panel>
  );
}
