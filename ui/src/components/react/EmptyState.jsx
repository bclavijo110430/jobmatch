import { Card, CardContent } from '@/components/ui/card';

export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <Card className="border-dashed border-jm-border-light bg-jm-surface/50">
      <CardContent className="flex flex-col items-center justify-center py-12 text-center">
        {Icon && (
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-jm-primary-soft">
            <Icon className="h-7 w-7 text-jm-primary-light" />
          </div>
        )}
        <h3 className="text-lg font-semibold text-jm-text-bright">{title}</h3>
        <p className="mt-1 max-w-md text-sm text-jm-text-secondary">{description}</p>
        {action && <div className="mt-5">{action}</div>}
      </CardContent>
    </Card>
  );
}
