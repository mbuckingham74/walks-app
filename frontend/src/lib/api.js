const API_BASE = import.meta.env.VITE_API_URL || '/api';

async function fetchAPI(endpoint, options = {}) {
  const { headers, ...restOptions } = options;
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    ...restOptions,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }

  // Use text() to safely handle empty bodies (Content-Length unreliable with CORS)
  const text = await response.text();
  if (!text.trim()) {
    return null;
  }

  const contentType = response.headers.get('content-type');
  // Accept application/json and application/*+json (e.g. application/problem+json)
  if (contentType && /application\/(?:.*\+)?json/.test(contentType)) {
    return JSON.parse(text);
  }

  // Non-JSON 2xx response is unexpected - throw rather than silently return null
  throw new Error(`Unexpected content-type: ${contentType || 'none'}`);
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
