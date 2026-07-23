import { useEffect, useState } from 'react';
import { useStore } from '@nanostores/react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Cpu } from 'lucide-react';
import api from '@/lib/api.js';
import { backendStore, setBackend } from '@/stores/appStore.js';
import { toast } from 'sonner';

export default function BackendSelector() {
  const backend = useStore(backendStore);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getBackends()
      .then((data) => {
        setBackend(data);
      })
      .catch(() => {
        setBackend({
          current: 'ollama',
          info: { label: 'Ollama', model: 'llama3.2:3b' },
          backends: [
            { key: 'ollama', label: 'Ollama (local)', model: 'llama3.2:3b', icon: '🟢' },
            { key: 'freellmapi', label: 'FreeLLMAPI (cloud)', model: 'auto', icon: '🔵' },
          ],
        });
      })
      .finally(() => setLoading(false));
  }, []);

  const handleChange = async (key) => {
    try {
      const data = await api.configureBackend(key);
      setBackend(data);
      toast.success(`Backend cambiado a ${data.info?.label || key}`);
    } catch (err) {
      toast.error(err.message || 'Error cambiando backend');
    }
  };

  if (loading || backend.backends.length === 0) {
    return (
      <div className="space-y-1.5">
        <Label className="text-xs font-medium uppercase tracking-wider text-jm-text-muted">Proveedor LLM</Label>
        <div className="h-9 animate-pulse rounded-md bg-jm-elevated" />
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      <Label className="text-xs font-medium uppercase tracking-wider text-jm-text-muted">Proveedor LLM</Label>
      <Select value={backend.current} onValueChange={handleChange}>
        <SelectTrigger className="h-9 w-full border-jm-border bg-jm-surface px-2.5 text-xs text-jm-text">
          <Cpu className="mr-1.5 h-3.5 w-3.5 shrink-0 text-jm-primary-light" />
          <SelectValue placeholder="Selecciona proveedor" className="truncate" />
        </SelectTrigger>
        <SelectContent
          position="popper"
          className="w-[var(--radix-select-trigger-width)] border-jm-border bg-jm-elevated text-jm-text"
        >
          {backend.backends.map((b) => (
            <SelectItem key={b.key} value={b.key} className="text-xs">
              <span className="mr-1.5">{b.icon}</span>
              <span className="truncate">{b.label}</span>
              <span className="ml-1 text-jm-text-muted">({b.model})</span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <p className="text-[10px] leading-tight text-jm-text-muted">
        Modelo: <span className="text-jm-text-secondary">{backend.model}</span>
      </p>
    </div>
  );
}
