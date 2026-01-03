const API_BASE = import.meta.env.VITE_API_URL || '/api';
const API_KEY = import.meta.env.VITE_API_KEY || '';

async function fetchAPI(endpoint, options = {}) {
  const { headers, ...restOptions } = options;
  const requestHeaders = {
    'Content-Type': 'application/json',
    ...headers,
  };

  // Add API key if configured
  if (API_KEY) {
    requestHeaders['X-API-Key'] = API_KEY;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: requestHeaders,
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
  getStats: (year, { signal } = {}) => fetchAPI(year ? `/stats?year=${year}` : '/stats', { signal }),

  // Steps
  getSteps: (start, end, { signal } = {}) => {
    const params = new URLSearchParams();
    if (start) params.append('start', start);
    if (end) params.append('end', end);
    return fetchAPI(`/steps?${params}`, { signal });
  },

  // Activities
  getActivities: (year, options = {}) => {
    const { limit = 50, signal } = options;
    const params = new URLSearchParams();
    if (year) params.append('year', year);
    params.append('limit', limit);
    return fetchAPI(`/activities?${params}`, { signal });
  },

  // Route
  getRoute: ({ signal } = {}) => fetchAPI('/route', { signal }),

  // Config
  getConfig: ({ signal } = {}) => fetchAPI('/config', { signal }),
};
