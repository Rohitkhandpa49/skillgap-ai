export interface ApiResponse<T = unknown> {
  success: true;
  data: T;
  message?: string;
}

export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
  requestId?: string;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: PaginationMeta;
}

export interface ResumeUploadResponseData {
  resumeId: string;
  filename: string;
  status: string;
  fileSize: number;
  mimeType: string;
}

export interface CandidateSkillDTO {
  id?: string;
  name: string;
  normalizedName: string;
  confidence: number;
  evidence?: string | null;
  sourceSection?: string | null;
}

export interface CandidateProfileDTO {
  id: string;
  userId: string;
  resumeId: string | null;
  summary: string | null;
  analysisVersion: string | null;
  skills: CandidateSkillDTO[];
  createdAt: Date;
  updatedAt: Date;
}

export interface JobSummaryDTO {
  id: string;
  title: string;
  normalizedTitle: string;
  jobType: string | null;
  location: string | null;
  minExperienceYears: number | null;
  maxExperienceYears: number | null;
  salaryRaw: string | null;
  skills: string[];
}

export interface JobDetailDTO extends JobSummaryDTO {
  description: string | null;
  source: string | null;
  requiredSkills: {
    name: string;
    normalizedName: string;
    importance: number | null;
    isRequired: boolean;
  }[];
}

export interface MatchScoreBreakdown {
  finalScore: number;
  skillOverlapScore: number;
  tfidfSimilarity: number;
  semanticSimilarity: number;
}

export interface MatchDTO {
  id: string;
  candidateProfileId: string;
  jobId: string;
  jobTitle: string;
  jobLocation: string | null;
  scores: MatchScoreBreakdown;
  matchingVersion: string;
  matchedSkills: string[];
  missingSkills: string[];
  explanation?: Record<string, unknown> | null;
  createdAt: Date;
}

export interface DevUserContext {
  userId: string;
  email: string;
  displayName: string;
}
