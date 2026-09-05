import { Badge } from '@/components/ui/badge';
import { statusColor, statusLabel, priorityColor, priorityBg } from '@/lib/helpers';
import type { ChallengeStatus, PriorityLevel } from '@/types';
import { cn } from '@/lib/utils';

export function StatusBadge({ status }: { status: ChallengeStatus }) {
  return (
    <Badge variant="outline" className={cn('text-xs font-medium', statusColor(status))}>
      {statusLabel(status)}
    </Badge>
  );
}

export function PriorityBadge({ level, score }: { level: PriorityLevel; score?: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className={cn('inline-flex h-2 w-2 rounded-full', priorityBg(level))} />
      <span className="text-sm font-semibold">
        {score !== undefined ? `${score}/100` : level}
      </span>
      <Badge variant="outline" className={cn('text-xs', priorityColor(level))}>
        {level} PRIORITY
      </Badge>
    </div>
  );
}
