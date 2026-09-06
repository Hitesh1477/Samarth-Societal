import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/hooks/use-auth';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { AdminRoute } from '@/components/AdminRoute';
import { AppLayout } from '@/components/layout/AppLayout';
import { Toaster } from '@/components/ui/sonner';
import { LandingPage } from '@/pages/LandingPage';
import { LoginPage } from '@/pages/LoginPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { AdminLoginPage } from '@/pages/AdminLoginPage';
import { ReportProblemPage } from '@/pages/ReportProblemPage';
import { AIAnalysisPage } from '@/pages/AIAnalysisPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { ProblemsPage } from '@/pages/ProblemsPage';
import { ChallengesPage } from '@/pages/ChallengesPage';
import { ChallengeDetailPage } from '@/pages/ChallengeDetailPage';
import { MapPage } from '@/pages/MapPage';
import { SolverMatchingPage } from '@/pages/SolverMatchingPage';
import { ProjectsPage } from '@/pages/ProjectsPage';
import { ProjectDetailPage } from '@/pages/ProjectDetailPage';
import { ImpactDashboardPage } from '@/pages/ImpactDashboardPage';
import { AnalyticsPage } from '@/pages/AnalyticsPage';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Admin login — public but leads nowhere without ADMIN role */}
          <Route path="/admin/login" element={<AdminLoginPage />} />

          {/* Admin-protected routes — AdminRoute enforces role === 'ADMIN' */}
          <Route
            path="/admin/dashboard"
            element={
              <AdminRoute>
                <AppLayout>
                  <DashboardPage />
                </AppLayout>
              </AdminRoute>
            }
          />
          {/* Convenience redirect: /admin → /admin/dashboard */}
          <Route path="/admin" element={<Navigate to="/admin/dashboard" replace />} />

          {/* Protected routes */}
          <Route
            path="/report"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <ReportProblemPage />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/report/:id/analysis"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <AIAnalysisPage />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <DashboardPage />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/problems"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <ProblemsPage />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/challenges"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <ChallengesPage />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/challenges/:id"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <ChallengeDetailPage />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/map"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <MapPage />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/matching/:challengeId"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <SolverMatchingPage />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/matching"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <SolverMatchingPage />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <ProjectsPage />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:id"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <ProjectDetailPage />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/impact/:projectId"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <ImpactDashboardPage />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/impact"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <ImpactDashboardPage />
                </AppLayout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <AnalyticsPage />
                </AppLayout>
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Toaster />
      </BrowserRouter>
    </AuthProvider>
  );
}
