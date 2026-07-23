import { Skeleton } from '@/components/ui/skeleton';

export default function JobListSkeleton({ count = 3 }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-xl border border-jm-border bg-jm-card p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 space-y-2">
              <Skeleton className="h-5 w-3/4 bg-jm-elevated" />
              <Skeleton className="h-4 w-1/2 bg-jm-elevated" />
            </div>
            <Skeleton className="h-6 w-20 bg-jm-elevated" />
          </div>
          <Skeleton className="mt-4 h-4 w-full bg-jm-elevated" />
          <Skeleton className="mt-2 h-4 w-5/6 bg-jm-elevated" />
          <div className="mt-4 flex gap-2">
            <Skeleton className="h-9 w-28 bg-jm-elevated" />
            <Skeleton className="h-9 w-28 bg-jm-elevated" />
          </div>
        </div>
      ))}
    </div>
  );
}
