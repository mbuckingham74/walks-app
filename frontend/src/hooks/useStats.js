import { useState, useEffect } from 'react';
import { api } from '../lib/api';

export function useStats(year = null) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        setLoading(true);
        const data = await api.getStats(year);
        setStats(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, [year]);

  const refetch = async () => {
    try {
      setLoading(true);
      const data = await api.getStats(year);
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { stats, loading, error, refetch };
}
