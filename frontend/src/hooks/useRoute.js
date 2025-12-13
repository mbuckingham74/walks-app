import { useState, useEffect } from 'react';
import { api } from '../lib/api';

export function useRoute() {
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchRoute() {
      try {
        setLoading(true);
        const data = await api.getRoute();
        setRoute(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchRoute();
  }, []);

  return { route, loading, error };
}
