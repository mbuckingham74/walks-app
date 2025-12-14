import { MapPin, Footprints, Trophy, Navigation, TrendingUp, Flame, Target, Calendar } from 'lucide-react';

export function StatsCards({ stats }) {
  if (!stats) return null;

  const cards = [
    {
      label: 'Total Distance',
      value: `${stats.total_distance_miles.toLocaleString()} mi`,
      icon: MapPin,
      color: 'bg-primary-500',
    },
    {
      label: 'Total Steps',
      value: stats.total_steps?.toLocaleString() || '0',
      icon: Footprints,
      color: 'bg-accent-500',
    },
    {
      label: 'Daily Average',
      value: stats.avg_daily_steps?.toLocaleString() || '0',
      icon: TrendingUp,
      color: 'bg-violet-500',
    },
    {
      label: 'Current Streak',
      value: `${stats.current_streak || 0} days`,
      icon: Flame,
      color: 'bg-orange-500',
    },
    {
      label: 'Best Day',
      value: stats.best_day_steps?.toLocaleString() || '0',
      subtext: stats.best_day_date ? new Date(stats.best_day_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : null,
      icon: Trophy,
      color: 'bg-amber-500',
    },
    {
      label: 'Goals Met',
      value: `${stats.days_goal_met || 0}`,
      subtext: stats.goal_met_percentage ? `${stats.goal_met_percentage}%` : null,
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
      value: stats.eta_date ? new Date(stats.eta_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : '—',
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
          <p className="text-2xl font-semibold text-gray-900 dark:text-white font-heading">
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
