import { MapPin, Footprints, Trophy, Navigation, TrendingUp, Flame, Target, Calendar } from 'lucide-react';
import { parseLocalDate } from '../lib/dates';

export function StatsCards({ stats }) {
  if (!stats) return null;

  const totalDistanceMiles = stats.all_time_distance_miles ?? stats.total_distance_miles ?? 0;
  const totalSteps = stats.all_time_steps ?? stats.total_steps ?? 0;
  const avgDailySteps = stats.all_time_avg_daily_steps ?? stats.avg_daily_steps ?? 0;
  const currentStreak = stats.all_time_current_streak ?? stats.current_streak ?? 0;
  const bestDaySteps = stats.all_time_best_day_steps ?? stats.best_day_steps ?? 0;
  const bestDayDate = stats.all_time_best_day_date ?? stats.best_day_date;
  const daysGoalMet = stats.all_time_days_goal_met ?? stats.days_goal_met ?? 0;
  const goalMetPercentage = stats.all_time_goal_met_percentage ?? stats.goal_met_percentage ?? 0;

  const cards = [
    {
      label: 'Total Distance',
      value: `${totalDistanceMiles.toLocaleString()} mi`,
      icon: MapPin,
      color: 'bg-primary-500',
    },
    {
      label: 'Total Steps',
      value: totalSteps.toLocaleString(),
      icon: Footprints,
      color: 'bg-accent-500',
    },
    {
      label: 'Daily Average',
      value: avgDailySteps.toLocaleString(),
      icon: TrendingUp,
      color: 'bg-violet-500',
    },
    {
      label: 'Current Streak',
      value: `${currentStreak} days`,
      icon: Flame,
      color: 'bg-orange-500',
    },
    {
      label: 'Best Day',
      value: bestDaySteps.toLocaleString(),
      subtext: bestDayDate ? parseLocalDate(bestDayDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : null,
      icon: Trophy,
      color: 'bg-amber-500',
    },
    {
      label: 'Goals Met',
      value: `${daysGoalMet}`,
      subtext: goalMetPercentage ? `${goalMetPercentage}%` : null,
      icon: Target,
      color: 'bg-emerald-500',
    },
    {
      label: 'Progress',
      value: `${stats.current_position?.percent_complete?.toFixed(1) || 0}%`,
      icon: Navigation,
      color: 'bg-cyan-500',
    },
    {
      label: 'ETA Boston',
      value: stats.eta_date ? parseLocalDate(stats.eta_date).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }) : '—',
      valueClass: 'text-xl',
      subtext: stats.days_to_boston ? `${stats.days_to_boston} days` : null,
      icon: Calendar,
      color: 'bg-rose-500',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition-all duration-200 cursor-default"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className={`${card.color} p-2 rounded-lg`}>
              <card.icon className="w-5 h-5 text-white" />
            </div>
            <span className="text-sm font-medium text-gray-500 dark:text-gray-400">{card.label}</span>
          </div>
          <p className={`${card.valueClass ?? 'text-2xl'} font-semibold text-gray-900 dark:text-white font-heading`}>
            {card.value}
          </p>
          {card.subtext && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{card.subtext}</p>
          )}
        </div>
      ))}
    </div>
  );
}
