import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import type { Session } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';
import type { UserRole } from '@/types';

interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: UserRole;
}

interface AuthContextValue {
  user: AuthUser | null;
  session: Session | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (name: string, email: string, password: string, role: UserRole) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const STORAGE_KEY = 'samarth_user';

async function loadProfileUser(session: Session): Promise<AuthUser> {
  const { data: profile, error } = await supabase
    .from('profiles')
    .select('name, role')
    .eq('id', session.user.id)
    .single();

  if (error || !profile?.role) {
    throw new Error('Your user profile could not be loaded. Please try again.');
  }

  return {
    id: session.user.id,
    name: profile.name || session.user.email?.split('@')[0] || 'User',
    email: session.user.email || '',
    role: profile.role as UserRole,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    localStorage.removeItem(STORAGE_KEY);

    let mounted = true;

    const syncSession = async (nextSession: Session | null) => {
      if (!mounted) return;
      setSession(nextSession);
      if (!nextSession) {
        localStorage.removeItem(STORAGE_KEY);
        setUser(null);
        return;
      }

      try {
        const profileUser = await loadProfileUser(nextSession);
        if (!mounted) return;
        setUser(profileUser);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(profileUser));
      } catch {
        if (!mounted) return;
        localStorage.removeItem(STORAGE_KEY);
        setUser(null);
      }
    };

    supabase.auth.getSession().then(({ data }) => {
      if (!mounted) return;
      syncSession(data.session).finally(() => {
        if (mounted) setLoading(false);
      });
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, newSession) => {
      void syncSession(newSession);
    });

    return () => {
      mounted = false;
      listener.subscription.unsubscribe();
    };
  }, []);

  const signIn = async (email: string, password: string) => {
    localStorage.removeItem(STORAGE_KEY);
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    if (!data.session) throw new Error('Sign in did not create a session.');
    const profileUser = await loadProfileUser(data.session);
    setSession(data.session);
    setUser(profileUser);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profileUser));
  };

  const signUp = async (name: string, email: string, password: string, role: UserRole) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { name, role } },
    });
    if (error) {
      throw new Error(`Account registration failed: ${error.message}`);
    }

    if (!data.user) {
      throw new Error('Registration succeeded, but the user profile could not be created. Please try again.');
    }

    if (!data.session) {
      throw new Error('Account created. Please confirm your email, then sign in.');
    }
    const profileUser = await loadProfileUser(data.session);
    setSession(data.session);
    setUser(profileUser);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profileUser));
  };

  const signOut = async () => {
    localStorage.removeItem(STORAGE_KEY);
    await supabase.auth.signOut();
    setSession(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, session, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
