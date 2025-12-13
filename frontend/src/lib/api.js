const API_BASE = import.meta.env.VITE_API_URL || '/api';

async function fetchAPI(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Stats
  getStats: (year) => fetchAPI(year ? `/stats?year=${year}` : '/stats'),

  // Steps
  getSteps: (start, end) => {
    const params = new URLSearchParams();
    if (start) params.append('start', start);
    if (end) params.append('end', end);
    return fetchAPI(`/steps?${params}`);
  },

  // Activities
  getActivities: (year, limit = 50) => {
    const params = new URLSearchParams();
    if (year) params.append('year', year);
    params.append('limit', limit);
    return fetchAPI(`/activities?${params}`);
  },

  // Route
  getRoute: () => fetchAPI('/route'),

  // Sync
  triggerSync: () => fetchAPI('/sync', { method: 'POST' }),
  triggerActivitiesSync: () => fetchAPI('/sync/activities', { method: 'POST' }),
  triggerStepsSync: () => fetchAPI('/sync/steps', { method: 'POST' }),
  getSyncStatus: () => fetchAPI('/sync/status'),
};
