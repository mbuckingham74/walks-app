import { useState, useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

const DATE_RANGES = [
  { label: 'Week', value: 7 },
  { label: 'Month', value: 30 },
  { label: 'Year', value: 365 },
  { label: 'All', value: null },
];

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;
  const metGoal = data.steps >= data.goal;

  return (
    <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-100">
      <p className="text-sm font-medium text-gray-900">{label}</p>
      <p className="text-lg font-semibold text-primary-600">
        {data.steps.toLocaleString()} steps
      </p>
      <p className="text-xs text-gray-500">
        Goal: {data.goal.toLocaleString()}
        {metGoal && <span className="ml-1 text-primary-500">Met!</span>}
      </p>
    </div>
  );
}

export function StepsChart({ steps }) {
  const [range, setRange] = useState(30);

  const chartData = useMemo(() => {
    if (!steps || steps.length === 0) return [];

    let filtered = steps;
    if (range !== null) {
      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() - range);
      filtered = steps.filter(s => new Date(s.step_date) >= cutoff);
    }

    return filtered.map(s => ({
      date: new Date(s.step_date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
      steps: s.steps,
      goal: s.goal,
    }));
  }, [steps, range]);

  const avgGoal = useMemo(() => {
    if (chartData.length === 0) return 10000;
    const sum = chartData.reduce((acc, d) => acc + d.goal, 0);
    return Math.round(sum / chartData.length);
  }, [chartData]);

  if (!steps || steps.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-gray-500">No step data available</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Range selector */}
      <div className="flex gap-2 mb-4">
        {DATE_RANGES.map(({ label, value }) => (
          <button
            key={label}
            onClick={() => setRange(value)}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors duration-200 cursor-pointer ${
              range === value
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="stepsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#16a34a" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#16a34a" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12, fill: '#6b7280' }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              tick={{ fontSize: 12, fill: '#6b7280' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              y={avgGoal}
              stroke="#9ca3af"
              strokeDasharray="5 5"
              label={{
                value: 'Goal',
                position: 'right',
                fill: '#9ca3af',
                fontSize: 12,
              }}
            />
            <Area
              type="monotone"
              dataKey="steps"
              stroke="#16a34a"
              strokeWidth={2}
              fill="url(#stepsGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
