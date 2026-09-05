// Centralized API types for SAMARTH platform

export type UserRole =
  | 'CITIZEN'
  | 'GOVERNMENT'
  | 'UNIVERSITY'
  | 'FACULTY'
  | 'STUDENT'
  | 'INDUSTRY'
  | 'ADMIN';

export type ChallengeStatus =
  | 'NEW'
  | 'UNDER_VALIDATION'
  | 'PRIORITIZED'
  | 'MATCHED'
  | 'SOLUTION_PROPOSED'
  | 'PILOT'
  | 'COMPLETED';

export type PriorityLevel = 'HIGH' | 'MEDIUM' | 'LOW';

export type UrgencyLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type ProblemCategory =
  | 'Infrastructure'
  | 'Water & Sanitation'
  | 'Healthcare'
  | 'Education'
  | 'Agriculture'
  | 'Environment'
  | 'Public Safety'
  | 'Transport'
  | 'Waste Management'
  | 'Other';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatarUrl?: string;
}

export interface ProblemReport {
  id: string;
  title: string;
  description: string;
  category: ProblemCategory;
  subcategory: string;
  urgency: UrgencyLevel;
  affectedPopulation: number;
  location: {
    lat: number;
    lng: number;
    name: string;
    district: string;
  };
  evidence: Evidence[];
  status: 'SUBMITTED' | 'ANALYZED' | 'MERGED';
  challengeId?: string;
  similarity?: number;
  distance?: string;
  createdAt: string;
  reporterName: string;
}

export interface Evidence {
  id: string;
  type: 'image' | 'audio' | 'document';
  url: string;
  name: string;
}

export interface AIAnalysis {
  problemId: string;
  structuredStatement: string;
  category: ProblemCategory;
  subcategory: string;
  keywords: string[];
  urgency: UrgencyLevel;
  confidence: number;
  affectedPopulation: number;
  evidenceCount: number;
}

export interface DuplicateReport {
  reportId: string;
  title: string;
  similarity: number;
  distance: string;
  date: string;
  location: string;
  reporter: string;
}

export interface DuplicateCluster {
  problemId: string;
  totalReports: number;
  similarity: number;
  reports: DuplicateReport[];
  unifiedChallengeId: string;
}

export interface PriorityBreakdown {
  safetyRisk: { score: number; max: number };
  populationImpact: { score: number; max: number };
  recurrence: { score: number; max: number };
  evidence: { score: number; max: number };
  locationRisk: { score: number; max: number };
}

export interface PriorityScore {
  challengeId: string;
  total: number;
  level: PriorityLevel;
  breakdown: PriorityBreakdown;
  explanation: string;
}

export interface Challenge {
  id: string;
  title: string;
  category: ProblemCategory;
  subcategory: string;
  location: {
    name: string;
    district: string;
    lat: number;
    lng: number;
  };
  reportCount: number;
  affectedPopulation: number;
  priority: number;
  priorityLevel: PriorityLevel;
  status: ChallengeStatus;
  assignedSolver?: string;
  createdAt: string;
  description: string;
}

export interface ChallengeDetail extends Challenge {
  structuredStatement: string;
  keywords: string[];
  confidence: number;
  timeline: TimelineEvent[];
  duplicateCluster: DuplicateCluster;
  priorityBreakdown: PriorityBreakdown;
  priorityExplanation: string;
  reports: ProblemReport[];
  evidence: Evidence[];
  matchedSolvers: SolverMatch[];
  solution?: Solution;
  pilot?: Pilot;
  impact?: ImpactSummary;
}

export interface TimelineEvent {
  id: string;
  label: string;
  status: 'done' | 'current' | 'pending';
  date?: string;
}

export interface SolverMatch {
  id: string;
  name: string;
  type: 'university' | 'industry';
  department?: string;
  matchScore: number;
  reasons: string[];
  description: string;
}

export interface Solution {
  challengeId: string;
  summary: string;
  approach: string;
  teamMembers: TeamMember[];
  facultyMentor: string;
  industryPartner: string;
  milestones: Milestone[];
  progress: number;
}

export interface TeamMember {
  id: string;
  name: string;
  role: string;
  avatarUrl?: string;
}

export interface Milestone {
  id: string;
  title: string;
  status: 'pending' | 'in_progress' | 'completed';
  progress: number;
  dueDate: string;
  evidenceCount: number;
}

export interface Pilot {
  challengeId: string;
  status: 'planned' | 'active' | 'completed';
  startDate: string;
  endDate?: string;
  location: string;
  participants: number;
}

export interface ImpactMetric {
  id: string;
  label: string;
  before: number;
  after: number;
  unit: string;
  improvement: number;
}

export interface ImpactSummary {
  projectId: string;
  impactScore: number;
  status: string;
  metrics: ImpactMetric[];
  beforeImage: string;
  afterImage: string;
  summary: string;
}

export interface Project {
  id: string;
  challengeId: string;
  challengeTitle: string;
  title: string;
  status: 'PROPOSAL' | 'ACTIVE' | 'PILOT' | 'COMPLETED';
  progress: number;
  team: TeamMember[];
  facultyMentor: string;
  industryPartner: string;
  createdAt: string;
}

export interface DashboardStats {
  totalReports: number;
  validatedChallenges: number;
  highPriority: number;
  activeProjects: number;
  completedPilots: number;
  impactMeasured: number;
  verifiedImpactPercent: number;
}

export interface DashboardData {
  stats: DashboardStats;
  challengesByCategory: { name: string; value: number }[];
  priorityDistribution: { name: string; value: number }[];
  reportsByDistrict: { name: string; value: number }[];
  challengeLifecycle: { stage: string; value: number }[];
  monthlyReports: { month: string; value: number }[];
  mapChallenges: MapChallenge[];
  aiInsights: string[];
}

export interface MapChallenge {
  id: string;
  title: string;
  lat: number;
  lng: number;
  priority: number;
  priorityLevel: PriorityLevel;
  reportCount: number;
  affectedPopulation: number;
  status: ChallengeStatus;
  category: ProblemCategory;
  district: string;
}

export interface MapData {
  challenges: MapChallenge[];
  hotspots: { name: string; count: number }[];
}

export interface ProblemFilters {
  category?: string;
  district?: string;
  priority?: string;
  status?: string;
  search?: string;
}

export interface SubmitProblemData {
  title: string;
  description: string;
  category: ProblemCategory;
  subcategory: string;
  urgency: UrgencyLevel;
  affectedPopulation: number;
  location: {
    lat: number;
    lng: number;
    name: string;
    district: string;
  };
  evidence: Evidence[];
  reporterName: string;
}
