import type { ChallengeStatus, PriorityLevel, UrgencyLevel } from '@/types';

export function statusColor(status: ChallengeStatus): string {
  const map: Record<ChallengeStatus, string> = {
    NEW: 'bg-slate-100 text-slate-700 border-slate-200',
    UNDER_VALIDATION: 'bg-amber-50 text-amber-700 border-amber-200',
    PRIORITIZED: 'bg-blue-50 text-blue-700 border-blue-200',
    MATCHED: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    SOLUTION_PROPOSED: 'bg-cyan-50 text-cyan-700 border-cyan-200',
    PILOT: 'bg-purple-50 text-purple-700 border-purple-200',
    COMPLETED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  };
  return map[status] ?? 'bg-slate-100 text-slate-700 border-slate-200';
}

export function statusLabel(status: ChallengeStatus): string {
  return status
    .split('_')
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(' ');
}

export function priorityColor(level: PriorityLevel): string {
  const map: Record<PriorityLevel, string> = {
    HIGH: 'bg-red-50 text-red-700 border-red-200',
    MEDIUM: 'bg-orange-50 text-orange-700 border-orange-200',
    LOW: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  };
  return map[level];
}

export function priorityBg(level: PriorityLevel): string {
  const map: Record<PriorityLevel, string> = {
    HIGH: 'bg-red-500',
    MEDIUM: 'bg-orange-500',
    LOW: 'bg-emerald-500',
  };
  return map[level];
}

export function urgencyColor(level: UrgencyLevel): string {
  const map: Record<UrgencyLevel, string> = {
    LOW: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    MEDIUM: 'bg-blue-50 text-blue-700 border-blue-200',
    HIGH: 'bg-orange-50 text-orange-700 border-orange-200',
    CRITICAL: 'bg-red-50 text-red-700 border-red-200',
  };
  return map[level];
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return 'just now';
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return formatDate(iso);
}
