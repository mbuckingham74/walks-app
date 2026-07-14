import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  Cell,
} from 'recharts';
import {
  ArrowLeft,
  Sun,
  Moon,
  Activity,
  AlertCircle,
  Calendar,
  Trophy,
  Flame,
  Target,
  Footprints,
  MapPin,
  TrendingUp,
  BarChart3,
  RotateCcw,
} from 'lucide-react';
import { useDetailedStats } from '../hooks/useDetailedStats';
import { useConfig } from '../hooks/useConfig';
import { useTheme } from '../hooks/useTheme';
import {
  formatNumber,
  formatShortDate,
  formatMediumDate,
  formatMonthYear,
  getChartColors,
} from '../lib/stats';
import { ActivityCalendar } from './visualizations/ActivityCalendar';
import { YearRace } from './visualizations/YearRace';
import { Momentum } from './visualizations/Momentum';
import { RecordChase } from './visualizations/RecordChase';
import { WeeklyFinishLine } from './visualizations/WeeklyFinishLine';
import { GoalSurplus } from './visualizations/GoalSurplus';
import { RollingRecords } from './visualizations/RollingRecords';
import { DayPercentile } from './visualizations/DayPercentile';
import { MilestoneTimeline } from './visualizations/MilestoneTimeline';
import { PerfectPeriods } from './visualizations/PerfectPeriods';
import { ComebackScore } from './visualizations/ComebackScore';

const AVAILABLE_YEARS = [2026, 2025, 2024, 2023];

function ChartTooltip({ active, payload, label, isDark }) {
  if (!active || !payload || !payload.length) return null;
  const colors = getChartColors(isDark);
  return (
    <div
      className="p-3 rounded-lg shadow-lg border"
      style={{
        backgroundColor: colors.tooltipBg,
        borderColor: colors.tooltipBorder,
      }}
    >
      <p style={{ color: colors.tooltipText }} className="text-sm font-medium">
        {label}
      </p>
      <p style={{ color: colors.primary }} className="text-lg font-semibold">
        {formatNumber(payload[0].value)}
      </p>
    </div>
  );
}

function Section({ title, subtitle, children }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden transition-colors duration-200">
      <div className="p-4 border-b border-gray-100 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white font-heading">
          {title}
        </h2>
        {subtitle && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{subtitle}</p>
        )}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function StatCard({ label, value, subtext, icon: Icon, colorClass }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200">
      <div className="flex items-center gap-3 mb-3">
        <div className={`${colorClass} p-2 rounded-lg`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <span className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</span>
      </div>
      <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
        {value}
      </p>
      {subtext && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{subtext}</p>
      )}
    </div>
  );
}

function LeaderboardTable({ items, columns, emptyText }) {
  if (!items || items.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">{emptyText}</div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            {columns.map((col) => (
              <th key={col.key} className={`pb-2 ${col.className || ''}`}>
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
          {items.map((item, index) => (
            <tr key={index} className="text-sm">
              {columns.map((col) => (
                <td key={col.key} className={`py-3 ${col.className || ''}`}>
                  {col.render(item)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ErrorState({ message, onRetry }) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-red-800 dark:text-red-200">
                Couldn&apos;t load stats
              </h2>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                {message || 'Something went wrong while loading your detailed statistics.'}
              </p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors cursor-pointer"
                >
                  <RotateCcw className="w-4 h-4" />
                  Try again
                </button>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export function StatsPage() {
  const currentYear = new Date().getFullYear();
  const [selectedYear, setSelectedYear] = useState(currentYear);
  const { stats, loading, error, refetch } = useDetailedStats(selectedYear);
  const { config } = useConfig();
  const { isDark, toggle: toggleTheme } = useTheme();
  const colors = useMemo(() => getChartColors(isDark), [isDark]);

  const data = useMemo(() => stats || null, [stats]);

  const yearOptions = useMemo(() => {
    const years = new Set([...AVAILABLE_YEARS, currentYear, currentYear - 1]);
    return Array.from(years).sort((a, b) => b - a);
  }, [currentYear]);

  if (error && !data) {
    return <ErrorState message={error} onRetry={refetch} />;
  }

  const summary = data?.year_summary || null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700 transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Link
                to="/"
                className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-300" />
              </Link>
              <div>
                <h1 className="text-xl font-semibold text-gray-900 dark:text-white font-heading">
                  Stats
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Deep dive into your walking data
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(Number(e.target.value))}
                className="block w-full rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm py-2 pl-3 pr-8 focus:border-primary-500 focus:ring-primary-500"
                aria-label="Select year"
              >
                {yearOptions.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200 cursor-pointer"
                aria-label="Toggle dark mode"
              >
                {isDark ? (
                  <Sun className="w-5 h-5 text-amber-500" />
                ) : (
                  <Moon className="w-5 h-5 text-gray-600" />
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {loading && !data && (
          <div className="flex items-center justify-center h-64">
            <div className="flex items-center gap-3 text-gray-500 dark:text-gray-400">
              <Activity className="w-5 h-5 animate-pulse" />
              <span>Loading detailed stats...</span>
            </div>
          </div>
        )}

        {error && data && (
          <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Stats refresh failed
                </h3>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
              </div>
              <button
                onClick={refetch}
                className="text-sm text-red-700 dark:text-red-300 hover:text-red-800 dark:hover:text-red-200 font-medium"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {data && (
          <div className="space-y-6">
            {/* Year summary cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                label="Total Steps"
                value={formatNumber(summary?.total_steps)}
                subtext={`${formatNumber(summary?.total_miles)} mi`}
                icon={Footprints}
                colorClass="bg-primary-500"
              />
              <StatCard
                label="Daily Average"
                value={formatNumber(summary?.avg_daily_steps)}
                icon={TrendingUp}
                colorClass="bg-violet-500"
              />
              <StatCard
                label="Best Day"
                value={formatNumber(summary?.best_single_day_steps)}
                subtext={formatShortDate(summary?.best_single_day_date)}
                icon={Trophy}
                colorClass="bg-amber-500"
              />
              <StatCard
                label="Goals Met"
                value={formatNumber(summary?.goal_met_days)}
                subtext={`${summary?.goal_met_percentage ?? 0}%`}
                icon={Target}
                colorClass="bg-emerald-500"
              />
            </div>

            {/* Activity calendar */}
            <ActivityCalendar data={data.activity_calendar} dailyGoal={config.daily_goal} />

            {/* Today motivators */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <RecordChase data={data.record_chase} />
              <DayPercentile data={data.day_percentile} />
              <WeeklyFinishLine data={data.weekly_finish_line} />
              <ComebackScore data={data.comeback_score} />
            </div>

            {/* Leaderboards */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Section title="Top 10 Days" subtitle="Highest single-day step counts">
                <LeaderboardTable
                  items={data.top_days}
                  emptyText="No step data recorded yet."
                  columns={[
                    {
                      key: 'rank',
                      label: '#',
                      className: 'w-10 text-gray-500 dark:text-gray-400',
                      render: (item) => item.rank,
                    },
                    {
                      key: 'date',
                      label: 'Date',
                      render: (item) => (
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">
                            {formatMediumDate(item.date)}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {item.miles} mi
                          </div>
                        </div>
                      ),
                    },
                    {
                      key: 'steps',
                      label: 'Steps',
                      className: 'text-right font-semibold text-gray-900 dark:text-white',
                      render: (item) => formatNumber(item.steps),
                    },
                  ]}
                />
              </Section>

              <Section title="Top 5 Weeks" subtitle="Best weekly totals">
                <LeaderboardTable
                  items={data.top_weeks}
                  emptyText="No weekly data available."
                  columns={[
                    {
                      key: 'rank',
                      label: '#',
                      className: 'w-10 text-gray-500 dark:text-gray-400',
                      render: (item) => item.rank,
                    },
                    {
                      key: 'week',
                      label: 'Week',
                      render: (item) => (
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">
                            Week {item.week}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {formatShortDate(item.start_date)} – {formatShortDate(item.end_date)}
                          </div>
                        </div>
                      ),
                    },
                    {
                      key: 'steps',
                      label: 'Steps',
                      className: 'text-right font-semibold text-gray-900 dark:text-white',
                      render: (item) => formatNumber(item.total_steps),
                    },
                  ]}
                />
              </Section>

              <Section title="Top 5 Months" subtitle="Best monthly totals">
                <LeaderboardTable
                  items={data.top_months}
                  emptyText="No monthly data available."
                  columns={[
                    {
                      key: 'rank',
                      label: '#',
                      className: 'w-10 text-gray-500 dark:text-gray-400',
                      render: (item) => item.rank,
                    },
                    {
                      key: 'month',
                      label: 'Month',
                      render: (item) => (
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">
                            {item.month_name}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {item.days_tracked} days tracked
                          </div>
                        </div>
                      ),
                    },
                    {
                      key: 'steps',
                      label: 'Steps',
                      className: 'text-right font-semibold text-gray-900 dark:text-white',
                      render: (item) => formatNumber(item.total_steps),
                    },
                  ]}
                />
              </Section>
            </div>

            {/* Year race */}
            <YearRace data={data.year_race} isDark={isDark} />

            {/* Momentum */}
            <Momentum data={data.momentum} isDark={isDark} />

            {/* Charts row 1 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Section title="Best Day of Week" subtitle="Average steps by weekday">
                <div className="h-72">
                  {data.day_of_week_breakdown.some((d) => d.count > 0) ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data.day_of_week_breakdown} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                        <XAxis
                          dataKey="day"
                          tick={{ fontSize: 12, fill: colors.axis }}
                          tickLine={false}
                          axisLine={{ stroke: colors.grid }}
                        />
                        <YAxis
                          tick={{ fontSize: 12, fill: colors.axis }}
                          tickLine={false}
                          axisLine={false}
                          tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                        />
                        <Tooltip content={<ChartTooltip isDark={isDark} />} />
                        <Bar dataKey="avg_steps" radius={[4, 4, 0, 0]}>
                          {data.day_of_week_breakdown.map((entry) => (
                            <Cell
                              key={entry.day}
                              fill={entry.day === data.best_day_of_week?.day ? colors.primary : '#9ca3af'}
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
                      No data available
                    </div>
                  )}
                </div>
              </Section>

              <Section title="Steps Distribution" subtitle="How your daily step counts cluster">
                <div className="h-72">
                  {data.steps_distribution.some((b) => b.count > 0) ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data.steps_distribution} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                        <XAxis
                          dataKey="label"
                          tick={{ fontSize: 12, fill: colors.axis }}
                          tickLine={false}
                          axisLine={{ stroke: colors.grid }}
                        />
                        <YAxis
                          tick={{ fontSize: 12, fill: colors.axis }}
                          tickLine={false}
                          axisLine={false}
                        />
                        <Tooltip content={<ChartTooltip isDark={isDark} />} />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                          {data.steps_distribution.map((entry) => (
                            <Cell key={entry.label} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
                      No data available
                    </div>
                  )}
                </div>
              </Section>
            </div>

            {/* Charts row 2 */}
            <Section title="Monthly Totals" subtitle="Steps and goal-met days per month">
              <div className="h-80">
                {data.monthly_totals.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.monthly_totals} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                      <XAxis
                        dataKey="month_name"
                        tick={{ fontSize: 12, fill: colors.axis }}
                        tickLine={false}
                        axisLine={{ stroke: colors.grid }}
                      />
                      <YAxis
                        yAxisId="left"
                        tick={{ fontSize: 12, fill: colors.axis }}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                      />
                      <YAxis
                        yAxisId="right"
                        orientation="right"
                        tick={{ fontSize: 12, fill: colors.axis }}
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip
                        content={({ active, payload, label }) => {
                          if (!active || !payload) return null;
                          return (
                            <div
                              className="p-3 rounded-lg shadow-lg border"
                              style={{
                                backgroundColor: colors.tooltipBg,
                                borderColor: colors.tooltipBorder,
                              }}
                            >
                              <p style={{ color: colors.tooltipText }} className="text-sm font-medium">
                                {label}
                              </p>
                              {payload.map((p, i) => (
                                <p key={i} style={{ color: p.color }} className="text-sm">
                                  {p.name}: {formatNumber(p.value)}
                                </p>
                              ))}
                            </div>
                          );
                        }}
                      />
                      <Bar
                        yAxisId="left"
                        dataKey="total_steps"
                        name="Steps"
                        fill={colors.primary}
                        radius={[4, 4, 0, 0]}
                      />
                      <Bar
                        yAxisId="right"
                        dataKey="goal_met_days"
                        name="Goal met days"
                        fill={colors.primaryFill}
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
                    No monthly data available
                  </div>
                )}
              </div>
            </Section>

            {/* Goal surplus */}
            <GoalSurplus data={data.goal_surplus} isDark={isDark} />

            <Section title="Cumulative Steps" subtitle="Total steps accumulated over the year">
              <div className="h-80">
                {data.cumulative_data.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data.cumulative_data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="cumulativeGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={colors.primary} stopOpacity={0.2} />
                          <stop offset="95%" stopColor={colors.primary} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12, fill: colors.axis }}
                        tickLine={false}
                        axisLine={{ stroke: colors.grid }}
                        tickFormatter={(value) => {
                          const d = new Date(value + 'T00:00:00');
                          return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
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
                          if (!active || !payload || !payload.length) return null;
                          const point = payload[0].payload;
                          return (
                            <div
                              className="p-3 rounded-lg shadow-lg border"
                              style={{
                                backgroundColor: colors.tooltipBg,
                                borderColor: colors.tooltipBorder,
                              }}
                            >
                              <p style={{ color: colors.tooltipText }} className="text-sm font-medium">
                                {formatMediumDate(label)}
                              </p>
                              <p style={{ color: colors.primary }} className="text-lg font-semibold">
                                {formatNumber(point.cumulative_steps)} steps
                              </p>
                              <p style={{ color: colors.axis }} className="text-xs">
                                {formatNumber(point.cumulative_miles)} mi total
                              </p>
                            </div>
                          );
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="cumulative_steps"
                        stroke={colors.primary}
                        strokeWidth={2}
                        fill="url(#cumulativeGradient)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-gray-500 dark:text-gray-400 text-sm">
                    No cumulative data available
                  </div>
                )}
              </div>
            </Section>

            {/* Rolling records */}
            <RollingRecords data={data.rolling_records} />

            {/* Perfect periods */}
            <PerfectPeriods data={data.perfect_periods} />

            {/* Insight cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200">
                <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-3">
                  <Calendar className="w-5 h-5" />
                  <h3 className="text-sm font-medium">Best Day of Week</h3>
                </div>
                {data.best_day_of_week ? (
                  <div>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
                      {data.best_day_of_week.day}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {formatNumber(data.best_day_of_week.avg_steps)} avg steps
                    </p>
                  </div>
                ) : (
                  <p className="text-gray-500 dark:text-gray-400 text-sm">No data</p>
                )}
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200">
                <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-3">
                  <Flame className="w-5 h-5" />
                  <h3 className="text-sm font-medium">Longest Streak</h3>
                </div>
                {data.longest_streak ? (
                  <div>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
                      {data.longest_streak.length} days
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {formatShortDate(data.longest_streak.start_date)} –{' '}
                      {formatShortDate(data.longest_streak.end_date)}
                    </p>
                  </div>
                ) : (
                  <p className="text-gray-500 dark:text-gray-400 text-sm">No streaks yet</p>
                )}
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200">
                <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-3">
                  <MapPin className="w-5 h-5" />
                  <h3 className="text-sm font-medium">Peak Month</h3>
                </div>
                {data.peak_month ? (
                  <div>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
                      {formatMonthYear(data.peak_month.month, data.peak_month.year)}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {formatNumber(data.peak_month.total_steps)} steps
                    </p>
                  </div>
                ) : (
                  <p className="text-gray-500 dark:text-gray-400 text-sm">No data</p>
                )}
              </div>
            </div>

            {/* Milestone timeline */}
            <MilestoneTimeline data={data.milestone_timeline} />

            {/* Consistency */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                  <BarChart3 className="w-5 h-5" />
                  <h3 className="text-sm font-medium">Consistency</h3>
                </div>
                <span className="text-sm font-semibold text-gray-900 dark:text-white">
                  {data.consistency?.percentage ?? 0}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
                <div
                  className="bg-primary-500 h-2.5 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(data.consistency?.percentage ?? 0, 100)}%` }}
                />
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                Tracked {formatNumber(data.consistency?.days_tracked)} of{' '}
                {formatNumber(data.consistency?.days_in_period)} days so far
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
