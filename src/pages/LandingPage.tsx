import { Link } from 'react-router-dom';
import {
  Sparkles,
  ArrowRight,
  FileText,
  Brain,
  Target,
  Users,
  MapPin,
  TrendingUp,
  CheckCircle2,
  Zap,
  ShieldCheck,
  Lightbulb,
  Building2,
  GraduationCap,
  HeartPulse,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const workflow = [
  { label: 'REPORT', icon: FileText },
  { label: 'ANALYZE', icon: Brain },
  { label: 'PRIORITIZE', icon: Target },
  { label: 'MATCH', icon: Users },
  { label: 'SOLVE', icon: Lightbulb },
  { label: 'PILOT', icon: ShieldCheck },
  { label: 'MEASURE', icon: TrendingUp },
];

const stats = [
  { value: '1,248', label: 'Problems Reported' },
  { value: '326', label: 'Challenges Created' },
  { value: '84', label: 'High Priority' },
  { value: '47', label: 'Active Projects' },
  { value: '19', label: 'Pilots' },
  { value: '12', label: 'Districts' },
];

const features = [
  {
    icon: Brain,
    title: 'AI Challenge Engine',
    description:
      'Transforms raw citizen reports into structured societal challenges using NLP and categorization.',
  },
  {
    icon: Target,
    title: 'Explainable Priority',
    description:
      'Every challenge gets a transparent priority score with a full breakdown of contributing factors.',
  },
  {
    icon: Users,
    title: 'Smart Solver Matching',
    description:
      'AI recommends the best university departments and industry partners for each challenge.',
  },
  {
    icon: MapPin,
    title: 'Geospatial Intelligence',
    description:
      'Interactive maps reveal problem hotspots and geographic patterns across districts.',
  },
  {
    icon: TrendingUp,
    title: 'Impact Tracking',
    description:
      'Before-and-after metrics prove real-world outcomes — not just project completion.',
  },
  {
    icon: Zap,
    title: 'Duplicate Detection',
    description:
      'AI clusters similar citizen reports into unified challenges, eliminating redundancy.',
  },
];

const roles = [
  { icon: HeartPulse, label: 'Citizens', desc: 'Report problems' },
  { icon: Building2, label: 'Government', desc: 'Validate & prioritize' },
  { icon: GraduationCap, label: 'Universities', desc: 'Propose solutions' },
  { icon: ShieldCheck, label: 'Industry', desc: 'Build & pilot' },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3.5 lg:px-8">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
              <Sparkles className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="font-heading text-lg font-bold leading-none">SAMARTH</h1>
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                Challenge Platform
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" asChild>
              <Link to="/login">Sign In</Link>
            </Button>
            <Button asChild>
              <Link to="/register">Get Started</Link>
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-blue-50/50 via-transparent to-transparent" />
        <div className="absolute right-0 top-0 h-96 w-96 rounded-full bg-blue-100/30 blur-3xl" />
        <div className="absolute left-0 top-40 h-72 w-72 rounded-full bg-emerald-50/40 blur-3xl" />

        <div className="relative mx-auto max-w-7xl px-4 py-20 lg:px-8 lg:py-28">
          <div className="mx-auto max-w-3xl text-center">
            <Badge variant="outline" className="mb-6 border-primary/30 bg-primary/5 text-primary">
              <Sparkles className="mr-1.5 h-3 w-3" />
              AI-Powered Civic Innovation Platform
            </Badge>
            <h1 className="font-heading text-4xl font-extrabold leading-tight tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              Turn Local Problems Into{' '}
              <span className="text-primary">Real Solutions.</span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
              An AI-powered platform connecting communities, government, universities and
              industry to solve real-world societal challenges.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Button size="lg" asChild className="gap-2">
                <Link to="/report">
                  Report a Problem
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link to="/challenges">Explore Challenges</Link>
              </Button>
            </div>
          </div>

          {/* Workflow */}
          <div className="mx-auto mt-16 max-w-5xl">
            <div className="flex flex-wrap items-center justify-center gap-2 lg:gap-4">
              {workflow.map((step, i) => {
                const Icon = step.icon;
                return (
                  <div key={step.label} className="flex items-center gap-2 lg:gap-4">
                    <div className="flex flex-col items-center gap-2">
                      <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-border bg-card shadow-sm transition-transform hover:scale-105">
                        <Icon className="h-5 w-5 text-primary" />
                      </div>
                      <span className="text-xs font-semibold tracking-wide text-muted-foreground">
                        {step.label}
                      </span>
                    </div>
                    {i < workflow.length - 1 && (
                      <ArrowRight className="hidden h-4 w-4 text-muted-foreground/40 lg:block" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y border-border/60 bg-card/50">
        <div className="mx-auto max-w-7xl px-4 py-12 lg:px-8">
          <div className="grid grid-cols-2 gap-6 lg:grid-cols-6">
            {stats.map((s) => (
              <div key={s.label} className="text-center">
                <p className="font-heading text-3xl font-bold text-primary">{s.value}</p>
                <p className="mt-1 text-sm text-muted-foreground">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-7xl px-4 py-20 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-heading text-3xl font-bold tracking-tight">
            A Complete Platform for Societal Innovation
          </h2>
          <p className="mt-3 text-muted-foreground">
            We don't just collect complaints. We convert real-world problems into measurable solutions.
          </p>
        </div>
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <Card key={f.title} className="border-border/60 transition-all hover:shadow-lg hover:-translate-y-0.5">
                <CardContent className="p-6">
                  <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10">
                    <Icon className="h-5.5 w-5.5 text-primary" style={{ width: '1.375rem', height: '1.375rem' }} />
                  </div>
                  <h3 className="mt-4 font-heading text-lg font-semibold">{f.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{f.description}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* Roles */}
      <section className="bg-card/50 border-y border-border/60">
        <div className="mx-auto max-w-7xl px-4 py-16 lg:px-8">
          <h2 className="text-center font-heading text-2xl font-bold">
            Built for Every Stakeholder
          </h2>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {roles.map((r) => {
              const Icon = r.icon;
              return (
                <div key={r.label} className="text-center">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10">
                    <Icon className="h-7 w-7 text-primary" />
                  </div>
                  <h3 className="mt-4 font-heading font-semibold">{r.label}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{r.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-7xl px-4 py-20 lg:px-8">
        <Card className="overflow-hidden border-primary/20 bg-gradient-to-br from-primary to-primary/80">
          <CardContent className="p-10 text-center lg:p-16">
            <h2 className="font-heading text-3xl font-bold text-primary-foreground lg:text-4xl">
              Ready to Solve Real Problems?
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-primary-foreground/80">
              Join the platform that's transforming how communities, universities and industry
              work together to create measurable impact.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Button size="lg" variant="secondary" asChild className="gap-2">
                <Link to="/register">
                  Create an Account
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild className="border-primary-foreground/30 bg-transparent text-primary-foreground hover:bg-primary-foreground/10">
                <Link to="/dashboard">View Dashboard</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/60 bg-card/30">
        <div className="mx-auto max-w-7xl px-4 py-8 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <span className="font-heading font-bold">SAMARTH</span>
              <span className="text-sm text-muted-foreground">— Societal Challenge & Innovation Platform</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Built for Smart India Hackathon
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
