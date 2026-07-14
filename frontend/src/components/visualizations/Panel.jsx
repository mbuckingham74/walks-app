export function Panel({ title, subtitle, icon: Icon, children, className = '' }) {
  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden transition-colors duration-200 ${className}`}
    >
      <div className="p-4 border-b border-gray-100 dark:border-gray-700">
        <div className="flex items-center gap-2">
          {Icon && (
            <Icon className="w-5 h-5 text-gray-400 dark:text-gray-500" />
          )}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white font-heading">
              {title}
            </h2>
            {subtitle && (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                {subtitle}
              </p>
            )}
          </div>
        </div>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}
