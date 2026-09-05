import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  TrendingUp,
  ArrowRight,
  CheckCircle2,
  Image as ImageIcon,
  Sparkles,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { api, isMockApi } from '@/services/api';
import type { ImpactSummary } from '@/types';

export function ImpactDashboardPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [impact, setImpact] = useState<ImpactSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const selectedProjectId = projectId ?? (isMockApi ? 'proj-001' : undefined);
    if (!selectedProjectId) {
      setLoading(false);
      return;
    }

    api.getImpact(selectedProjectId).then((i) => {
      setImpact(i);
      setLoading(false);
    });
  }, [projectId]);

  if (!loading && !impact) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-16 text-center text-sm text-muted-foreground">
          Select a project to view its impact dashboard
        </CardContent>
      </Card>
    );
  }

  if (loading || !impact) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-64 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  const chartData = impact.metrics.map((m) => ({
    name: m.label,
    before: m.before,
    after: m.after,
  }));

  const radialData = [{ name: 'Impact Score', value: impact.impactScore, fill: '#16a34a' }];

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" asChild className="gap-1">
        <Link to={`/projects/${projectId}`}>
          <ArrowLeft className="h-4 w-4" />
          Back to Project
        </Link>
      </Button>

      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-50">
            <TrendingUp className="h-5 w-5 text-emerald-600" />
          </div>
          <div>
            <h1 className="font-heading text-2xl font-bold tracking-tight">Measuring Real-World Impact</h1>
            <p className="text-sm text-muted-foreground">
              Before-and-after metrics proving measurable outcomes
            </p>
          </div>
        </div>
      </div>

      {/* Impact Score + Status */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="border-emerald-200 bg-emerald-50/50 lg:col-span-1">
          <CardContent className="flex flex-col items-center p-6">
            <ResponsiveContainer width="100%" height={180}>
              <RadialBarChart
                data={radialData}
                innerRadius="70%"
                outerRadius="100%"
                dataKey="value"
                startAngle={90}
                endAngle={-270}
              >
                <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
                <RadialBar background dataKey="value" cornerRadius={10} fill="#16a34a" />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="-mt-28 text-center">
              <p className="font-heading text-4xl font-bold text-emerald-600">
                {impact.impactScore}
              </p>
              <p className="text-xs text-muted-foreground">/ 100 Impact Score</p>
            </div>
            <Badge
              variant="outline"
              className="mt-20 border-emerald-300 bg-emerald-100 text-emerald-700"
            >
              <CheckCircle2 className="mr-1 h-3 w-3" />
              {impact.status}
            </Badge>
          </CardContent>
        </Card>

        {/* Summary */}
        <Card className="border-border/60 lg:col-span-2">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <CardTitle className="text-base">Impact Summary</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed text-muted-foreground">{impact.summary}</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {impact.metrics.map((m) => (
                <div key={m.id} className="rounded-lg border border-border/60 p-3">
                  <p className="text-xs text-muted-foreground">{m.label}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-sm font-semibold text-red-600">{m.before}{m.unit}</span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                    <span className="text-sm font-semibold text-emerald-600">{m.after}{m.unit}</span>
                  </div>
                  <div className="mt-2">
                    <Progress value={m.improvement} className="h-1.5" />
                    <p className="mt-1 text-xs text-emerald-600">{m.improvement}% improvement</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Before/After Chart */}
      <Card className="border-border/60">
        <CardHeader>
          <CardTitle className="text-base">Before vs After Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
              />
              <Bar dataKey="before" fill="#dc2626" radius={[4, 4, 0, 0]} name="Before" barSize={28} />
              <Bar dataKey="after" fill="#16a34a" radius={[4, 4, 0, 0]} name="After" barSize={28} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Before/After Evidence */}
      <Card className="border-border/60">
        <CardHeader>
          <CardTitle className="text-base">Evidence: Before & After</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <p className="mb-2 text-sm font-medium text-red-600">Before</p>
              <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-red-200 bg-red-50/30">
                <div className="text-center">
                  <ImageIcon className="mx-auto h-8 w-8 text-muted-foreground/50" />
                  <p className="mt-2 text-xs text-muted-foreground">Before evidence photo</p>
                </div>
              </div>
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-emerald-600">After</p>
              <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-emerald-200 bg-emerald-50/30">
                <div className="text-center">
                  <ImageIcon className="mx-auto h-8 w-8 text-muted-foreground/50" />
                  <p className="mt-2 text-xs text-muted-foreground">After evidence photo</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* CTA */}
      <div className="flex justify-center gap-3 py-2">
        <Button variant="outline" asChild>
          <Link to="/dashboard">Back to Dashboard</Link>
        </Button>
        <Button variant="outline" asChild className="gap-2">
          <Link to="/challenges">
            View All Challenges
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    </div>
  );
}
