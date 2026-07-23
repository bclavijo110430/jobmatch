import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import JobCard from '@/components/react/JobCard.jsx';
import EmptyState from '@/components/react/EmptyState.jsx';
import JobListSkeleton from '@/components/react/JobListSkeleton.jsx';
import { selectedJobStore, addSavedUrl, selectJobForInterview } from '@/stores/appStore.js';
import api from '@/lib/api.js';
import { toast } from 'sonner';
import { BellRing, Star, Trash2 } from 'lucide-react';

export default function DetectedIsland() {
  const [detectedJobs, setDetectedJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.getDiscovered();
      setDetectedJobs(data.jobs || []);
    } catch (err) {
      toast.error(err.message || 'Error cargando detectadas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSave = async (job) => {
    try {
      await api.saveJob(job);
      addSavedUrl(job.url);
      toast.success('Movida a favoritos');
    } catch (err) {
      toast.error(err.message || 'Error guardando oferta');
    }
  };

  const handleDelete = async (job) => {
    try {
      await api.deleteDiscovered(job.id);
      setDetectedJobs((prev) => prev.filter((j) => j.id !== job.id));
      toast.success('Oferta eliminada');
    } catch (err) {
      toast.error(err.message || 'Error eliminando oferta');
    }
  };

  const handleClear = async () => {
    try {
      await api.clearDiscovered();
      setDetectedJobs([]);
      toast.success('Histórico vaciado');
    } catch (err) {
      toast.error(err.message || 'Error vaciando histórico');
    }
  };

  const handleInterview = (job) => {
    selectJobForInterview(job);
    window.location.href = '/interview';
  };

  if (loading) {
    return <JobListSkeleton count={3} />;
  }

  return (
    <div className="space-y-5">
      <Card className="border-jm-border bg-jm-card">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-jm-text-bright">
              <BellRing className="h-5 w-5 text-jm-primary-light" />
              Detectadas
            </CardTitle>
            {detectedJobs.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleClear}
                className="border-jm-border text-jm-danger hover:bg-jm-danger-soft hover:text-jm-danger"
              >
                <Trash2 className="mr-1.5 h-4 w-4" />
                Vaciar
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-jm-text-secondary">
            {detectedJobs.length} oferta(s) detectada(s) por la automatización.
          </p>
        </CardContent>
      </Card>

      {detectedJobs.length === 0 ? (
        <EmptyState
          icon={BellRing}
          title="Sin ofertas detectadas aún"
          description="Inicia la automatización para recibir ofertas filtradas por IA."
        />
      ) : (
        <div className="space-y-3">
          {detectedJobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              saved={false}
              onSave={() => handleSave(job)}
              onInterview={() => handleInterview(job)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
