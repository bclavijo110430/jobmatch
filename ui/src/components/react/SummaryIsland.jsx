import { useMemo } from 'react';
import { useStore } from '@nanostores/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress'; // need to add progress component
import { Badge } from '@/components/ui/badge';
import EmptyState from '@/components/react/EmptyState.jsx';
import { jobsStore, candidateLevelStore, profileStore, cvTextStore } from '@/stores/appStore.js';
import { BarChart3, Languages, Briefcase } from 'lucide-react';

const ENGLISH_ORDER = ['Ninguno', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

export default function SummaryIsland() {
  const jobs = useStore(jobsStore);
  const level = useStore(candidateLevelStore);
  const profile = useStore(profileStore);
  const cvText = useStore(cvTextStore);

  const matchCount = useMemo(() => jobs.filter((j) => j.english_match).length, [jobs]);
  const total = jobs.length || 1;
  const pct = Math.round((matchCount / total) * 100);

  const levelsCount = useMemo(() => {
    const counts = {};
    for (const j of jobs) {
      const lvl = j.english_level || 'Ninguno';
      counts[lvl] = (counts[lvl] || 0) + 1;
    }
    return counts;
  }, [jobs]);

  if (!cvText) {
    return (
      <EmptyState
        icon={BarChart3}
        title="Sin datos del perfil"
        description="Sube tu CV en el dashboard para ver tu resumen y estadísticas."
      />
    );
  }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <Card className="border-jm-border bg-jm-card">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-jm-text-bright">
              <Languages className="h-5 w-5 text-jm-primary-light" />
              Nivel de inglés
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-jm-text-bright">{level || 'No analizado'}</p>
          </CardContent>
        </Card>

        <Card className="border-jm-border bg-jm-card">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-jm-text-bright">
              <Briefcase className="h-5 w-5 text-jm-primary-light" />
              Ofertas disponibles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-jm-text-bright">{jobs.length}</p>
          </CardContent>
        </Card>
      </div>

      {jobs.length > 0 && (
        <>
          <Card className="border-jm-border bg-jm-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold text-jm-text-bright">
                Compatibilidad de inglés: {pct}%
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Progress value={pct} className="h-2 bg-jm-elevated" />
              <p className="text-sm text-jm-text-secondary">
                {matchCount} de {jobs.length} ofertas compatibles con tu nivel.
              </p>
            </CardContent>
          </Card>

          <Card className="border-jm-border bg-jm-card">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-semibold text-jm-text-bright">
                Distribución por nivel de inglés
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {ENGLISH_ORDER.filter((lvl) => levelsCount[lvl]).map((lvl) => {
                  const count = levelsCount[lvl];
                  const bar = '█'.repeat(Math.min(count, 40));
                  return (
                    <div key={lvl} className="flex items-center gap-3 text-sm">
                      <Badge variant="secondary" className="w-20 justify-center">{lvl}</Badge>
                      <span className="text-jm-text-muted w-8">({count})</span>
                      <span className="font-mono text-jm-primary-light">{bar}</span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      <Card className="border-jm-border bg-jm-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold text-jm-text-bright">Texto del CV</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="max-h-64 overflow-y-auto rounded-md border border-jm-border bg-jm-bg p-3 font-mono text-xs text-jm-text-secondary">
            {cvText}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
