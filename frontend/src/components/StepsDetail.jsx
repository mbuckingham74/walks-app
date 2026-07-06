import { useMemo } from 'react';
import { Link, Navigate, useParams } from 'react-router-dom';
import { useConfig } from '../hooks/useConfig';
import { useSteps } from '../hooks/useSteps';
import { useTheme } from '../hooks/useTheme';
import { ArrowLeft, Sun, Moon, Activity, Calendar, Footprints, MapPin } from 'lucide-react';
import { parseLocalDate, formatDate } from '../lib/dates';

export function StepsDetail() {
  const { year: yearParam } = useParams();
  const isValidYear = /^\d{4}$/.test(yearParam ?? '');
  const year = isValidYear ? Number.parseInt(yearParam, 10) : new Date().getFullYear();
  const { steps, loading: stepsLoading, error: stepsError } = useSteps(
    `${year}-01-01`,
    `${year}-12-31`
  );
  const { config, loading: configLoading, error: configError } = useConfig();
  const { isDark, toggle: toggleTheme } = useTheme();

  if (!isValidYear) {
    return <Navigate to="/" replace />;
  }

  const sortedSteps = useMemo(
    () =>
      [...steps].sort(
        (a, b) => parseLocalDate(b.step_date) - parseLocalDate(a.step_date)
      ),
    [steps]
  );
  const totalSteps = useMemo(
    () => sortedSteps.reduce((sum, day) => sum + day.steps, 0),
    [sortedSteps]
  );
  const totalMiles = totalSteps / config.steps_per_mile;
  const loading = stepsLoading || configLoading;
  const error = stepsError || configError;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      <header className="bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700 transition-colors duration-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link
                to="/"
                className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-300" />
              </Link>
              <div>
                <h1 className="text-xl font-semibold text-gray-900 dark:text-white font-heading">
                  {year} Steps Detail
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Daily breakdown of your walking progress
                </p>
              </div>
            </div>
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
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="flex items-center gap-3 text-gray-500 dark:text-gray-400">
              <Activity className="w-5 h-5 animate-pulse" />
              <span>Loading steps data...</span>
            </div>
          </div>
        ) : error ? (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 text-red-700 dark:text-red-400">
            Error loading data: {error}
          </div>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-1">
                  <Calendar className="w-4 h-4" />
                  <span className="text-sm font-medium">Days Tracked</span>
                </div>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
                  {sortedSteps.length}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-1">
                  <Footprints className="w-4 h-4" />
                  <span className="text-sm font-medium">Total Steps</span>
                </div>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
                  {totalSteps.toLocaleString()}
                </p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-1">
                  <MapPin className="w-4 h-4" />
                  <span className="text-sm font-medium">Total Distance</span>
                </div>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
                  {totalMiles.toFixed(1)} mi
                </p>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-100 dark:border-gray-700">
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Steps
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Distance
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Goal
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                    {sortedSteps.length === 0 ? (
                      <tr>
                        <td
                          colSpan="4"
                          className="px-6 py-8 text-sm text-center text-gray-500 dark:text-gray-400"
                        >
                          No step data recorded for {year} yet.
                        </td>
                      </tr>
                    ) : (
                      sortedSteps.map((day) => {
                        const miles = day.steps / config.steps_per_mile;
                        const metGoal = day.steps >= config.daily_goal;

                        return (
                          <tr
                            key={day.step_date}
                            className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                          >
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {formatDate(day.step_date)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900 dark:text-white">
                              {day.steps.toLocaleString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-600 dark:text-gray-400">
                              {miles.toFixed(2)} mi
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-center">
                              {metGoal ? (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 dark:bg-emerald-900/30 text-emerald-800 dark:text-emerald-400">
                                  Met
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                                  —
                                </span>
                              )}
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
