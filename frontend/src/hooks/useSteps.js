import { useState, useEffect } from 'react';
import { api } from '../lib/api';

export function useSteps(startDate = null, endDate = null) {
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchSteps() {
      try {
        setLoading(true);
        const data = await api.getSteps(startDate, endDate);
        setSteps(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchSteps();
  }, [startDate, endDate]);

  const refetch = async () => {
    try {
      setLoading(true);
      const data = await api.getSteps(startDate, endDate);
      setSteps(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { steps, loading, error, refetch };
}
