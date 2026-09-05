"""
Shared enums — mirror of the TypeScript types in frontend/src/types/index.ts.

Field names and values are kept identical to the frontend so that JSON
serialisation round-trips cleanly.
"""

from enum import Enum


class UserRole(str, Enum):
    CITIZEN = "CITIZEN"
    GOVERNMENT = "GOVERNMENT"
    UNIVERSITY = "UNIVERSITY"
    FACULTY = "FACULTY"
    STUDENT = "STUDENT"
    INDUSTRY = "INDUSTRY"
    ADMIN = "ADMIN"


class ChallengeStatus(str, Enum):
    NEW = "NEW"
    UNDER_VALIDATION = "UNDER_VALIDATION"
    PRIORITIZED = "PRIORITIZED"
    MATCHED = "MATCHED"
    SOLUTION_PROPOSED = "SOLUTION_PROPOSED"
    PILOT = "PILOT"
    COMPLETED = "COMPLETED"


class PriorityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class UrgencyLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ProblemCategory(str, Enum):
    INFRASTRUCTURE = "Infrastructure"
    WATER_SANITATION = "Water & Sanitation"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    AGRICULTURE = "Agriculture"
    ENVIRONMENT = "Environment"
    PUBLIC_SAFETY = "Public Safety"
    TRANSPORT = "Transport"
    WASTE_MANAGEMENT = "Waste Management"
    OTHER = "Other"


class ProblemStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    ANALYZED = "ANALYZED"
    MERGED = "MERGED"


class EvidenceType(str, Enum):
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"


class ProjectStatus(str, Enum):
    PROPOSAL = "PROPOSAL"
    ACTIVE = "ACTIVE"
    PILOT = "PILOT"
    COMPLETED = "COMPLETED"


class MilestoneStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class PilotStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"


class SolverType(str, Enum):
    UNIVERSITY = "university"
    INDUSTRY = "industry"


class TimelineEventStatus(str, Enum):
    DONE = "done"
    CURRENT = "current"
    PENDING = "pending"
