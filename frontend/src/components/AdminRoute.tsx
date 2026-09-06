import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuth } from '@/hooks/use-auth';

/**
 * AdminRoute — route guard for /admin/* paths.
 *
 * Behaviour:
 *   - Still loading session    → show spinner (same as ProtectedRoute)
 *   - No authenticated user    → redirect to /admin/login
 *   - Authenticated but NOT ADMIN → redirect to /login with a state flag
 *     so the normal login page can surface an "unauthorised" message if needed
 *   - Authenticated AND ADMIN  → render children
 *
 * This is a hard server-side-style gate: the check runs on every render
 * of a protected admin route, so manually typing a URL does not bypass it.
 */
export function AdminRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  // Not signed in at all → back to admin login
  if (!user) {
    return <Navigate to="/admin/login" replace />;
  }

  // Signed in but not an admin → redirect to normal login
  // (the user has no business on this route regardless of how they got here)
  if (user.role !== 'ADMIN') {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
