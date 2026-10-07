import { z } from 'zod';

export const AISkillSchema = z.object({
  name: z.string(),
  canonical_name: z.string().optional(),
  normalized_name: z.string().optional(),
  confidence: z.number().min(0).max(1),
  evidence: z.union([z.string(), z.array(z.string())]).nullable().optional(),
  source_sections: z.array(z.string()).optional(),
  source_section: z.string().nullable().optional(),
});

export const AICandidateProfileSchema = z.object({
  candidate_id: z.string().nullable().optional(),
  skills: z.array(AISkillSchema).default([]),
  summary: z.string().nullable().optional(),
  experience_years: z.number().nullable().optional(),
  education_level: z.string().nullable().optional(),
  total_skills_count: z.number().optional(),
});

export const AIAnalyzeResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    candidate_profile: AICandidateProfileSchema,
  }),
});

export const AIScoreComponentsSchema = z.object({
  skill_overlap: z.number().min(0).max(1),
  tfidf_similarity: z.number().min(0).max(1).nullable().optional(),
  text_similarity: z.number().min(0).max(1).nullable().optional(),
  semantic_similarity: z.number().min(0).max(1).nullable().optional(),
});

export const AIMatchItemSchema = z.object({
  job_id: z.string(),
  job_title: z.string().optional(),
  location: z.string().nullable().optional(),
  match_score: z.number().min(0).max(100).optional(),
  final_score: z.number().min(0).max(100).optional(),
  components: AIScoreComponentsSchema.optional(),
  skill_overlap_score: z.number().min(0).max(1).optional(),
  tfidf_similarity: z.number().min(0).max(1).optional(),
  semantic_similarity: z.number().min(0).max(1).optional(),
  matched_skills: z.array(z.string()).default([]),
  missing_skills: z.array(z.string()).default([]),
  explanation: z.union([z.array(z.string()), z.record(z.any())]).optional(),
});

export const AIMatchResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    matching_version: z.string(),
    formula: z.string().optional(),
    total_jobs_evaluated: z.number().optional(),
    matches: z.array(AIMatchItemSchema),
  }),
});

export const AIAnalyzeAndMatchResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    candidate_profile: AICandidateProfileSchema,
    matching_version: z.string(),
    formula: z.string().optional(),
    total_jobs_evaluated: z.number().optional(),
    top_matches: z.array(AIMatchItemSchema),
  }),
});
