import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  MapPin,
  Users2,
  Target,
  FileText,
  CheckCircle2,
  Circle,
  Brain,
  Image as ImageIcon,
  Users,
  Lightbulb,
  ShieldCheck,
  TrendingUp,
  Calendar,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { StatusBadge, PriorityBadge } from '@/components/shared/Badges';
import { api, isMockApi } from '@/services/api';
import type { ChallengeDetail } from '@/types';
import { urgencyColor, formatDate } from '@/lib/helpers';
import { toast } from 'sonner';

export function ChallengeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [challenge, setChallenge] = useState<ChallengeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [creatingProject, setCreatingProject] = useState(false);
  const [projectError, setProjectError] = useState<string | null>(null);

  useEffect(() => {
    const selectedChallengeId = id ?? (isMockApi ? 'ch-001' : undefined);
    if (!selectedChallengeId) {
      setLoading(false);
      return;
    }

    api.getChallenge(selectedChallengeId).then((c) => {
      setChallenge(c);
      setLoading(false);
    });
  }, [id]);

  if (loading || !challenge) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-32 animate-pulse rounded-lg bg-muted" />
        <div className="h-64 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  const breakdown = challenge.priorityBreakdown;
  const breakdownItems = [
    { label: 'Safety Risk', ...breakdown.safetyRisk },
    { label: 'Population Impact', ...breakdown.populationImpact },
    { label: 'Recurrence', ...breakdown.recurrence },
    { label: 'Evidence', ...breakdown.evidence },
    { label: 'Location Risk', ...breakdown.locationRisk },
  ];

  const handleCreateProject = async () => {
    if (creatingProject) return;

    setCreatingProject(true);
    setProjectError(null);
    const selectedSolver = challenge.matchedSolvers[0];
    try {
      const project = await api.createProject({
        challengeId: challenge.id,
        title: `${challenge.title} Solution Project`,
        team: selectedSolver
          ? [{
              id: selectedSolver.id,
              name: selectedSolver.name,
              role: selectedSolver.type === 'university' ? 'University Solver' : 'Industry Partner',
            }]
          : [],
        facultyMentor: selectedSolver?.type === 'university' ? selectedSolver.name : '',
        industryPartner: selectedSolver?.type === 'industry' ? selectedSolver.name : '',
      });
      toast.success('Solution project created');
      navigate(`/projects/${project.id}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to create solution project.';
      setProjectError(message);
      toast.error(message);
    } finally {
      setCreatingProject(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Back */}
      <Button variant="ghost" size="sm" asChild className="gap-1">
        <Link to="/challenges">
          <ArrowLeft className="h-4 w-4" />
          Back to Challenges
        </Link>
      </Button>

      {/* Header */}
      <div>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="font-heading text-2xl font-bold tracking-tight">{challenge.title}</h1>
            <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                {challenge.location.name}, {challenge.location.district}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <FileText className="h-4 w-4" />
                {challenge.reportCount} reports
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Users2 className="h-4 w-4" />
                {challenge.affectedPopulation.toLocaleString()} affected
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={challenge.status} />
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-border/60">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">Priority Score</p>
            <div className="mt-1">
              <PriorityBadge level={challenge.priorityLevel} score={challenge.priority} />
            </div>
          </CardContent>
        </Card>
        <Card className="border-border/60">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">Reports</p>
            <p className="mt-1 text-xl font-bold">{challenge.reportCount}</p>
          </CardContent>
        </Card>
        <Card className="border-border/60">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">Affected Population</p>
            <p className="mt-1 text-xl font-bold">{challenge.affectedPopulation.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card className="border-border/60">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">Assigned Solver</p>
            <p className="mt-1 text-sm font-medium">{challenge.assignedSolver ?? 'Not assigned'}</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList className="flex h-auto flex-wrap gap-1">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
          <TabsTrigger value="analysis">AI Analysis</TabsTrigger>
          <TabsTrigger value="evidence">Evidence</TabsTrigger>
          <TabsTrigger value="solvers">Matched Solvers</TabsTrigger>
          <TabsTrigger value="solution">Solution</TabsTrigger>
          <TabsTrigger value="pilot">Pilot</TabsTrigger>
          <TabsTrigger value="impact">Impact</TabsTrigger>
        </TabsList>

        {/* Overview */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            {/* Structured Statement */}
            <Card className="border-border/60">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Brain className="h-4 w-4 text-primary" />
                  <CardTitle className="text-base">Structured Problem Statement</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed text-foreground">{challenge.structuredStatement}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {challenge.keywords.map((kw) => (
                    <Badge key={kw} variant="secondary" className="text-xs">{kw}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Priority Breakdown */}
            <Card className="border-border/60">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Target className="h-4 w-4 text-primary" />
                    <CardTitle className="text-base">Explainable Priority Score</CardTitle>
                  </div>
                  <Badge variant="outline" className="border-red-200 bg-red-50 text-red-700">
                    {challenge.priorityLevel} PRIORITY
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <p className="font-heading text-4xl font-bold text-primary">{challenge.priority}</p>
                    <p className="text-xs text-muted-foreground">/ 100</p>
                  </div>
                  <p className="flex-1 text-sm text-muted-foreground">{challenge.priorityExplanation}</p>
                </div>
                <div className="space-y-3">
                  {breakdownItems.map((item) => (
                    <div key={item.label}>
                      <div className="flex justify-between text-xs">
                        <span className="font-medium">{item.label}</span>
                        <span className="text-muted-foreground">{item.score} / {item.max}</span>
                      </div>
                      <Progress value={(item.score / item.max) * 100} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Timeline */}
          <Card className="border-border/60">
            <CardHeader>
              <CardTitle className="text-base">Challenge Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap items-center gap-2">
                {challenge.timeline.map((t, i) => {
                  const Icon = t.status === 'done' ? CheckCircle2 : t.status === 'current' ? Circle : Circle;
                  return (
                    <div key={t.id} className="flex items-center gap-2">
                      <div className={`flex flex-col items-center gap-1 ${t.status === 'pending' ? 'opacity-40' : ''}`}>
                        <div className={`flex h-8 w-8 items-center justify-center rounded-full ${
                          t.status === 'done' ? 'bg-emerald-100 text-emerald-600' :
                          t.status === 'current' ? 'bg-primary text-primary-foreground' :
                          'bg-secondary text-muted-foreground'
                        }`}>
                          <Icon className="h-4 w-4" />
                        </div>
                        <span className="max-w-[80px] text-center text-[10px] font-medium leading-tight">{t.label}</span>
                      </div>
                      {i < challenge.timeline.length - 1 && (
                        <div className={`h-0.5 w-6 ${t.status === 'done' ? 'bg-emerald-300' : 'bg-border'}`} />
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Reports */}
        <TabsContent value="reports" className="space-y-3">
          {challenge.reports.map((r) => (
            <Card key={r.id} className="border-border/60">
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <h4 className="font-medium">"{r.title}"</h4>
                    <p className="mt-1 text-sm text-muted-foreground">{r.description}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                      <Badge variant="outline" className={`text-xs ${urgencyColor(r.urgency)}`}>{r.urgency}</Badge>
                      <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{r.location.name}</span>
                      <span>{r.reporterName}</span>
                      <span>{formatDate(r.createdAt)}</span>
                    </div>
                  </div>
                  {r.similarity && (
                    <div className="shrink-0 text-right">
                      <p className="text-lg font-bold text-primary">{r.similarity}%</p>
                      <p className="text-xs text-muted-foreground">similarity</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* AI Analysis */}
        <TabsContent value="analysis" className="space-y-4">
          <Card className="border-primary/20 bg-primary/5">
            <CardContent className="p-6">
              <div className="mb-3 flex items-center gap-2">
                <Brain className="h-4 w-4 text-primary" />
                <span className="text-sm font-semibold text-primary">AI Analysis Summary</span>
              </div>
              <p className="text-base leading-relaxed">{challenge.structuredStatement}</p>
              <div className="mt-4 grid gap-4 sm:grid-cols-3">
                <div>
                  <p className="text-xs text-muted-foreground">Category</p>
                  <p className="font-medium">{challenge.category}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Confidence</p>
                  <p className="font-medium">{challenge.confidence}%</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Duplicate Cluster</p>
                  <p className="font-medium">{challenge.duplicateCluster.totalReports} reports, {challenge.duplicateCluster.similarity}% similarity</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Evidence */}
        <TabsContent value="evidence" className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {challenge.evidence.map((ev) => (
              <Card key={ev.id} className="overflow-hidden border-border/60">
                <div className="flex h-32 items-center justify-center bg-secondary">
                  <ImageIcon className="h-8 w-8 text-muted-foreground" />
                </div>
                <CardContent className="p-2">
                  <p className="truncate text-xs text-muted-foreground">{ev.name}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Matched Solvers */}
        <TabsContent value="solvers" className="space-y-4">
          {challenge.matchedSolvers.map((s, i) => (
            <Card key={s.id} className={`border-border/60 ${i === 0 ? 'border-primary/30' : ''}`}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      {i === 0 && <Badge className="bg-primary text-primary-foreground text-xs">BEST MATCH</Badge>}
                      <h4 className="font-semibold">{s.name}</h4>
                    </div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {s.type === 'university' ? 'University' : 'Industry Partner'}
                      {s.department ? ` • ${s.department}` : ''}
                    </p>
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
                  <div className="shrink-0 text-center">
                    <p className="font-heading text-3xl font-bold text-primary">{s.matchScore}%</p>
                    <p className="text-xs text-muted-foreground">match score</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          <div className="flex justify-center gap-3">
            <Button asChild className="gap-2">
              <Link to={`/matching/${challenge.id}`}>
                <Users className="h-4 w-4" />
                View Full Solver Matching
              </Link>
            </Button>
          </div>
        </TabsContent>

        {/* Solution */}
        <TabsContent value="solution" className="space-y-4">
          {challenge.solution ? (
            <>
              <Card className="border-border/60">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Lightbulb className="h-4 w-4 text-primary" />
                    <CardTitle className="text-base">Proposed Solution</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm font-semibold">{challenge.solution.summary}</p>
                    <p className="mt-2 text-sm text-muted-foreground">{challenge.solution.approach}</p>
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">Overall Progress</span>
                      <span className="font-bold text-primary">{challenge.solution.progress}%</span>
                    </div>
                    <Progress value={challenge.solution.progress} className="mt-2 h-3" />
                  </div>
                </CardContent>
              </Card>

              <Card className="border-border/60">
                <CardHeader>
                  <CardTitle className="text-base">Team</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {challenge.solution.teamMembers.map((m) => (
                      <div key={m.id} className="flex items-center gap-3 rounded-lg border border-border/60 p-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                          {m.name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                        </div>
                        <div>
                          <p className="text-sm font-medium">{m.name}</p>
                          <p className="text-xs text-muted-foreground">{m.role}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card className="border-border/60">
                <CardHeader>
                  <CardTitle className="text-base">Milestones</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {challenge.solution.milestones.map((m) => (
                    <div key={m.id} className="flex items-center gap-4 rounded-lg border border-border/60 p-3">
                      {m.status === 'completed' ? (
                        <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
                      ) : (
                        <Circle className={`h-5 w-5 shrink-0 ${m.status === 'in_progress' ? 'text-primary' : 'text-muted-foreground'}`} />
                      )}
                      <div className="flex-1">
                        <p className="text-sm font-medium">{m.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {m.status === 'completed' ? 'Completed' : m.status === 'in_progress' ? 'In Progress' : 'Pending'}
                          {m.dueDate && ` • Due ${formatDate(m.dueDate)}`}
                        </p>
                      </div>
                      <div className="w-24">
                        <Progress value={m.progress} className="h-1.5" />
                      </div>
                      <span className="text-xs font-medium">{m.progress}%</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                <p className="text-sm text-muted-foreground">No solution proposed yet</p>
                <Button className="mt-4" onClick={handleCreateProject} disabled={creatingProject}>
                  {creatingProject ? 'Creating Project...' : 'Start Solution Project'}
                </Button>
                {projectError && <p className="mt-3 text-sm text-destructive">{projectError}</p>}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Pilot */}
        <TabsContent value="pilot" className="space-y-4">
          {challenge.pilot ? (
            <Card className="border-border/60">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-primary" />
                  <CardTitle className="text-base">Pilot Program</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid gap-4 sm:grid-cols-3">
                  <div>
                    <p className="text-xs text-muted-foreground">Status</p>
                    <Badge variant="outline" className="mt-1 capitalize">{challenge.pilot.status}</Badge>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Start Date</p>
                    <p className="mt-1 flex items-center gap-1 text-sm font-medium">
                      <Calendar className="h-3.5 w-3.5" />
                      {formatDate(challenge.pilot.startDate)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Participants</p>
                    <p className="mt-1 text-sm font-medium">{challenge.pilot.participants.toLocaleString()}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="border-dashed">
              <CardContent className="py-16 text-center text-sm text-muted-foreground">
                Pilot not yet started
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Impact */}
        <TabsContent value="impact" className="space-y-4">
          {challenge.impact ? (
            <Card className="border-border/60">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-primary" />
                  <CardTitle className="text-base">Impact Summary</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <p className="font-heading text-4xl font-bold text-emerald-600">{challenge.impact.impactScore}</p>
                    <p className="text-xs text-muted-foreground">/ 100 Impact Score</p>
                  </div>
                  <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700">
                    {challenge.impact.status}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{challenge.impact.summary}</p>
                {challenge.impact.projectId && (
                  <Button asChild variant="outline" className="gap-2">
                    <Link to={`/impact/${challenge.impact.projectId}`}>
                      <TrendingUp className="h-4 w-4" />
                      View Full Impact Dashboard
                    </Link>
                  </Button>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card className="border-dashed">
              <CardContent className="py-16 text-center text-sm text-muted-foreground">
                Impact not yet measured
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
