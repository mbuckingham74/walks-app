import { useMemo } from 'react';
import { useFetch } from './useFetch';
import { api } from '../lib/api';

const DEFAULT_CONFIG = {
  steps_per_mile: 1850,
  daily_goal: 15000,
};

export function useConfig() {
  const fetchFn = useMemo(() => ({ signal }) => api.getConfig({ signal }), []);
  const { data: config, loading, error } = useFetch(fetchFn, []);

  return { config: config || DEFAULT_CONFIG, loading, error };
}
