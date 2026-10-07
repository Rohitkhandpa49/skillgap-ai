import { z } from 'zod';

export const PaginationQuerySchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  search: z.string().optional(),
});

export const MatchRequestSchema = z.object({
  topK: z.coerce.number().int().min(1).max(50).default(10),
  candidateProfileId: z.string().uuid().optional(),
});

export const ResumeIdParamSchema = z.object({
  resumeId: z.string().uuid('Invalid resumeId format, must be a UUID'),
});

export const JobIdParamSchema = z.object({
  jobId: z.string().min(1, 'jobId is required'),
});

export const MatchIdParamSchema = z.object({
  matchId: z.string().uuid('Invalid matchId format, must be a UUID'),
});
