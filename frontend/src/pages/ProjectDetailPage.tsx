import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Users2,
  Building2,
  GraduationCap,
  CheckCircle2,
  Circle,
  Plus,
  Upload,
  MessageSquare,
  Lightbulb,
  FileText,
  ShieldCheck,
  TrendingUp,
  Calendar,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { api, isMockApi } from '@/services/api';
import type { Milestone, Project, Solution } from '@/types';
import { formatDate } from '@/lib/helpers';
import { toast } from 'sonner';

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [solution, setSolution] = useState<Solution | null>(null);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [milestoneTitle, setMilestoneTitle] = useState('');
  const [milestoneError, setMilestoneError] = useState<string | null>(null);
  const [milestoneSubmitting, setMilestoneSubmitting] = useState(false);
  const [milestoneUpdating, setMilestoneUpdating] = useState<string | null>(null);
  const [projectUpdating, setProjectUpdating] = useState(false);
  const [pilotUpdating, setPilotUpdating] = useState(false);

  useEffect(() => {
    const selectedProjectId = id ?? (isMockApi ? 'proj-001' : undefined);
    if (!selectedProjectId) {
      setLoading(false);
      return;
    }

    api.getProject(selectedProjectId).then(async (p) => {
      const s = await api.getSolution(p.challengeId);
      setProject(p);
      setSolution(s);
      setMilestones(s?.milestones ?? []);
      setLoading(false);
    }).catch((err: unknown) => {
      setError(err instanceof Error ? err.message : 'Unable to load project.');
      setLoading(false);
    });
  }, [id]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <FileText className="h-8 w-8 text-destructive" />
        <h2 className="mt-4 font-heading text-xl font-semibold">Project unavailable</h2>
        <p className="mt-2 text-sm text-muted-foreground">{error}</p>
      </div>
    );
  }

  if (loading || !project) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-32 animate-pulse rounded-lg bg-muted" />
        <div className="h-64 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  const completedMilestones = milestones.filter((m) => m.status === 'completed').length;

  const handleUpdateProject = async () => {
    if (projectUpdating) return;
    setProjectUpdating(true);
    try {
      const updated = await api.updateProject(project.id, { status: 'ACTIVE' });
      setProject(updated);
      toast.success('Project status updated');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Unable to update project.');
    } finally {
      setProjectUpdating(false);
    }
  };

  const handleStartPilot = async () => {
    if (pilotUpdating || project.status === 'PILOT') return;
    setPilotUpdating(true);
    try {
      const updated = await api.updateProject(project.id, { status: 'PILOT' });
      setProject(updated);
      toast.success('Project moved to pilot');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Unable to start pilot.');
    } finally {
      setPilotUpdating(false);
    }
  };

  const handleAddFeedback = () => {
    if (!feedback.trim()) return;
    toast.success('Feedback added');
    setFeedback('');
  };

  const handleAddMilestone = async () => {
    if (milestoneSubmitting) return;
    if (!milestoneTitle.trim()) {
      setMilestoneError('Enter a milestone title.');
      return;
    }

    setMilestoneSubmitting(true);
    setMilestoneError(null);
    try {
      const created = await api.createMilestone(project.id, {
        title: milestoneTitle.trim(),
        status: 'pending',
        progress: 0,
        dueDate: '',
        evidenceCount: 0,
      }) as Milestone;
      setMilestones((current) => [...current, created]);
      setMilestoneTitle('');
      const updatedProject = await api.getProject(project.id);
      setProject(updatedProject);
      toast.success('Milestone created');
    } catch (err) {
      setMilestoneError(err instanceof Error ? err.message : 'Unable to create milestone.');
    } finally {
      setMilestoneSubmitting(false);
    }
  };

  const handleUpdateMilestone = async (milestone: Milestone) => {
    if (milestoneUpdating) return;
    const completed = milestone.progress < 100;
    setMilestoneUpdating(milestone.id);
    setMilestoneError(null);
    try {
      const updated = await api.updateMilestone(milestone.id, {
        progress: completed ? 100 : 0,
        status: completed ? 'completed' : 'pending',
      }) as Milestone;
      setMilestones((current) => current.map((item) => item.id === updated.id ? updated : item));
      const updatedProject = await api.getProject(project.id);
      setProject(updatedProject);
      toast.success('Milestone updated');
    } catch (err) {
      setMilestoneError(err instanceof Error ? err.message : 'Unable to update milestone.');
    } finally {
      setMilestoneUpdating(null);
    }
  };

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" asChild className="gap-1">
        <Link to="/projects">
          <ArrowLeft className="h-4 w-4" />
          Back to Projects
        </Link>
      </Button>

      {/* Header */}
      <div>
        <h1 className="font-heading text-2xl font-bold tracking-tight">{project.title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{project.challengeTitle}</p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <Badge variant="outline" className="text-xs">{project.status}</Badge>
          {project.status === 'PROPOSAL' && (
            <Button size="sm" variant="outline" onClick={handleUpdateProject} disabled={projectUpdating}>
              {projectUpdating ? 'Updating...' : 'Activate Project'}
            </Button>
          )}
          <span className="text-sm text-muted-foreground">
            Created {formatDate(project.createdAt)}
          </span>
        </div>
      </div>

      {/* Overview cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-border/60">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground">
              <TrendingUp className="h-4 w-4" />
              <span className="text-xs font-medium uppercase tracking-wide">Progress</span>
            </div>
            <p className="mt-2 text-2xl font-bold">{project.progress}%</p>
            <Progress value={project.progress} className="mt-2 h-2" />
          </CardContent>
        </Card>
        <Card className="border-border/60">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Users2 className="h-4 w-4" />
              <span className="text-xs font-medium uppercase tracking-wide">Team</span>
            </div>
            <p className="mt-2 text-2xl font-bold">{project.team.length}</p>
            <p className="text-xs text-muted-foreground">members</p>
          </CardContent>
        </Card>
        <Card className="border-border/60">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground">
              <GraduationCap className="h-4 w-4" />
              <span className="text-xs font-medium uppercase tracking-wide">Mentor</span>
            </div>
            <p className="mt-2 text-sm font-semibold">{project.facultyMentor}</p>
          </CardContent>
        </Card>
        <Card className="border-border/60">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Building2 className="h-4 w-4" />
              <span className="text-xs font-medium uppercase tracking-wide">Industry</span>
            </div>
            <p className="mt-2 text-sm font-semibold">{project.industryPartner}</p>
          </CardContent>
        </Card>
      </div>

      {/* Team */}
      <Card className="border-border/60">
        <CardHeader>
          <CardTitle className="text-base">Team Members</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {project.team.map((m) => (
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

      {/* Tabs */}
      <Tabs defaultValue="milestones">
        <TabsList className="flex h-auto flex-wrap gap-1">
          <TabsTrigger value="proposal">Proposal</TabsTrigger>
          <TabsTrigger value="milestones">Milestones</TabsTrigger>
          <TabsTrigger value="prototype">Prototype</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="feedback">Feedback</TabsTrigger>
          <TabsTrigger value="pilot">Pilot</TabsTrigger>
        </TabsList>

        {/* Proposal */}
        <TabsContent value="proposal" className="space-y-4">
          {solution && (
            <Card className="border-border/60">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-primary" />
                  <CardTitle className="text-base">Solution Proposal</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-xs text-muted-foreground">Summary</p>
                  <p className="mt-1 text-sm font-medium">{solution.summary}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Approach</p>
                  <p className="mt-1 text-sm leading-relaxed">{solution.approach}</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Milestones */}
        <TabsContent value="milestones" className="space-y-4">
          <Card className="border-border/60">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">
                  Milestones ({completedMilestones}/{milestones.length} completed)
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Input
                    className="w-52"
                    placeholder="Milestone title"
                    value={milestoneTitle}
                    onChange={(e) => setMilestoneTitle(e.target.value)}
                    disabled={milestoneSubmitting}
                  />
                  <Button size="sm" variant="outline" className="gap-2" onClick={handleAddMilestone} disabled={milestoneSubmitting}>
                    <Plus className="h-3.5 w-3.5" />
                    {milestoneSubmitting ? 'Adding...' : 'Add Milestone'}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {milestones.map((m) => (
                <div key={m.id} className="rounded-lg border border-border/60 p-4">
                  <div className="flex items-center gap-3">
                    {m.status === 'completed' ? (
                      <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-600" />
                    ) : (
                      <Circle
                        className={`h-5 w-5 shrink-0 ${
                          m.status === 'in_progress' ? 'text-primary' : 'text-muted-foreground'
                        }`}
                      />
                    )}
                    <div className="flex-1">
                      <p className="text-sm font-medium">{m.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {m.status === 'completed'
                          ? 'Completed'
                          : m.status === 'in_progress'
                          ? 'In Progress'
                          : 'Pending'}
                        {m.dueDate && ` • Due ${formatDate(m.dueDate)}`}
                        {m.evidenceCount > 0 && ` • ${m.evidenceCount} evidence files`}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-20">
                        <Progress value={m.progress} className="h-1.5" />
                      </div>
                      <span className="text-xs font-medium">{m.progress}%</span>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 gap-1 text-xs"
                        onClick={() => toast.success('Evidence upload dialog would open')}
                      >
                        <Upload className="h-3 w-3" />
                        Upload
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-7 gap-1 text-xs"
                        onClick={() => handleUpdateMilestone(m)}
                        disabled={milestoneUpdating !== null}
                      >
                        {milestoneUpdating === m.id ? 'Updating...' : m.progress >= 100 ? 'Reopen' : 'Complete'}
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
          {milestoneError && <p className="text-sm text-destructive">{milestoneError}</p>}
        </TabsContent>

        {/* Prototype */}
        <TabsContent value="prototype" className="space-y-4">
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="h-8 w-8 text-muted-foreground/50" />
              <p className="mt-3 text-sm text-muted-foreground">No prototype uploaded yet</p>
              <Button
                size="sm"
                variant="outline"
                className="mt-3 gap-2"
                onClick={() => toast.success('Prototype upload dialog would open')}
              >
                <Upload className="h-3.5 w-3.5" />
                Upload Prototype
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Documents */}
        <TabsContent value="documents" className="space-y-4">
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="h-8 w-8 text-muted-foreground/50" />
              <p className="mt-3 text-sm text-muted-foreground">No documents uploaded yet</p>
              <Button
                size="sm"
                variant="outline"
                className="mt-3 gap-2"
                onClick={() => toast.success('Document upload dialog would open')}
              >
                <Upload className="h-3.5 w-3.5" />
                Upload Document
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Feedback */}
        <TabsContent value="feedback" className="space-y-4">
          <Card className="border-border/60">
            <CardHeader>
              <div className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-primary" />
                <CardTitle className="text-base">Team Feedback</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Textarea
                  placeholder="Add feedback or comments..."
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  rows={3}
                />
                <div className="flex justify-end">
                  <Button size="sm" onClick={handleAddFeedback} className="gap-2">
                    <MessageSquare className="h-3.5 w-3.5" />
                    Add Feedback
                  </Button>
                </div>
              </div>
              <div className="space-y-3">
                <div className="rounded-lg border border-border/60 p-3">
                  <div className="flex items-center gap-2">
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                      RK
                    </div>
                    <span className="text-sm font-medium">Dr. Rajesh Kumar</span>
                    <span className="text-xs text-muted-foreground">2 days ago</span>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Prototype testing is progressing well. Need to schedule field testing next week.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Pilot */}
        <TabsContent value="pilot" className="space-y-4">
          <Card className="border-border/60">
            <CardHeader>
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-primary" />
                <CardTitle className="text-base">Pilot Phase</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <p className="text-xs text-muted-foreground">Status</p>
                  <Badge variant="outline" className="mt-1">{project.status}</Badge>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Start Date</p>
                  <p className="mt-1 flex items-center gap-1 text-sm font-medium">
                    <Calendar className="h-3.5 w-3.5" />
                    Pending
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Participants</p>
                  <p className="mt-1 text-sm font-medium">2,500</p>
                </div>
              </div>
              {project.status !== 'PILOT' && (
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={handleStartPilot}
                  disabled={pilotUpdating}
                >
                  {pilotUpdating ? 'Starting Pilot...' : 'Start Pilot'}
                </Button>
              )}
              <Button asChild variant="outline" className="mt-4 gap-2">
                <Link to={`/impact/${project.id}`}>
                  <TrendingUp className="h-4 w-4" />
                  View Impact Dashboard
                </Link>
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
