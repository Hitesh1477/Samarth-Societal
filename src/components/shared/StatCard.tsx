import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  trend?: string;
  color?: string;
}

export function StatCard({ label, value, icon: Icon, trend, color = 'text-primary' }: StatCardProps) {
  return (
    <Card className="border-border/60 transition-shadow hover:shadow-md">
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary">
            <Icon className={cn('h-5 w-5', color)} />
          </div>
          {trend && (
            <span className="text-xs font-medium text-emerald-600">{trend}</span>
          )}
        </div>
        <p className="mt-4 text-2xl font-bold tracking-tight">{value}</p>
        <p className="mt-1 text-sm text-muted-foreground">{label}</p>
      </CardContent>
    </Card>
  );
}
