import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../lib/api';

export function useSteps(startDate = null, endDate = null) {
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    async function fetchSteps() {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getSteps(startDate, endDate, { signal });
        setSteps(data);
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

    fetchSteps();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [startDate, endDate]);

  const refetch = useCallback(async () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    try {
      setLoading(true);
      setError(null);
      const data = await api.getSteps(startDate, endDate, { signal });
      setSteps(data);
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      if (!signal.aborted) {
        setLoading(false);
      }
    }
  }, [startDate, endDate]);

  return { steps, loading, error, refetch };
}
