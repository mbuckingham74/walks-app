import { useState, useEffect, useRef } from 'react';
import { api } from '../lib/api';

const DEFAULT_CONFIG = {
  steps_per_mile: 2000,
  daily_goal: 15000,
};

export function useConfig() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    async function fetchConfig() {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getConfig({ signal });
        setConfig(data);
      } catch (err) {
        if (err.name !== 'AbortError') {
          setError(err.message);
          // Keep default config on error
        }
      } finally {
        if (!signal.aborted) {
          setLoading(false);
        }
      }
    }

    fetchConfig();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  return { config, loading, error };
}
