import { useState } from 'react';
import { RefreshCw, Check, AlertCircle } from 'lucide-react';
import { api } from '../lib/api';

export function SyncButton({ onSyncComplete }) {
  const [syncing, setSyncing] = useState(false);
  const [status, setStatus] = useState(null); // 'success' | 'error' | null

  const handleSync = async () => {
    setSyncing(true);
    setStatus(null);

    try {
      await api.triggerSync();
      setStatus('success');
      if (onSyncComplete) {
        // Wait a bit for sync to process, then refresh data
        setTimeout(() => {
          onSyncComplete();
        }, 2000);
      }
    } catch (error) {
      setStatus('error');
      console.error('Sync failed:', error);
    } finally {
      setSyncing(false);
      // Clear status after 3 seconds
      setTimeout(() => setStatus(null), 3000);
    }
  };

  return (
    <button
      onClick={handleSync}
      disabled={syncing}
      className={`
        flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm
        transition-all duration-200 cursor-pointer
        ${syncing
          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
          : status === 'success'
          ? 'bg-primary-100 text-primary-700'
          : status === 'error'
          ? 'bg-red-100 text-red-700'
          : 'bg-primary-500 text-white hover:bg-primary-600 active:bg-primary-700'
        }
      `}
    >
      {syncing ? (
        <>
          <RefreshCw className="w-4 h-4 animate-spin" />
          Syncing...
        </>
      ) : status === 'success' ? (
        <>
          <Check className="w-4 h-4" />
          Synced!
        </>
      ) : status === 'error' ? (
        <>
          <AlertCircle className="w-4 h-4" />
          Failed
        </>
      ) : (
        <>
          <RefreshCw className="w-4 h-4" />
          Sync from Garmin
        </>
      )}
    </button>
  );
}
