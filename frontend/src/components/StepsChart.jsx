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
  { label: 'Month', value: 'month' },
  { label: 'Last 30', value: 30 },
  { label: 'Year', value: 365 },
  { label: 'All', value: null },
];

const DEFAULT_DAILY_GOAL = 15000;

function CustomTooltip({ active, payload, label, dailyGoal }) {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;
  const steps = data.steps ?? 0;
  const goal = data.goal ?? dailyGoal;
  const metGoal = steps >= goal;

  return (
    <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-100 dark:border-gray-700">
      <p className="text-sm font-medium text-gray-900 dark:text-white">{label}</p>
      <p className="text-lg font-semibold text-primary-600 dark:text-primary-400">
        {steps.toLocaleString()} steps
      </p>
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Goal: {goal.toLocaleString()}
        {metGoal && <span className="ml-1 text-primary-500 dark:text-primary-400">Met!</span>}
      </p>
    </div>
  );
}

export function StepsChart({ steps, isDark = false, dailyGoal = DEFAULT_DAILY_GOAL }) {
  const [range, setRange] = useState(30);

  // Theme-aware colors for Recharts
  const chartColors = {
    grid: isDark ? '#374151' : '#e5e7eb',
    axis: isDark ? '#9ca3af' : '#6b7280',
    reference: isDark ? '#6b7280' : '#9ca3af',
  };

  const chartData = useMemo(() => {
    // Create a map of existing step data by date string
    const stepsMap = new Map();
    if (steps && steps.length > 0) {
      steps.forEach(s => {
        const dateKey = s.step_date; // YYYY-MM-DD format from API
        stepsMap.set(dateKey, {
          steps: s.steps ?? 0,
          goal: s.goal ?? dailyGoal,
        });
      });
    }

    // Helper to format date as YYYY-MM-DD in local timezone (not UTC)
    const toLocalDateString = (d) => {
      const year = d.getFullYear();
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    };

    // Determine date range
    const today = new Date();
    let startDate, endDate;

    if (range === null) {
      // "All" - show all data from earliest to latest date in dataset
      if (steps && steps.length > 0) {
        const dates = steps.map(s => new Date(s.step_date + 'T00:00:00'));
        startDate = new Date(Math.min(...dates));
        endDate = new Date(Math.max(...dates));
        // Extend to today if data exists beyond
        if (today > endDate) {
          endDate = new Date(today);
        }
      } else {
        // Fallback to current year if no data
        startDate = new Date(today.getFullYear(), 0, 1);
        endDate = new Date(today.getFullYear(), 11, 31);
      }
    } else if (range === 365) {
      // "Year" - show full current year
      startDate = new Date(today.getFullYear(), 0, 1);
      endDate = new Date(today.getFullYear(), 11, 31);
    } else if (range === 'month') {
      // "Month" - current calendar month (1st to last day)
      startDate = new Date(today.getFullYear(), today.getMonth(), 1);
      endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0); // Last day of month
    } else {
      // Week or Last 30 - show just that range from today backwards
      endDate = new Date(today);
      startDate = new Date(today);
      startDate.setDate(startDate.getDate() - range);
    }

    // Generate all dates in range using local timezone
    const result = [];
    const current = new Date(startDate);
    while (current <= endDate) {
      const dateKey = toLocalDateString(current);
      const data = stepsMap.get(dateKey);
      result.push({
        date: current.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        }),
        steps: data?.steps ?? 0,
        goal: data?.goal ?? dailyGoal,
      });
      current.setDate(current.getDate() + 1);
    }

    return result;
  }, [steps, range, dailyGoal]);

  const avgGoal = useMemo(() => {
    if (chartData.length === 0) return dailyGoal;
    const sum = chartData.reduce((acc, d) => acc + d.goal, 0);
    return Math.round(sum / chartData.length);
  }, [chartData]);

  if (!steps || steps.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-gray-500 dark:text-gray-400">No step data available</p>
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
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
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
            <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12, fill: chartColors.axis }}
              tickLine={false}
              axisLine={{ stroke: chartColors.grid }}
            />
            <YAxis
              tick={{ fontSize: 12, fill: chartColors.axis }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomTooltip dailyGoal={dailyGoal} />} />
            <ReferenceLine
              y={avgGoal}
              stroke={chartColors.reference}
              strokeDasharray="5 5"
              label={{
                value: 'Goal',
                position: 'right',
                fill: chartColors.reference,
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
