import { useEffect, useMemo, useState } from 'react';
import { useStore } from '@nanostores/react';
import ProfileCard from '@/components/react/ProfileCard.jsx';
import SearchCard from '@/components/react/SearchCard.jsx';
import StatsRow from '@/components/react/StatsRow.jsx';
import FilterPanel from '@/components/react/FilterPanel.jsx';
import JobCard from '@/components/react/JobCard.jsx';
import EmptyState from '@/components/react/EmptyState.jsx';
import JobListSkeleton from '@/components/react/JobListSkeleton.jsx';
import { Button } from '@/components/ui/button';
import { Briefcase } from 'lucide-react';
import { jobsStore, savedUrlsStore, uiStore, selectedJobStore, profileStore, setSavedUrls, addSavedUrl, selectJobForInterview } from '@/stores/appStore.js';
import { applyFilters, sortByDate } from '@/lib/filters.js';
import api from '@/lib/api.js';
import { toast } from 'sonner';

const DEFAULT_FILTERS = {
  keyword: '',
  modality: 'Todas',
  locations: [],
  englishLevels: [],
  companies: [],
  minSalary: 0,
  maxExperience: 15,
};

export default function DashboardIsland() {
  const jobs = useStore(jobsStore);
  const savedUrls = useStore(savedUrlsStore);
  const ui = useStore(uiStore);
  const profile = useStore(profileStore);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);

  useEffect(() => {
    api.getSaved()
      .then((data) => {
        const urls = (data.jobs || []).map((j) => j.url).filter(Boolean);
        setSavedUrls(urls);
      })
      .catch(() => {});
  }, []);

  const filteredJobs = useMemo(() => {
    return sortByDate(applyFilters(jobs, filters));
  }, [jobs, filters]);

  const handleSave = async (job) => {
    try {
      await api.saveJob(job);
      addSavedUrl(job.url);
      toast.success('Oferta guardada');
    } catch (err) {
      toast.error(err.message || 'Error guardando oferta');
    }
  };

  const handleInterview = (job) => {
    selectJobForInterview(job);
    window.location.href = '/interview';
  };

  const hasProfile = profile.skills?.length > 0 || profile.target_titles?.length > 0;

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <ProfileCard />
        <SearchCard />
      </div>

      <StatsRow />

      <FilterPanel filters={filters} onChange={setFilters} />

      {ui.isSearching ? (
        <JobListSkeleton count={3} />
      ) : filteredJobs.length === 0 ? (
        <EmptyState
          icon={Briefcase}
          title={jobs.length === 0 ? 'Bienvenido a JobMatch' : 'Sin resultados'}
          description={
            jobs.length === 0
              ? 'Sube tu CV y busca ofertas para empezar. Usa los filtros para refinar resultados.'
              : 'Ninguna oferta coincide con los filtros activos.'
          }
          action={
            jobs.length === 0 && !hasProfile ? (
              <Button onClick={() => document.getElementById('cv-upload')?.click()} className="bg-jm-primary hover:bg-jm-primary-hover">
                Subir CV
              </Button>
            ) : null
          }
        />
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-jm-text-bright">
              Ofertas ({filteredJobs.length})
            </h2>
          </div>
          {filteredJobs.map((job, idx) => (
            <JobCard
              key={job.url ? `${job.url}-${idx}` : idx}
              job={job}
              saved={job.url && savedUrls.has(job.url)}
              onSave={() => handleSave(job)}
              onInterview={() => handleInterview(job)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
