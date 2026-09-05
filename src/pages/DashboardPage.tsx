import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Target,
  AlertTriangle,
  FolderKanban,
  ShieldCheck,
  TrendingUp,
  Sparkles,
  ArrowRight,
  Brain,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { StatCard } from '@/components/shared/StatCard';
import { api } from '@/services/api';
import type { DashboardData } from '@/types';

const chartColors = ['#1e3a8a', '#0284c7', '#16a34a', '#f59e0b', '#dc2626', '#7c3aed', '#0891b2', '#be185d'];

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboardStats().then((d) => {
      setData(d);
      setLoading(false);
    });
  }, []);

  if (loading || !data) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 animate-pulse rounded bg-muted" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-32 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="h-72 animate-pulse rounded-lg bg-muted" />
          <div className="h-72 animate-pulse rounded-lg bg-muted" />
        </div>
      </div>
    );
  }

  const stats = [
    { label: 'Total Reports', value: data.stats.totalReports.toLocaleString(), icon: FileText, color: 'text-blue-600' },
    { label: 'Validated Challenges', value: data.stats.validatedChallenges, icon: Target, color: 'text-indigo-600' },
    { label: 'High Priority', value: data.stats.highPriority, icon: AlertTriangle, color: 'text-red-600' },
    { label: 'Active Projects', value: data.stats.activeProjects, icon: FolderKanban, color: 'text-cyan-600' },
    { label: 'Completed Pilots', value: data.stats.completedPilots, icon: ShieldCheck, color: 'text-emerald-600' },
    { label: 'Verified Impact', value: `${data.stats.verifiedImpactPercent}%`, icon: TrendingUp, color: 'text-green-600' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
          <Sparkles className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h1 className="font-heading text-2xl font-bold tracking-tight">Societal Challenge Intelligence</h1>
          <p className="text-sm text-muted-foreground">Real-time overview of challenges across Jharkhand</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((s) => (
          <StatCard key={s.label} {...s} />
        ))}
      </div>

      {/* Charts row 1 */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Challenges by Category */}
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="text-base">Challenges by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data.challengesByCategory} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} stroke="#94a3b8" width={80} />
                <Tooltip
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                />
                <Bar dataKey="value" fill="#1e3a8a" radius={[0, 4, 4, 0]} barSize={18} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Priority Distribution */}
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="text-base">Priority Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={data.priorityDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                  labelLine={false}
                  style={{ fontSize: '12px' }}
                >
                  {data.priorityDistribution.map((_, i) => (
                    <Cell key={i} fill={chartColors[i % chartColors.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Charts row 2 */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Reports by District */}
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="text-base">Reports by District</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data.reportsByDistrict}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }} />
                <Bar dataKey="value" fill="#0284c7" radius={[4, 4, 0, 0]} barSize={32} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Monthly Reports */}
        <Card className="border-border/60">
          <CardHeader>
            <CardTitle className="text-base">Monthly Reports Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={data.monthlyReports}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }} />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#1e3a8a"
                  strokeWidth={2.5}
                  dot={{ fill: '#1e3a8a', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Challenge Lifecycle + AI Insights */}
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="border-border/60 lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Challenge Lifecycle</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={data.challengeLifecycle}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="stage" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 12 }} stroke="#94a3b8" />
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }} />
                <Bar dataKey="value" fill="#16a34a" radius={[4, 4, 0, 0]} barSize={28} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* AI Insights */}
        <Card className="border-primary/20 bg-primary/5">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              <CardTitle className="text-base text-primary">AI Insights</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.aiInsights.map((insight, i) => (
              <div key={i} className="flex items-start gap-2 rounded-lg border border-primary/10 bg-card p-3">
                <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                <p className="text-sm text-foreground">{insight}</p>
              </div>
            ))}
            <Link to="/challenges" className="flex items-center gap-1 text-sm font-medium text-primary hover:underline">
              View all challenges
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Map Hotspots */}
      <Card className="border-border/60">
        <CardHeader>
          <CardTitle className="text-base">Jharkhand Problem Hotspots</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {data.mapChallenges
              .reduce((acc, c) => {
                const existing = acc.find((a) => a.district === c.district);
                if (existing) {
                  existing.count += 1;
                } else {
                  acc.push({ district: c.district, count: 1, maxPriority: c.priority });
                }
                return acc;
              }, [] as { district: string; count: number; maxPriority: number }[])
              .sort((a, b) => b.count - a.count)
              .map((h) => (
                <Link
                  key={h.district}
                  to="/map"
                  className="flex items-center justify-between rounded-lg border border-border/60 p-4 transition-all hover:border-primary/30 hover:shadow-md"
                >
                  <div>
                    <p className="font-semibold">{h.district}</p>
                    <p className="text-sm text-muted-foreground">{h.count} challenges</p>
                  </div>
                  <Badge variant="outline" className="border-red-200 bg-red-50 text-red-700">
                    {h.maxPriority}/100
                  </Badge>
                </Link>
              ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
