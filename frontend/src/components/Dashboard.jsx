import { Link } from 'react-router-dom';
import { useStats } from '../hooks/useStats';
import { useSteps } from '../hooks/useSteps';
import { useRoute } from '../hooks/useRoute';
import { useTheme } from '../hooks/useTheme';
import { useConfig } from '../hooks/useConfig';
import { StatsCards } from './StatsCards';
import { RouteMap } from './RouteMap';
import { StepsChart } from './StepsChart';
import { ProgressCard } from './ProgressCard';
import { ROUTE_CONFIG } from '../config';
import { Map, Activity, Sun, Moon, TrendingUp, TrendingDown, Minus, ChevronRight, AlertCircle, BarChart3 } from 'lucide-react';

export function Dashboard() {
  const currentYear = new Date().getFullYear();
  const previousYear = currentYear - 1;

  const { stats, loading: statsLoading, error: statsError } = useStats(currentYear);
  const { stats: previousYearStats, loading: previousYearLoading, error: previousYearError } = useStats(previousYear);
  const { steps, loading: stepsLoading, error: stepsError } = useSteps(`${currentYear}-01-01`, `${currentYear}-12-31`);
  const { route, loading: routeLoading, error: routeError } = useRoute();
  const { config, loading: configLoading, error: configError } = useConfig();
  const { isDark, toggle: toggleTheme } = useTheme();

  const isLoading = statsLoading || previousYearLoading || stepsLoading || routeLoading || configLoading;
  const errors = [statsError, previousYearError, stepsError, routeError, configError].filter(Boolean);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700 transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-primary-500 p-2 rounded-lg">
                <Map className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900 dark:text-white font-heading">
                  Steps Tracker
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">{ROUTE_CONFIG.name}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Link
                to="/stats"
                className="hidden sm:inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-sm font-medium text-gray-700 dark:text-gray-200 transition-colors duration-200"
              >
                <BarChart3 className="w-4 h-4" />
                Stats
              </Link>
              <Link
                to="/stats"
                className="sm:hidden p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
                aria-label="Stats"
              >
                <BarChart3 className="w-5 h-5 text-gray-600 dark:text-gray-300" />
              </Link>
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

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="flex items-center gap-3 text-gray-500 dark:text-gray-400">
              <Activity className="w-5 h-5 animate-pulse" />
              <span>Loading your walking data...</span>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {errors.length > 0 && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                      Unable to load some data
                    </h3>
                    <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                      Some data could not be retrieved. The dashboard may show incomplete information.
                    </p>
                  </div>
                </div>
              </div>
            )}
            {/* Stats cards */}
            <StatsCards stats={stats} />

            {/* Bento grid layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Map - takes 2 columns */}
              <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden transition-colors duration-200">
                <div className="p-4 border-b border-gray-100 dark:border-gray-700">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white font-heading">
                    Route Progress
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {route?.total_distance?.toLocaleString() ?? '—'} miles from {ROUTE_CONFIG.startCity} to {ROUTE_CONFIG.endCity}
                  </p>
                </div>
                <div className="h-[400px]">
                  <RouteMap
                    route={route}
                    currentPosition={stats?.current_position}
                  />
                </div>
              </div>

              {/* Progress card - 1 column */}
              <div className="space-y-6">
                <ProgressCard currentPosition={stats?.current_position} />

                {/* Week comparison */}
                {stats && (
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200">
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
                      This Week vs Last Week
                    </h3>
                    <div className="flex items-center gap-3 mb-3">
                      {stats.week_comparison !== null ? (
                        <>
                          {stats.week_comparison > 0 ? (
                            <div className="bg-emerald-100 dark:bg-emerald-900/30 p-2 rounded-lg">
                              <TrendingUp className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                            </div>
                          ) : stats.week_comparison < 0 ? (
                            <div className="bg-red-100 dark:bg-red-900/30 p-2 rounded-lg">
                              <TrendingDown className="w-5 h-5 text-red-600 dark:text-red-400" />
                            </div>
                          ) : (
                            <div className="bg-gray-100 dark:bg-gray-700 p-2 rounded-lg">
                              <Minus className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                            </div>
                          )}
                          <span className={`text-2xl font-semibold font-heading ${
                            stats.week_comparison > 0
                              ? 'text-emerald-600 dark:text-emerald-400'
                              : stats.week_comparison < 0
                              ? 'text-red-600 dark:text-red-400'
                              : 'text-gray-900 dark:text-white'
                          }`}>
                            {stats.week_comparison > 0 ? '+' : ''}{stats.week_comparison}%
                          </span>
                        </>
                      ) : (
                        <span className="text-gray-500 dark:text-gray-400">No data yet</span>
                      )}
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">This week</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {stats.this_week_steps?.toLocaleString() || 0} steps
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Last week</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {stats.last_week_steps?.toLocaleString() || 0} steps
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* All-time progress */}
                {stats && (
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200">
                    <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                      All-Time Progress
                    </h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Total steps</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {stats.all_time_steps?.toLocaleString() || 0}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Total distance</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {stats.all_time_distance_miles?.toLocaleString() || 0} mi
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Miles remaining</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {stats.miles_remaining?.toLocaleString() || 0} mi
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Steps to Boston</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {stats.steps_to_boston?.toLocaleString() || 0}
                        </span>
                      </div>
                      {stats.crossings_completed > 0 && (
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">America crossings</span>
                          <span className="font-medium text-primary-600 dark:text-primary-400">
                            {stats.crossings_completed}x
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Year-by-year breakdown */}
                <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 transition-colors duration-200">
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">
                    Year-by-Year
                  </h3>
                  <div className="space-y-3">
                    {/* Current year */}
                    {stats && (
                      <Link
                        to={`/${currentYear}`}
                        className="block p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-gray-900 dark:text-white">{currentYear}</span>
                          <ChevronRight className="w-4 h-4 text-gray-400" />
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600 dark:text-gray-400">
                            {stats.total_steps?.toLocaleString() || 0} steps
                          </span>
                          <span className="text-gray-600 dark:text-gray-400">
                            {stats.total_days} days
                          </span>
                        </div>
                      </Link>
                    )}
                    {/* Previous year */}
                    {previousYearStats && (
                      <Link
                        to={`/${previousYear}`}
                        className="block p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-gray-900 dark:text-white">{previousYear}</span>
                          <ChevronRight className="w-4 h-4 text-gray-400" />
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600 dark:text-gray-400">
                            {previousYearStats.total_steps?.toLocaleString() || 0} steps
                          </span>
                          <span className="text-gray-600 dark:text-gray-400">
                            {previousYearStats.total_days} days
                          </span>
                        </div>
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Steps chart */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden transition-colors duration-200">
              <div className="p-4 border-b border-gray-100 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white font-heading">
                  Daily Steps
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Track your daily step count and goal progress
                </p>
              </div>
              <div className="h-[300px] p-4">
                <StepsChart steps={steps} isDark={isDark} dailyGoal={config.daily_goal} />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 mt-8 transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-sm text-gray-400 dark:text-gray-500 text-center">
            Data synced from Apple Health via iOS Shortcut
          </p>
        </div>
      </footer>
    </div>
  );
}
