import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Target,
  Map,
  Users,
  FolderKanban,
  BarChart3,
  Settings,
  UserCircle,
  LogOut,
  PlusCircle,
  ListChecks,
  TrendingUp,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '@/hooks/use-auth';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

const adminNav = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/problems', label: 'Problems', icon: FileText },
  { to: '/challenges', label: 'Challenges', icon: Target },
  { to: '/map', label: 'Map', icon: Map },
  { to: '/matching', label: 'Solver Matching', icon: Users },
  { to: '/projects', label: 'Projects', icon: FolderKanban },
  { to: '/impact', label: 'Impact', icon: TrendingUp },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
];

const citizenNav = [
  { to: '/report', label: 'Report a Problem', icon: PlusCircle },
  { to: '/problems', label: 'My Reports', icon: ListChecks },
  { to: '/impact', label: 'My Impact', icon: TrendingUp },
];

export function Sidebar({ open, onClose }: SidebarProps) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const navItems = user?.role === 'CITIZEN' ? citizenNav : adminNav;

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
  };

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={cn(
          'fixed left-0 top-0 z-50 h-screen w-64 transform border-r border-border bg-card transition-transform duration-300 lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex items-center gap-2.5 px-5 py-5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
              <Sparkles className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="font-heading text-lg font-bold leading-none text-foreground">
                SAMARTH
              </h1>
              <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                Challenge Platform
              </p>
            </div>
          </div>

          <Separator />

          {/* Nav */}
          <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={onClose}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                    )
                  }
                >
                  <Icon className="h-4.5 w-4.5 shrink-0" style={{ width: '1.125rem', height: '1.125rem' }} />
                  {item.label}
                </NavLink>
              );
            })}
          </nav>

          <Separator />

          {/* Bottom */}
          <div className="space-y-1 p-3">
            <NavLink
              to="/profile"
              onClick={onClose}
              className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            >
              <UserCircle className="h-4.5 w-4.5" style={{ width: '1.125rem', height: '1.125rem' }} />
              Profile
            </NavLink>
            <NavLink
              to="/settings"
              onClick={onClose}
              className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            >
              <Settings className="h-4.5 w-4.5" style={{ width: '1.125rem', height: '1.125rem' }} />
              Settings
            </NavLink>
            <Button
              variant="ghost"
              onClick={handleSignOut}
              className="w-full justify-start gap-3 text-muted-foreground hover:text-foreground"
            >
              <LogOut className="h-4.5 w-4.5" style={{ width: '1.125rem', height: '1.125rem' }} />
              Sign Out
            </Button>
          </div>
        </div>
      </aside>
    </>
  );
}
