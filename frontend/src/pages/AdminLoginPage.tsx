import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, Mail, Lock, ArrowRight, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { useAuth } from '@/hooks/use-auth';
import { supabase } from '@/lib/supabase';

/**
 * Admin-only login page at /admin/login.
 *
 * Uses the existing Supabase auth flow (signIn → loadProfileUser).
 * After credentials are verified, the profile role is checked:
 *   - role === 'ADMIN'  → redirect to /admin/dashboard
 *   - any other role    → sign out immediately, show unauthorized message
 *
 * No registration link is present — admin accounts must be provisioned
 * directly in the database.
 */
export function AdminLoginPage() {
  const { signIn, signOut } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // signIn loads the profile from Supabase and stores the typed role
      await signIn(email, password);

      // Re-read the session to get the user id for the role check.
      // supabase is the same client already used by use-auth — no extra requests.
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        setError('Session could not be established. Please try again.');
        setLoading(false);
        return;
      }

      const { data: profile, error: profileError } = await supabase
        .from('profiles')
        .select('role')
        .eq('id', session.user.id)
        .single();

      if (profileError || !profile?.role) {
        await signOut();
        setError('Your profile could not be loaded. Please try again.');
        setLoading(false);
        return;
      }

      if (profile.role !== 'ADMIN') {
        // Not an admin — sign out immediately and show a clear message
        await signOut();
        setError('Access denied. This portal is restricted to administrators only.');
        setLoading(false);
        return;
      }

      // Role confirmed as ADMIN
      navigate('/admin/dashboard', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign in failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-slate-100/50 to-background px-4">
      <div className="w-full max-w-md">
        {/* Logo / branding */}
        <div className="mb-8 text-center">
          <div className="inline-flex flex-col items-center gap-2">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-lg">
              <ShieldCheck className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="font-heading text-xl font-bold leading-none">SAMARTH</h1>
              <p className="mt-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                Admin Portal
              </p>
            </div>
          </div>
        </div>

        <Card className="border-border/60 shadow-lg">
          <CardHeader className="space-y-1">
            <CardTitle className="font-heading text-2xl">Administrator Sign In</CardTitle>
            <CardDescription>
              Restricted access — authorised personnel only
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="admin-email">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="admin-email"
                    type="email"
                    placeholder="admin@example.com"
                    className="pl-9"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="username"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="admin-password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="admin-password"
                    type="password"
                    placeholder="••••••••"
                    className="pl-9"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    required
                  />
                </div>
              </div>

              <Button type="submit" className="w-full gap-2" disabled={loading}>
                {loading ? 'Verifying...' : 'Sign In to Admin Portal'}
                {!loading && <ArrowRight className="h-4 w-4" />}
              </Button>
            </form>

            {/* Intentionally no registration or "create account" link */}
            <p className="mt-6 text-center text-xs text-muted-foreground">
              Standard user?{' '}
              <a href="/login" className="font-medium text-primary hover:underline">
                Go to regular login
              </a>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
