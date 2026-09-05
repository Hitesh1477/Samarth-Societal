import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FolderKanban, ArrowRight, Users2, MapPin } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { api } from '@/services/api';
import type { Project } from '@/types';
import { formatDate } from '@/lib/helpers';

const statusStyles: Record<Project['status'], string> = {
  PROPOSAL: 'bg-slate-100 text-slate-700 border-slate-200',
  ACTIVE: 'bg-blue-50 text-blue-700 border-blue-200',
  PILOT: 'bg-purple-50 text-purple-700 border-purple-200',
  COMPLETED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
};

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getProjects().then((p) => {
      setProjects(p);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-32 animate-pulse rounded-lg bg-muted" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold tracking-tight">Projects</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Solution projects built by university teams and industry partners
        </p>
      </div>

      {projects.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <FolderKanban className="h-10 w-10 text-muted-foreground/50" />
            <p className="mt-4 text-sm text-muted-foreground">No projects yet</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {projects.map((p) => (
            <Link key={p.id} to={`/projects/${p.id}`}>
              <Card className="h-full border-border/60 transition-all hover:border-primary/30 hover:shadow-md">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <h3 className="font-heading font-semibold">{p.title}</h3>
                      <p className="mt-1 text-sm text-muted-foreground">{p.challengeTitle}</p>
                    </div>
                    <Badge variant="outline" className={`shrink-0 text-xs ${statusStyles[p.status]}`}>
                      {p.status}
                    </Badge>
                  </div>

                  <div className="mt-4">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">Progress</span>
                      <span className="font-semibold">{p.progress}%</span>
                    </div>
                    <Progress value={p.progress} className="mt-1.5 h-2" />
                  </div>

                  <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Users2 className="h-3.5 w-3.5" />
                      {p.team.length} members
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3.5 w-3.5" />
                      {p.industryPartner}
                    </span>
                    <span>{formatDate(p.createdAt)}</span>
                  </div>

                  <div className="mt-3 flex justify-end">
                    <Button variant="ghost" size="sm" className="gap-1">
                      Open Workspace
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Button>
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
