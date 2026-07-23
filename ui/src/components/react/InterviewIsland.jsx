import { useEffect, useRef, useState } from 'react';
import { useStore } from '@nanostores/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import EmptyState from '@/components/react/EmptyState.jsx';
import JobListSkeleton from '@/components/react/JobListSkeleton.jsx';
import { selectedJobStore, cvTextStore, loadSelectedJobFromStorage, selectJobForInterview } from '@/stores/appStore.js';
import api from '@/lib/api.js';
import { toast } from 'sonner';
import { Mic, Send, User, Bot, RefreshCw, Briefcase, Building2, MapPin, ExternalLink } from 'lucide-react';

function JobSelector() {
  const [savedJobs, setSavedJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSaved()
      .then((data) => setSavedJobs(data.jobs || []))
      .catch(() => toast.error('Error cargando ofertas guardadas'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <JobListSkeleton count={3} />;
  }

  if (savedJobs.length === 0) {
    return (
      <EmptyState
        icon={Mic}
        title="Selecciona una oferta"
        description="No tienes ofertas guardadas. Ve a Ofertas, elige una y haz clic en 'Simular entrevista'."
      />
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <Card className="border-jm-border bg-jm-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold text-jm-text-bright">
            Selecciona una oferta para la entrevista
          </CardTitle>
          <p className="text-sm text-jm-text-secondary">
            {savedJobs.length} oferta(s) guardada(s)
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          {savedJobs.map((job) => (
            <Card
              key={job.id || job.url}
              className="border-jm-border bg-jm-surface"
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Briefcase className="h-4 w-4 text-jm-primary-light" />
                      <h3 className="text-sm font-semibold text-jm-text-bright">
                        {job.title || 'Sin título'}
                      </h3>
                    </div>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-jm-text-secondary">
                      {job.company && job.company !== 'No disponible' && (
                        <span className="flex items-center gap-1">
                          <Building2 className="h-3.5 w-3.5" />
                          {job.company}
                        </span>
                      )}
                      {job.location && job.location !== 'N/A' && (
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5" />
                          {job.location}
                        </span>
                      )}
                    </div>
                    {job.english_level && (
                      <Badge variant="default" className="text-xs">
                        Inglés: {job.english_level}
                      </Badge>
                    )}
                  </div>
                  <div className="flex flex-col gap-2">
                    <Button
                      size="sm"
                      onClick={() => selectJobForInterview(job)}
                      className="bg-jm-primary hover:bg-jm-primary-hover"
                    >
                      <Mic className="mr-1.5 h-4 w-4" />
                      Entrevistar
                    </Button>
                    {job.url && (
                      <Button variant="outline" size="sm" asChild className="border-jm-border bg-jm-card hover:bg-jm-surface-hover">
                        <a href={job.url} target="_blank" rel="noopener noreferrer" className="gap-1.5">
                          <ExternalLink className="h-3.5 w-3.5" />
                          Ver
                        </a>
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

export default function InterviewIsland() {
  const selectedJob = useStore(selectedJobStore);
  const cvText = useStore(cvTextStore);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (!selectedJob) {
      const stored = loadSelectedJobFromStorage();
      if (stored) {
        selectedJobStore.set(stored);
      }
    }
  }, []);

  useEffect(() => {
    if (selectedJob && cvText && messages.length === 0) {
      startInterview();
    }
  }, [selectedJob, cvText]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startInterview = async () => {
    setLoading(true);
    try {
      const data = await api.startInterview(selectedJob);
      setMessages([{ role: 'assistant', content: data.message }]);
    } catch (err) {
      toast.error(err.message || 'Error iniciando entrevista');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMsg = { role: 'user', content: input.trim() };
    const nextHistory = [...messages, userMsg];
    setMessages(nextHistory);
    setInput('');
    setLoading(true);
    try {
      const data = await api.continueInterview(selectedJob, nextHistory);
      setMessages([...nextHistory, { role: 'assistant', content: data.message }]);
    } catch (err) {
      toast.error(err.message || 'Error continuando entrevista');
    } finally {
      setLoading(false);
    }
  };

  if (!cvText) {
    return (
      <EmptyState
        icon={User}
        title="Necesitamos tu CV"
        description="Sube tu CV en el dashboard para poder simular una entrevista personalizada."
      />
    );
  }

  if (!selectedJob) {
    return <JobSelector />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <Card className="border-jm-border bg-jm-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold text-jm-text-bright">
            Entrevista: {selectedJob.title}
          </CardTitle>
          <p className="text-sm text-jm-text-secondary">
            {selectedJob.company} · {selectedJob.location}
          </p>
        </CardHeader>
        <CardContent>
          <Button
            variant="outline"
            size="sm"
            onClick={startInterview}
            disabled={loading}
            className="border-jm-border bg-jm-surface hover:bg-jm-surface-hover"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Reiniciar entrevista
          </Button>
        </CardContent>
      </Card>

      <Card className="border-jm-border bg-jm-card">
        <CardContent className="flex h-[50vh] flex-col gap-3 overflow-y-auto p-4">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${msg.role === 'user' ? 'bg-jm-primary' : 'bg-jm-success'}`}>
                {msg.role === 'user' ? <User className="h-4 w-4 text-white" /> : <Bot className="h-4 w-4 text-white" />}
              </div>
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                  msg.role === 'user'
                    ? 'bg-jm-primary text-white'
                    : 'bg-jm-elevated text-jm-text'
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}
          {loading && messages.length > 0 && messages[messages.length - 1].role === 'user' && (
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-jm-success">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div className="bg-jm-elevated rounded-lg px-4 py-2 text-sm text-jm-text-muted">
                Escribiendo...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </CardContent>
      </Card>

      <div className="flex items-center gap-2">
        <Input
          placeholder="Escribe tu respuesta aquí..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          disabled={loading}
          className="border-jm-border bg-jm-surface text-jm-text placeholder:text-jm-text-muted focus-visible:ring-jm-primary"
        />
        <Button onClick={handleSend} disabled={loading || !input.trim()} className="bg-jm-primary hover:bg-jm-primary-hover">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
