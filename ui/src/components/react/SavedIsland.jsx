import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import JobCard from '@/components/react/JobCard.jsx';
import EmptyState from '@/components/react/EmptyState.jsx';
import JobListSkeleton from '@/components/react/JobListSkeleton.jsx';
import { selectedJobStore, setSavedUrls, selectJobForInterview } from '@/stores/appStore.js';
import api from '@/lib/api.js';
import { toast } from 'sonner';
import { Star } from 'lucide-react';

export default function SavedIsland() {
  const [savedJobs, setSavedJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.getSaved();
      setSavedJobs(data.jobs || []);
      setSavedUrls((data.jobs || []).map((j) => j.url).filter(Boolean));
    } catch (err) {
      toast.error(err.message || 'Error cargando favoritos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (job) => {
    try {
      await api.deleteSaved(job.id);
      setSavedJobs((prev) => prev.filter((j) => j.id !== job.id));
      toast.success('Eliminado de favoritos');
    } catch (err) {
      toast.error(err.message || 'Error eliminando favorito');
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
          <CardTitle className="flex items-center gap-2 text-base font-semibold text-jm-text-bright">
            <Star className="h-5 w-5 text-jm-primary-light" />
            Favoritos
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-jm-text-secondary">
            {savedJobs.length} oferta(s) guardada(s)
          </p>
        </CardContent>
      </Card>

      {savedJobs.length === 0 ? (
        <EmptyState
          icon={Star}
          title="Sin favoritos aún"
          description="Guarda ofertas desde la pestaña Ofertas para verlas aquí."
        />
      ) : (
        <div className="space-y-3">
          {savedJobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              saved={true}
              onUnsave={() => handleDelete(job)}
              onInterview={() => handleInterview(job)}
              showActions={true}
            />
          ))}
          <div className="flex justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={load}
              className="border-jm-border bg-jm-surface hover:bg-jm-surface-hover"
            >
              Refrescar
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
