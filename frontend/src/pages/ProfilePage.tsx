import { Link } from 'react-router-dom';
import { Mail, Shield, UserCircle, Settings } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { useAuth } from '@/hooks/use-auth';

function formatRole(role: string) {
  return role
    .split('_')
    .map((part) => part.charAt(0) + part.slice(1).toLowerCase())
    .join(' ');
}

export function ProfilePage() {
  const { user } = useAuth();
  const initials = user?.name
    ? user.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .slice(0, 2)
        .toUpperCase()
    : 'U';

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Profile</h1>
        <p className="text-sm text-muted-foreground">Your account details on SAMARTH</p>
      </div>

      <Card>
        <CardContent className="flex flex-col items-start gap-6 pt-6 sm:flex-row sm:items-center">
          <Avatar className="h-20 w-20">
            <AvatarFallback className="bg-primary text-lg font-semibold text-primary-foreground">
              {initials}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0 flex-1 space-y-1">
            <h2 className="font-heading text-xl font-semibold">{user?.name ?? 'User'}</h2>
            <p className="truncate text-sm text-muted-foreground">{user?.email}</p>
            <Badge variant="outline" className="mt-2">
              {user?.role ? formatRole(user.role) : 'Unknown'}
            </Badge>
          </div>
          <Button asChild variant="outline">
            <Link to="/settings">
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </Link>
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Account information</CardTitle>
          <CardDescription>These values come from your signed-in session</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-3 rounded-lg border border-border p-3">
            <UserCircle className="mt-0.5 h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Full name</p>
              <p className="text-sm font-medium">{user?.name ?? '—'}</p>
            </div>
          </div>
          <div className="flex items-start gap-3 rounded-lg border border-border p-3">
            <Mail className="mt-0.5 h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Email</p>
              <p className="text-sm font-medium">{user?.email ?? '—'}</p>
            </div>
          </div>
          <div className="flex items-start gap-3 rounded-lg border border-border p-3">
            <Shield className="mt-0.5 h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Role</p>
              <p className="text-sm font-medium">{user?.role ? formatRole(user.role) : '—'}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
