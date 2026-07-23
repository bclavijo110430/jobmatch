import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Briefcase, MapPin, Calendar, Building2, Mic, Star, ExternalLink } from 'lucide-react';

const modalityIcon = {
  Remoto: '🏠',
  Remote: '🏠',
  Híbrido: '🔄',
  Hybrid: '🔄',
  Presencial: '🏢',
  'On-site': '🏢',
};

const modalityVariant = {
  Remoto: 'success',
  Remote: 'success',
  Híbrido: 'primary',
  Hybrid: 'primary',
  Presencial: 'secondary',
  'On-site': 'secondary',
};

const englishVariant = (level) => {
  if (['C1', 'C2', 'C1-C2'].includes(level)) return 'success';
  if (['B1', 'B2', 'B1-B2'].includes(level)) return 'default';
  if (['A1', 'A2', 'A1-A2'].includes(level)) return 'warning';
  return 'secondary';
};

export default function JobCard({ job, saved, onSave, onUnsave, onInterview, showActions = true }) {
  const {
    id,
    title,
    url,
    company,
    location,
    created_at,
    modality,
    english_level,
    english_match,
    salary,
    description_short,
    source,
  } = job;

  const dateDisplay = created_at && created_at !== 'Fecha desconocida' ? created_at.slice(0, 10) : '';
  const salaryDisplay = salary && salary !== 'No disponible' ? salary.split('-')[0].trim() : null;

  return (
    <Card className="card-hover border-jm-border bg-jm-card">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <a
              href={url || '#'}
              target={url ? '_blank' : undefined}
              rel={url ? 'noopener noreferrer' : undefined}
              className="text-base font-semibold text-jm-text-bright hover:text-jm-primary-light sm:text-lg"
            >
              {title || 'Sin título'}
            </a>
            <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-jm-text-secondary">
              {company && company !== 'No disponible' && (
                <span className="flex items-center gap-1">
                  <Building2 className="h-3.5 w-3.5" />
                  {company}
                </span>
              )}
              {location && location !== 'N/A' && (
                <span className="flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5" />
                  {location}
                </span>
              )}
              {dateDisplay && (
                <span className="flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5" />
                  {dateDisplay}
                </span>
              )}
              {source && (
                <span className="text-jm-text-muted">{source}</span>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end gap-1">
            <Badge variant={modalityVariant[modality] || 'secondary'}>
              {modalityIcon[modality] || '📌'} {modality || 'No especificado'}
            </Badge>
            {salaryDisplay ? (
              <span className="text-sm font-medium text-jm-text-bright">{salaryDisplay}</span>
            ) : (
              <span className="text-xs text-jm-text-muted">Sin salario</span>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={englishVariant(english_level)}>
            {english_match ? '✅ ' : ''}Inglés: {english_level || 'Ninguno'}
          </Badge>
        </div>
        <p className="mt-3 line-clamp-3 text-sm leading-relaxed text-jm-text-secondary">
          {description_short || 'Sin descripción'}
        </p>
      </CardContent>

      {showActions && (
        <CardFooter className="flex flex-wrap gap-2 border-t border-jm-border/50 pt-3">
          {url && (
            <Button variant="outline" size="sm" asChild className="border-jm-border bg-jm-surface hover:bg-jm-surface-hover">
              <a href={url} target="_blank" rel="noopener noreferrer" className="gap-1.5">
                <ExternalLink className="h-4 w-4" />
                Ver oferta
              </a>
            </Button>
          )}
          {onInterview && (
            <Button variant="outline" size="sm" onClick={onInterview} className="border-jm-border bg-jm-surface hover:bg-jm-surface-hover">
              <Mic className="mr-1.5 h-4 w-4" />
              Simular entrevista
            </Button>
          )}
          {saved ? (
            <Button variant="default" size="sm" onClick={onUnsave} className="bg-jm-primary hover:bg-jm-primary-hover">
              <Star className="mr-1.5 h-4 w-4 fill-current" />
              Guardada
            </Button>
          ) : (
            <Button variant="outline" size="sm" onClick={onSave} className="border-jm-border bg-jm-surface hover:bg-jm-surface-hover">
              <Star className="mr-1.5 h-4 w-4" />
              Guardar
            </Button>
          )}
        </CardFooter>
      )}
    </Card>
  );
}
