import type {
  AIAnalysis,
  Challenge,
  ChallengeDetail,
  DashboardData,
  DuplicateCluster,
  ImpactSummary,
  MapData,
  PriorityScore,
  ProblemFilters,
  ProblemReport,
  Project,
  SolverMatch,
  Solution,
  SubmitProblemData,
} from '@/types';
import {
  createMockReport,
  mockAIAnalysis,
  mockChallengeDetail,
  mockChallenges,
  mockDashboardData,
  mockDuplicateCluster,
  mockImpact,
  mockMapData,
  mockPriorityScore,
  mockProjects,
  mockReports,
  mockSolverMatches,
} from './mockData';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string;
const USE_MOCK = (import.meta.env.VITE_USE_MOCK_API as string) === 'true';

async function mockDelay(ms = 800): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function apiCall<T>(
  path: string,
  options?: RequestInit & { mockResponse?: T; mockDelayMs?: number }
): Promise<T> {
  if (USE_MOCK || !API_BASE_URL) {
    await mockDelay(options?.mockDelayMs ?? 600);
    return options?.mockResponse as T;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`API ${res.status}: ${errorBody}`);
  }

  return res.json();
}

export const api = {
  // Problems
  async submitProblem(data: SubmitProblemData): Promise<ProblemReport> {
    return apiCall('/api/problems', {
      method: 'POST',
      body: JSON.stringify(data),
      mockResponse: createMockReport(data),
      mockDelayMs: 1200,
    });
  },

  async getProblem(id: string): Promise<ProblemReport> {
    return apiCall(`/api/problems/${id}`, {
      mockResponse: mockReports.find((r) => r.id === id) ?? mockReports[0],
    });
  },

  async getProblems(filters?: ProblemFilters): Promise<ProblemReport[]> {
    let reports = [...mockReports];
    if (filters?.category && filters.category !== 'all')
      reports = reports.filter((r) => r.category === filters.category);
    if (filters?.district && filters.district !== 'all')
      reports = reports.filter((r) => r.location.district === filters.district);
    if (filters?.search)
      reports = reports.filter((r) =>
        r.title.toLowerCase().includes(filters.search!.toLowerCase())
      );
    return apiCall('/api/problems', { mockResponse: reports });
  },

  async analyzeProblem(id: string): Promise<AIAnalysis> {
    return apiCall(`/api/problems/${id}/analyze`, {
      method: 'POST',
      mockResponse: mockAIAnalysis,
      mockDelayMs: 3000,
    });
  },

  async getRelatedProblems(id: string): Promise<DuplicateCluster> {
    return apiCall(`/api/problems/${id}/duplicates`, {
      mockResponse: mockDuplicateCluster,
      mockDelayMs: 1500,
    });
  },

  // Challenges
  async getChallenges(filters?: ProblemFilters): Promise<Challenge[]> {
    let challenges = [...mockChallenges];
    if (filters?.category && filters.category !== 'all')
      challenges = challenges.filter((c) => c.category === filters.category);
    if (filters?.district && filters.district !== 'all')
      challenges = challenges.filter((c) => c.location.district === filters.district);
    if (filters?.priority && filters.priority !== 'all')
      challenges = challenges.filter((c) => c.priorityLevel === filters.priority);
    if (filters?.status && filters.status !== 'all')
      challenges = challenges.filter((c) => c.status === filters.status);
    if (filters?.search)
      challenges = challenges.filter((c) =>
        c.title.toLowerCase().includes(filters.search!.toLowerCase())
      );
    return apiCall('/api/challenges', { mockResponse: challenges });
  },

  async getChallenge(id: string): Promise<ChallengeDetail> {
    return apiCall(`/api/challenges/${id}`, {
      mockResponse:
        mockChallenges.find((c) => c.id === id)
          ? { ...mockChallengeDetail, ...mockChallenges.find((c) => c.id === id) }
          : mockChallengeDetail,
    });
  },

  async getPriority(id: string): Promise<PriorityScore> {
    return apiCall(`/api/challenges/${id}/priority`, {
      mockResponse: mockPriorityScore,
    });
  },

  // Solver Matching
  async getSolverMatches(challengeId: string): Promise<SolverMatch[]> {
    return apiCall(`/api/challenges/${challengeId}/solver-matches`, {
      mockResponse: mockSolverMatches,
      mockDelayMs: 1500,
    });
  },

  // Projects
  async createProject(data: Partial<Project>): Promise<Project> {
    return apiCall('/api/projects', {
      method: 'POST',
      body: JSON.stringify(data),
      mockResponse: mockProjects[0],
    });
  },

  async getProjects(): Promise<Project[]> {
    return apiCall('/api/projects', { mockResponse: mockProjects });
  },

  async getProject(id: string): Promise<Project> {
    return apiCall(`/api/projects/${id}`, {
      mockResponse: mockProjects.find((p) => p.id === id) ?? mockProjects[0],
    });
  },

  async updateProject(id: string, data: Partial<Project>): Promise<Project> {
    return apiCall(`/api/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      mockResponse: { ...mockProjects[0], ...data, id },
    });
  },

  async getSolution(challengeId: string): Promise<Solution> {
    return apiCall(`/api/challenges/${challengeId}/solution`, {
      mockResponse: mockChallengeDetail.solution!,
    });
  },

  // Milestones
  async createMilestone(projectId: string, data: unknown): Promise<unknown> {
    return apiCall(`/api/projects/${projectId}/milestones`, {
      method: 'POST',
      body: JSON.stringify(data),
      mockResponse: { success: true },
    });
  },

  async updateMilestone(id: string, data: unknown): Promise<unknown> {
    return apiCall(`/api/milestones/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
      mockResponse: { success: true },
    });
  },

  // Impact
  async addImpactMetric(projectId: string, data: unknown): Promise<unknown> {
    return apiCall(`/api/projects/${projectId}/impact`, {
      method: 'POST',
      body: JSON.stringify(data),
      mockResponse: { success: true },
    });
  },

  async getImpact(projectId: string): Promise<ImpactSummary> {
    return apiCall(`/api/projects/${projectId}/impact`, {
      mockResponse: mockImpact,
    });
  },

  // Dashboard
  async getDashboardStats(): Promise<DashboardData> {
    return apiCall('/api/dashboard/stats', {
      mockResponse: mockDashboardData,
    });
  },

  // Map
  async getMapChallenges(): Promise<MapData> {
    return apiCall('/api/map/challenges', {
      mockResponse: mockMapData,
    });
  },
};
