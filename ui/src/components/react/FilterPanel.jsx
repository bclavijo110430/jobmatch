import { useMemo, useState } from 'react';
import { useStore } from '@nanostores/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Filter, ChevronDown, X } from 'lucide-react';
import { jobsStore } from '@/stores/appStore.js';
import { getUniqueLocations, getUniqueCompanies } from '@/lib/filters.js';

const ENGLISH_LEVELS = ['Ninguno', 'A1-A2', 'B1-B2', 'C1-C2'];

export default function FilterPanel({ filters, onChange }) {
  const jobs = useStore(jobsStore);
  const [open, setOpen] = useState(false);

  const locations = useMemo(() => getUniqueLocations(jobs), [jobs]);
  const companies = useMemo(() => getUniqueCompanies(jobs), [jobs]);

  const toggleArray = (key, value) => {
    const current = filters[key] || [];
    const next = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value];
    onChange({ ...filters, [key]: next });
  };

  const hasFilters =
    filters.keyword ||
    filters.modality !== 'Todas' ||
    (filters.locations?.length || 0) > 0 ||
    (filters.englishLevels?.length || 0) > 0 ||
    (filters.companies?.length || 0) > 0 ||
    filters.minSalary > 0 ||
    (filters.maxExperience || 0) > 0;

  const clearFilters = () => {
    onChange({
      keyword: '',
      modality: 'Todas',
      locations: [],
      englishLevels: [],
      companies: [],
      minSalary: 0,
      maxExperience: 15,
    });
  };

  if (jobs.length === 0) return null;

  return (
    <Card className="border-jm-border bg-jm-card">
      <Collapsible open={open} onOpenChange={setOpen}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base font-semibold text-jm-text-bright">
              <Filter className="h-5 w-5 text-jm-primary-light" />
              Filtros avanzados
            </CardTitle>
            <div className="flex items-center gap-2">
              {hasFilters && (
                <Button variant="ghost" size="sm" onClick={clearFilters} className="h-8 text-jm-text-muted hover:text-jm-text">
                  <X className="mr-1 h-4 w-4" />
                  Limpiar
                </Button>
              )}
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 text-jm-text-secondary">
                  <ChevronDown className={`h-4 w-4 transition-transform ${open ? 'rotate-180' : ''}`} />
                </Button>
              </CollapsibleTrigger>
            </div>
          </div>
        </CardHeader>
        <CollapsibleContent>
          <CardContent className="grid gap-5 pt-0 sm:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-1.5">
              <Label className="text-jm-text-secondary">Palabra clave</Label>
              <Input
                placeholder="filtrar por título..."
                value={filters.keyword}
                onChange={(e) => onChange({ ...filters, keyword: e.target.value })}
                className="border-jm-border bg-jm-surface text-jm-text placeholder:text-jm-text-muted focus-visible:ring-jm-primary"
              />
            </div>

            <div className="space-y-1.5">
              <Label className="text-jm-text-secondary">Modalidad</Label>
              <Select
                value={filters.modality}
                onValueChange={(v) => onChange({ ...filters, modality: v })}
              >
                <SelectTrigger className="border-jm-border bg-jm-surface text-jm-text">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="border-jm-border bg-jm-elevated text-jm-text">
                  <SelectItem value="Todas">Todas</SelectItem>
                  <SelectItem value="Remoto">Remoto</SelectItem>
                  <SelectItem value="Híbrido">Híbrido</SelectItem>
                  <SelectItem value="Presencial">Presencial</SelectItem>
                  <SelectItem value="No especificado">No especificado</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-jm-text-secondary">Ubicación</Label>
              <div className="max-h-32 overflow-y-auto rounded-md border border-jm-border bg-jm-surface p-2">
                {locations.length === 0 ? (
                  <p className="text-xs text-jm-text-muted">Sin opciones</p>
                ) : (
                  locations.map((loc) => (
                    <label key={loc} className="flex items-center gap-2 py-1 text-sm text-jm-text-secondary hover:text-jm-text">
                      <Checkbox
                        checked={filters.locations?.includes(loc)}
                        onCheckedChange={() => toggleArray('locations', loc)}
                        className="border-jm-border data-[state=checked]:border-jm-primary data-[state=checked]:bg-jm-primary"
                      />
                      {loc}
                    </label>
                  ))
                )}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label className="text-jm-text-secondary">Nivel de inglés</Label>
              <div className="flex flex-wrap gap-3">
                {ENGLISH_LEVELS.map((lvl) => (
                  <label key={lvl} className="flex items-center gap-1.5 text-sm text-jm-text-secondary hover:text-jm-text">
                    <Checkbox
                      checked={filters.englishLevels?.includes(lvl)}
                      onCheckedChange={() => toggleArray('englishLevels', lvl)}
                      className="border-jm-border data-[state=checked]:border-jm-primary data-[state=checked]:bg-jm-primary"
                    />
                    {lvl}
                  </label>
                ))}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label className="text-jm-text-secondary">Empresa</Label>
              <div className="max-h-32 overflow-y-auto rounded-md border border-jm-border bg-jm-surface p-2">
                {companies.length === 0 ? (
                  <p className="text-xs text-jm-text-muted">Sin opciones</p>
                ) : (
                  companies.map((c) => (
                    <label key={c} className="flex items-center gap-2 py-1 text-sm text-jm-text-secondary hover:text-jm-text">
                      <Checkbox
                        checked={filters.companies?.includes(c)}
                        onCheckedChange={() => toggleArray('companies', c)}
                        className="border-jm-border data-[state=checked]:border-jm-primary data-[state=checked]:bg-jm-primary"
                      />
                      {c}
                    </label>
                  ))
                )}
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label className="text-jm-text-secondary">Salario mínimo (COP)</Label>
                <Input
                  type="number"
                  min={0}
                  step={500000}
                  value={filters.minSalary}
                  onChange={(e) => onChange({ ...filters, minSalary: Number(e.target.value) })}
                  className="border-jm-border bg-jm-surface text-jm-text focus-visible:ring-jm-primary"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-jm-text-secondary">Experiencia máxima: {filters.maxExperience} años</Label>
                <Slider
                  value={[filters.maxExperience]}
                  onValueChange={([v]) => onChange({ ...filters, maxExperience: v })}
                  min={0}
                  max={15}
                  step={1}
                />
              </div>
            </div>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
