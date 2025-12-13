import { MapPin, Footprints, Trophy, Navigation } from 'lucide-react';

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
      label: 'Total Walks',
      value: stats.total_walks.toLocaleString(),
      icon: Footprints,
      color: 'bg-accent-500',
    },
    {
      label: 'Crossings Completed',
      value: stats.crossings_completed,
      icon: Trophy,
      color: 'bg-amber-500',
    },
    {
      label: 'Progress',
      value: `${stats.current_position.percent_complete.toFixed(1)}%`,
      icon: Navigation,
      color: 'bg-emerald-500',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow duration-200 cursor-default"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className={`${card.color} p-2 rounded-lg`}>
              <card.icon className="w-5 h-5 text-white" />
            </div>
            <span className="text-sm font-medium text-gray-500">{card.label}</span>
          </div>
          <p className="text-2xl font-semibold text-gray-900 font-heading">
            {card.value}
          </p>
        </div>
      ))}
    </div>
  );
}
