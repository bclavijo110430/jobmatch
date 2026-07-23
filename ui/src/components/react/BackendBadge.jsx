import { useEffect, useState } from 'react';
import { Cpu } from 'lucide-react';
import api from '@/lib/api.js';
import { setBackend, backendStore } from '@/stores/appStore.js';
import { useStore } from '@nanostores/react';

export default function BackendBadge() {
  const backend = useStore(backendStore);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getBackends()
      .then((data) => {
        setBackend(data);
      })
      .catch(() => {
        setBackend({ current: 'ollama', info: { label: 'Ollama', model: 'llama3.2:3b' }, backends: [] });
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="h-8 w-32 animate-pulse rounded-md bg-jm-elevated" />
    );
  }

  return (
    <div className="flex items-center gap-2 rounded-lg border border-jm-border bg-jm-elevated px-3 py-1.5 text-xs">
      <Cpu className="h-4 w-4 text-jm-primary-light" />
      <div className="hidden flex-col sm:flex">
        <span className="font-medium text-jm-text-bright">{backend.label}</span>
        <span className="text-jm-text-muted">{backend.model}</span>
      </div>
      <span className="sm:hidden text-jm-text-secondary">{backend.current}</span>
    </div>
  );
}
