import { useMemo } from 'react';
import { useFetch } from './useFetch';
import { api } from '../lib/api';

export function useSteps(startDate = null, endDate = null) {
  const fetchFn = useMemo(() => ({ signal }) => api.getSteps(startDate, endDate, { signal }), [startDate, endDate]);
  const { data: steps, loading, error, refetch } = useFetch(fetchFn, [startDate, endDate]);

  return { steps: steps || [], loading, error, refetch };
}
