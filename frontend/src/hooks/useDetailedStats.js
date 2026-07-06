import { useMemo } from 'react';
import { useFetch } from './useFetch';
import { api } from '../lib/api';

export function useDetailedStats(year = null) {
  const fetchFn = useMemo(
    () => ({ signal }) => api.getDetailedStats(year, { signal }),
    [year]
  );
  const { data: stats, loading, error, refetch } = useFetch(fetchFn, [year]);

  return { stats, loading, error, refetch };
}
