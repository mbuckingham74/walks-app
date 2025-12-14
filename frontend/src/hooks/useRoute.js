import { useState, useEffect, useRef } from 'react';
import { api } from '../lib/api';

export function useRoute() {
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    async function fetchRoute() {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getRoute({ signal });
        setRoute(data);
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

    fetchRoute();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  return { route, loading, error };
}
