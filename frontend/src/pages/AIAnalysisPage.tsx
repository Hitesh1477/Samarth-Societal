import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Brain,
  Search,
  Target,
  Users,
  CheckCircle2,
  Loader2,
  ArrowRight,
  Sparkles,
  MapPin,
  AlertCircle,
  FileText,
  Users2,
  TrendingUp,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { api, isMockApi } from '@/services/api';
import type { AIAnalysis, DuplicateCluster, PriorityScore } from '@/types';
import { urgencyColor } from '@/lib/helpers';

const steps = [
  { label: 'Understanding your problem...', icon: Brain },
  { label: 'Checking similar reports...', icon: Search },
  { label: 'Calculating priority...', icon: Target },
  { label: 'Finding potential solvers...', icon: Users },
  { label: 'Challenge ready.', icon: CheckCircle2 },
];

export function AIAnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null);
  const [duplicates, setDuplicates] = useState<DuplicateCluster | null>(null);
  const [priority, setPriority] = useState<PriorityScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      for (let i = 0; i < steps.length; i++) {
        if (cancelled) return;
        setStep(i);
        await new Promise((r) => setTimeout(r, 1000));
      }
      if (cancelled) return;
      const selectedProblemId = id ?? (isMockApi ? 'rpt-001' : undefined);
      if (!selectedProblemId) {
        setLoading(false);
        return;
      }
      try {
        const a = await api.analyzeProblem(selectedProblemId);
        const d = await api.getRelatedProblems(selectedProblemId);
        const p = await api.getPriority(d.unifiedChallengeId ?? selectedProblemId);
        if (cancelled) return;
        setAnalysis(a);
        setDuplicates(d);
        setPriority(p);
        setLoading(false);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Unable to load AI analysis.');
        setLoading(false);
      }
    };
    run();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) {
    return (
      <div className="mx-auto flex max-w-2xl flex-col items-center justify-center py-20 text-center">
        <AlertCircle className="mb-4 h-10 w-10 text-destructive" />
        <h2 className="font-heading text-2xl font-bold">Analysis unavailable</h2>
        <p className="mt-2 text-sm text-muted-foreground">{error}</p>
      </div>
    );
  }

  if (loading || !analysis || !priority) {
    return (
      <div className="mx-auto flex max-w-2xl flex-col items-center justify-center py-20">
        <div className="relative mb-8">
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-primary/10">
            <Brain className="h-10 w-10 text-primary animate-pulse-soft" />
          </div>
          <div className="absolute -inset-2 animate-ping rounded-2xl border-2 border-primary/20" />
        </div>
        <h2 className="font-heading text-2xl font-bold">AI Analysis in Progress</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Our AI is processing your report to create a structured challenge
        </p>

        <div className="mt-10 w-full max-w-md space-y-4">
          {steps.map((s, i) => {
            const Icon = s.icon;
            const isDone = i < step;
            const isCurrent = i === step;
            return (
              <div
                key={s.label}
                className={`flex items-center gap-3 rounded-lg border p-3 transition-all ${
                  isDone
                    ? 'border-emerald-200 bg-emerald-50'
                    : isCurrent
                    ? 'border-primary/30 bg-primary/5'
                    : 'border-border bg-card opacity-50'
                }`}
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-lg">
                  {isDone ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                  ) : isCurrent ? (
                    <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  ) : (
                    <Icon className="h-5 w-5 text-muted-foreground" />
                  )}
                </div>
                <span
                  className={`text-sm font-medium ${
                    isDone ? 'text-emerald-700' : isCurrent ? 'text-foreground' : 'text-muted-foreground'
                  }`}
                >
                  {s.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  const unifiedChallengeId = duplicates?.unifiedChallengeId ?? (isMockApi ? 'ch-001' : undefined);

  return (
    <div className="mx-auto max-w-4xl space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
          <Sparkles className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h1 className="font-heading text-2xl font-bold tracking-tight">AI Challenge Analysis</h1>
          <p className="text-sm text-muted-foreground">Structured problem statement generated by AI</p>
        </div>
      </div>

      {/* Structured Statement */}
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="p-6">
          <div className="mb-3 flex items-center gap-2">
            <Brain className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold text-primary">Structured Problem Statement</span>
          </div>
          <p className="text-base leading-relaxed text-foreground">
            {analysis.structuredStatement}
          </p>
        </CardContent>
      </Card>

      {/* Analysis Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card className="border-border/60">
          <CardContent className="p-5">
            <div className="flex items-center gap-2 text-muted-foreground">
              <FileText className="h-4 w-4" />
              <span className="text-xs font-medium uppercase tracking-wide">Category</span>
            </div>
            <p className="mt-2 font-semibold">{analysis.category}</p>
            <p className="text-sm text-muted-foreground">{analysis.subcategory}</p>
          </CardContent>
        </Card>
        <Card className="border-border/60">
          <CardContent className="p-5">
            <div className="flex items-center gap-2 text-muted-foreground">
              <AlertCircle className="h-4 w-4" />
              <span className="text-xs font-medium uppercase tracking-wide">Urgency</span>
            </div>
            <div className="mt-2">
              <Badge variant="outline" className={urgencyColor(analysis.urgency)}>
                {analysis.urgency}
              </Badge>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              Confidence: <span className="font-semibold text-foreground">{Math.round(analysis.confidence * 100)}%</span>
            </p>
          </CardContent>
        </Card>
        <Card className="border-border/60">
          <CardContent className="p-5">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Users2 className="h-4 w-4" />
              <span className="text-xs font-medium uppercase tracking-wide">Affected Population</span>
            </div>
            <p className="mt-2 text-2xl font-bold">{analysis.affectedPopulation.toLocaleString()}</p>
            <p className="text-sm text-muted-foreground">{analysis.evidenceCount} evidence files</p>
          </CardContent>
        </Card>
      </div>

      {/* Keywords */}
      <Card className="border-border/60">
        <CardHeader>
          <CardTitle className="text-base">AI-Extracted Keywords</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {analysis.keywords.map((kw) => (
            <Badge key={kw} variant="secondary" className="bg-secondary text-secondary-foreground">
              {kw}
            </Badge>
          ))}
        </CardContent>
      </Card>

      {/* Duplicate Detection */}
      {duplicates && (
        <Card className="border-border/60">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">
                  {duplicates.reports.length > 0 ? 'Related Reports Detected' : 'No Related Reports Detected'}
                </CardTitle>
                <p className="mt-1 text-sm text-muted-foreground">
                  {duplicates.reports.length > 0
                    ? 'AI found similar reports and merged them into a unified challenge'
                    : 'No similar reports were found for this problem'}
                </p>
              </div>
              {duplicates.reports.length > 0 && <div className="flex items-center gap-3 text-right">
                <div>
                  <p className="text-2xl font-bold text-primary">{duplicates.totalReports}</p>
                  <p className="text-xs text-muted-foreground">citizen reports</p>
                </div>
                <ArrowRight className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-2xl font-bold text-emerald-600">{Math.round(duplicates.similarity * 100)}%</p>
                  <p className="text-xs text-muted-foreground">similarity</p>
                </div>
                <ArrowRight className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-2xl font-bold">1</p>
                  <p className="text-xs text-muted-foreground">unified challenge</p>
                </div>
              </div>}
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {duplicates.reports.slice(0, 5).map((r) => (
              <div
                key={r.reportId}
                className="flex items-center justify-between gap-4 rounded-lg border border-border/60 p-3 transition-colors hover:bg-secondary/50"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">"{r.title}"</p>
                  <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {r.location}
                    </span>
                    <span>{r.distance}</span>
                    <span>{r.reporter}</span>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <div className="w-16">
                    <Progress value={r.similarity * 100} className="h-1.5" />
                  </div>
                  <span className="text-sm font-semibold text-primary">{Math.round(r.similarity * 100)}%</span>
                </div>
              </div>
            ))}
            {duplicates.reports.length > 0 && (
              <div className="flex items-center gap-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                Likely duplicate / related reports merged into unified challenge
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Priority Preview */}
      <Card className="border-border/60">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-primary" />
            <CardTitle className="text-base">Priority Score Preview</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-6">
            <div className="text-center">
              <p className="font-heading text-4xl font-bold text-primary">{priority.total}</p>
              <p className="text-xs text-muted-foreground">/ 100</p>
            </div>
            <div className="flex-1 space-y-2">
              <div>
                <div className="flex justify-between text-xs">
                  <span>Safety Risk</span>
                  <span className="font-medium">{priority.breakdown.safetyRisk.score}/{priority.breakdown.safetyRisk.max}</span>
                </div>
                <Progress value={(priority.breakdown.safetyRisk.score / priority.breakdown.safetyRisk.max) * 100} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-xs">
                  <span>Population Impact</span>
                  <span className="font-medium">{priority.breakdown.populationImpact.score}/{priority.breakdown.populationImpact.max}</span>
                </div>
                <Progress value={(priority.breakdown.populationImpact.score / priority.breakdown.populationImpact.max) * 100} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-xs">
                  <span>Recurrence</span>
                  <span className="font-medium">{priority.breakdown.recurrence.score}/{priority.breakdown.recurrence.max}</span>
                </div>
                <Progress value={(priority.breakdown.recurrence.score / priority.breakdown.recurrence.max) * 100} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-xs">
                  <span>Evidence</span>
                  <span className="font-medium">{priority.breakdown.evidence.score}/{priority.breakdown.evidence.max}</span>
                </div>
                <Progress value={(priority.breakdown.evidence.score / priority.breakdown.evidence.max) * 100} className="h-2" />
              </div>
              <div>
                <div className="flex justify-between text-xs">
                  <span>Location Risk</span>
                  <span className="font-medium">{priority.breakdown.locationRisk.score}/{priority.breakdown.locationRisk.max}</span>
                </div>
                <Progress value={(priority.breakdown.locationRisk.score / priority.breakdown.locationRisk.max) * 100} className="h-2" />
              </div>
            </div>
            <Badge variant="outline" className="border-red-200 bg-red-50 text-red-700">
              {priority.level} PRIORITY
            </Badge>
          </div>
          <p className="mt-4 text-sm text-muted-foreground">{priority.explanation}</p>
        </CardContent>
      </Card>

      {/* CTA */}
      <div className="flex justify-center gap-3 py-4">
        <Button variant="outline" onClick={() => navigate('/problems')}>
          View All Problems
        </Button>
        {unifiedChallengeId ? (
          <Button asChild className="gap-2">
            <Link to={`/challenges/${unifiedChallengeId}`}>
              View Unified Challenge
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        ) : (
          <Button className="gap-2" disabled>
            Unified Challenge Unavailable
          </Button>
        )}
      </div>
    </div>
  );
}
