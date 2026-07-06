import { useMemo } from 'react';
import { useFetch } from './useFetch';
import { api } from '../lib/api';

export function useRoute() {
  const fetchFn = useMemo(() => ({ signal }) => api.getRoute({ signal }), []);
  const { data: route, loading, error } = useFetch(fetchFn, []);

  return { route, loading, error };
}
