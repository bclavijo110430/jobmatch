import { useEffect, useState } from 'react';
import { useStore } from '@nanostores/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import EmptyState from '@/components/react/EmptyState.jsx';
import { cvTextStore, automationStore, setAutomation } from '@/stores/appStore.js';
import api from '@/lib/api.js';
import { toast } from 'sonner';
import { Zap, Play, Square, RotateCcw, Send, Bot } from 'lucide-react';

export default function AutomationIsland() {
  const cvText = useStore(cvTextStore);
  const automation = useStore(automationStore);

  const [token, setToken] = useState('');
  const [chatId, setChatId] = useState('');
  const [interval, setInterval] = useState(30);
  const [keyword, setKeyword] = useState('');

  useEffect(() => {
    api.getProfile()
      .then((profile) => {
        setInterval(profile.auto_interval || 30);
        setKeyword(profile.auto_keyword || '');
      })
      .catch(() => {});
    refreshStatus();
    const id = setInterval(refreshStatus, 5000);
    return () => clearInterval(id);
  }, []);

  const refreshStatus = async () => {
    try {
      const status = await api.getAutomationStatus();
      const logs = await api.getAutomationLogs();
      setAutomation({ ...status, logs: logs.logs });
    } catch {
      // ignore polling errors
    }
  };

  const handleStart = async () => {
    try {
      await api.startAutomation({
        telegram_token: token,
        telegram_chat_id: chatId,
        interval_minutes: interval,
        keyword,
      });
      toast.success('Automatización iniciada');
      refreshStatus();
    } catch (err) {
      toast.error(err.message || 'Error iniciando automatización');
    }
  };

  const handleStop = async () => {
    try {
      await api.stopAutomation();
      toast.success('Automatización detenida');
      refreshStatus();
    } catch (err) {
      toast.error(err.message || 'Error deteniendo automatización');
    }
  };

  const handleReset = async () => {
    try {
      await api.resetAutomation();
      toast.success('Historial reseteado');
      refreshStatus();
    } catch (err) {
      toast.error(err.message || 'Error reseteando');
    }
  };

  const handleTest = async () => {
    try {
      await api.testTelegram({ telegram_token: token, telegram_chat_id: chatId });
      toast.success('Notificación de prueba enviada');
    } catch (err) {
      toast.error(err.message || 'Error enviando notificación de prueba');
    }
  };

  if (!cvText) {
    return (
      <EmptyState
        icon={Bot}
        title="Sube tu CV primero"
        description="La automatización usa tu perfil para filtrar ofertas. Sube tu CV en el dashboard."
      />
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <Card className="border-jm-border bg-jm-card">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-jm-text-bright">
              <Zap className="h-5 w-5 text-jm-primary-light" />
              Automatización de búsqueda
            </CardTitle>
            <Badge variant={automation.running ? 'success' : 'secondary'}>
              {automation.running ? '🟢 Activa' : '⚪ Detenida'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label className="text-jm-text-secondary">Telegram Bot Token</Label>
              <Input
                type="password"
                placeholder="123456:ABC-DEF..."
                value={token}
                onChange={(e) => setToken(e.target.value)}
                className="border-jm-border bg-jm-surface text-jm-text placeholder:text-jm-text-muted focus-visible:ring-jm-primary"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-jm-text-secondary">Chat ID</Label>
              <Input
                placeholder="123456789"
                value={chatId}
                onChange={(e) => setChatId(e.target.value)}
                className="border-jm-border bg-jm-surface text-jm-text placeholder:text-jm-text-muted focus-visible:ring-jm-primary"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-jm-text-secondary">Intervalo (minutos)</Label>
              <Input
                type="number"
                min={1}
                max={720}
                step={5}
                value={interval}
                onChange={(e) => setInterval(Number(e.target.value))}
                className="border-jm-border bg-jm-surface text-jm-text focus-visible:ring-jm-primary"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-jm-text-secondary">Keyword adicional</Label>
              <Input
                placeholder="ej: Python, React..."
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="border-jm-border bg-jm-surface text-jm-text placeholder:text-jm-text-muted focus-visible:ring-jm-primary"
              />
            </div>
          </div>

          <Separator className="bg-jm-border" />

          <div className="flex flex-wrap gap-2">
            <Button
              onClick={handleStart}
              disabled={automation.running || !token || !chatId}
              className="bg-jm-primary hover:bg-jm-primary-hover"
            >
              <Play className="mr-2 h-4 w-4" />
              Iniciar
            </Button>
            <Button
              variant="outline"
              onClick={handleStop}
              disabled={!automation.running}
              className="border-jm-border bg-jm-surface hover:bg-jm-surface-hover"
            >
              <Square className="mr-2 h-4 w-4" />
              Detener
            </Button>
            <Button
              variant="outline"
              onClick={handleReset}
              className="border-jm-border bg-jm-surface hover:bg-jm-surface-hover"
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Resetear
            </Button>
            <Button
              variant="outline"
              onClick={handleTest}
              disabled={!token || !chatId}
              className="border-jm-border bg-jm-surface hover:bg-jm-surface-hover"
            >
              <Send className="mr-2 h-4 w-4" />
              Probar notificación
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="border-jm-border bg-jm-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold text-jm-text-bright">Registro</CardTitle>
        </CardHeader>
        <CardContent>
          {automation.logs.length === 0 ? (
            <p className="text-sm text-jm-text-muted">Sin eventos aún.</p>
          ) : (
            <div className="max-h-64 overflow-y-auto rounded-md border border-jm-border bg-jm-bg p-3 font-mono text-xs text-jm-text-secondary">
              {automation.logs.map((log, idx) => (
                <div key={idx} className="py-0.5">
                  {log}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
