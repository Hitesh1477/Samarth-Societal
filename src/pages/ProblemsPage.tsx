import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Search, MapPin, ArrowRight, Filter } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { api } from '@/services/api';
import type { ProblemReport, ProblemCategory } from '@/types';
import { urgencyColor, timeAgo } from '@/lib/helpers';

const categories: (ProblemCategory | 'all')[] = [
  'all',
  'Infrastructure',
  'Water & Sanitation',
  'Healthcare',
  'Education',
  'Agriculture',
  'Environment',
  'Public Safety',
  'Transport',
  'Waste Management',
  'Other',
];

export function ProblemsPage() {
  const [reports, setReports] = useState<ProblemReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<string>('all');

  useEffect(() => {
    api
      .getProblems({ search, category })
      .then((r) => {
        setReports(r);
        setLoading(false);
      });
  }, [search, category]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold tracking-tight">Problems</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          All citizen-reported problems across the platform
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search problems..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Select value={category} onValueChange={setCategory}>
          <SelectTrigger className="w-full sm:w-48">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {categories.map((c) => (
              <SelectItem key={c} value={c}>
                {c === 'all' ? 'All Categories' : c}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* List */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : reports.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <FileText className="h-10 w-10 text-muted-foreground/50" />
            <p className="mt-4 text-sm text-muted-foreground">No problems found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {reports.map((r) => (
            <Link key={r.id} to={`/report/${r.id}/analysis`}>
              <Card className="border-border/60 transition-all hover:border-primary/30 hover:shadow-md">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <h3 className="font-semibold text-foreground">{r.title}</h3>
                      <p className="mt-1 line-clamp-1 text-sm text-muted-foreground">
                        {r.description}
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                        <Badge variant="outline" className="text-xs">
                          {r.category}
                        </Badge>
                        <Badge variant="outline" className={`text-xs ${urgencyColor(r.urgency)}`}>
                          {r.urgency}
                        </Badge>
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {r.location.name}
                        </span>
                        <span>{r.affectedPopulation.toLocaleString()} affected</span>
                        <span>{timeAgo(r.createdAt)}</span>
                      </div>
                    </div>
                    {r.status === 'ANALYZED' && r.challengeId && (
                      <Button variant="ghost" size="sm" asChild className="shrink-0 gap-1">
                        <Link to={`/challenges/${r.challengeId}`}>
                          View Challenge
                          <ArrowRight className="h-3.5 w-3.5" />
                        </Link>
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
