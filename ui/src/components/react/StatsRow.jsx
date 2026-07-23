import { useStore } from '@nanostores/react';
import { Card, CardContent } from '@/components/ui/card';
import { jobsStore, candidateLevelStore } from '@/stores/appStore.js';

export default function StatsRow() {
  const jobs = useStore(jobsStore);
  const level = useStore(candidateLevelStore);

  const total = jobs.length;
  const matchCount = jobs.filter((j) => j.english_match).length;
  const savedCount = 0; // fetched separately

  const stats = [
    { label: 'Total ofertas', value: total },
    { label: 'Match inglés', value: matchCount },
    { label: 'Tu nivel', value: level || '—' },
  ];

  if (total === 0) return null;

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {stats.map((s) => (
        <Card key={s.label} className="border-jm-border bg-gradient-to-br from-jm-surface to-jm-card">
          <CardContent className="p-4">
            <p className="text-xs font-medium uppercase tracking-wider text-jm-text-muted">{s.label}</p>
            <p className="mt-1 text-2xl font-bold text-jm-text-bright">{s.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
