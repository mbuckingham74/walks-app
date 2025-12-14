import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../lib/api';

export function useStats(year = null) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    async function fetchStats() {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getStats(year, { signal });
        setStats(data);
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err.message);
        }
      } finally {
        if (!signal.aborted) {
          setLoading(false);
        }
      }
    }

    fetchStats();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [year]);

  const refetch = useCallback(async () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    try {
      setLoading(true);
      setError(null);
      const data = await api.getStats(year, { signal });
      setStats(data);
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      if (!signal.aborted) {
        setLoading(false);
      }
    }
  }, [year]);

  return { stats, loading, error, refetch };
}
