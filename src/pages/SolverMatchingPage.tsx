import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Users,
  Building2,
  GraduationCap,
  CheckCircle2,
  Brain,
  Sparkles,
  Mail,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { api } from '@/services/api';
import type { SolverMatch } from '@/types';
import { toast } from 'sonner';

export function SolverMatchingPage() {
  const { challengeId } = useParams<{ challengeId: string }>();
  const [solvers, setSolvers] = useState<SolverMatch[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSolverMatches(challengeId ?? 'ch-001').then((s) => {
      setSolvers(s);
      setLoading(false);
    });
  }, [challengeId]);

  if (loading || !solvers) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="mt-4 text-sm text-muted-foreground">Finding best solvers...</p>
      </div>
    );
  }

  const universities = solvers.filter((s) => s.type === 'university');
  const industries = solvers.filter((s) => s.type === 'industry');

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" asChild className="gap-1">
        <Link to={`/challenges/${challengeId}`}>
          <ArrowLeft className="h-4 w-4" />
          Back to Challenge
        </Link>
      </Button>

      <div>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Brain className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="font-heading text-2xl font-bold tracking-tight">AI Recommended Solvers</h1>
            <p className="text-sm text-muted-foreground">
              Smart matching based on expertise, capability, and local presence
            </p>
          </div>
        </div>
      </div>

      {/* Universities */}
      <div>
        <div className="mb-3 flex items-center gap-2">
          <GraduationCap className="h-5 w-5 text-primary" />
          <h2 className="font-heading text-lg font-semibold">University Matches</h2>
        </div>
        <div className="space-y-4">
          {universities.map((s, i) => (
            <Card
              key={s.id}
              className={`border-border/60 transition-all hover:shadow-md ${
                i === 0 ? 'border-primary/30 ring-1 ring-primary/10' : ''
              }`}
            >
              <CardContent className="p-5">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      {i === 0 && (
                        <Badge className="bg-primary text-primary-foreground text-xs">
                          BEST MATCH
                        </Badge>
                      )}
                      <h3 className="font-heading text-lg font-semibold">{s.name}</h3>
                    </div>
                    {s.department && (
                      <p className="mt-1 text-sm text-muted-foreground">{s.department}</p>
                    )}
                    <p className="mt-2 text-sm">{s.description}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {s.reasons.map((r) => (
                        <Badge
                          key={r}
                          variant="outline"
                          className="gap-1 text-xs"
                        >
                          <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                          {r}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="shrink-0 text-center sm:text-right">
                    <p className="font-heading text-3xl font-bold text-primary">
                      {s.matchScore}%
                    </p>
                    <p className="text-xs text-muted-foreground">match score</p>
                    <Button
                      size="sm"
                      className="mt-3 gap-2"
                      onClick={() => toast.success(`Invitation sent to ${s.name}`)}
                    >
                      <Mail className="h-3.5 w-3.5" />
                      Invite
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Industry */}
      <div>
        <div className="mb-3 flex items-center gap-2">
          <Building2 className="h-5 w-5 text-primary" />
          <h2 className="font-heading text-lg font-semibold">Industry Partner Matches</h2>
        </div>
        <div className="space-y-4">
          {industries.map((s) => (
            <Card key={s.id} className="border-border/60 transition-all hover:shadow-md">
              <CardContent className="p-5">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex-1">
                    <h3 className="font-heading text-lg font-semibold">{s.name}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">Industry Partner</p>
                    <p className="mt-2 text-sm">{s.description}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {s.reasons.map((r) => (
                        <Badge key={r} variant="outline" className="gap-1 text-xs">
                          <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                          {r}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="shrink-0 text-center sm:text-right">
                    <p className="font-heading text-3xl font-bold text-primary">
                      {s.matchScore}%
                    </p>
                    <p className="text-xs text-muted-foreground">match score</p>
                    <Button
                      size="sm"
                      className="mt-3 gap-2"
                      onClick={() => toast.success(`Invitation sent to ${s.name}`)}
                    >
                      <Mail className="h-3.5 w-3.5" />
                      Invite Partner
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Explanation */}
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="p-5">
          <div className="flex items-start gap-3">
            <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
            <div>
              <p className="text-sm font-semibold text-primary">AI Matching Explanation</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Recommended because this team has experience in drainage modelling, GIS mapping
                and urban infrastructure projects. Match scores are calculated using expertise
                alignment, past project similarity, team availability, and geographic proximity
                to the challenge location.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* CTA */}
      <div className="flex justify-center gap-3 py-2">
        <Button variant="outline" asChild>
          <Link to={`/challenges/${challengeId}`}>Back to Challenge</Link>
        </Button>
        <Button asChild className="gap-2">
          <Link to="/projects">
            View Projects
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    </div>
  );
}
