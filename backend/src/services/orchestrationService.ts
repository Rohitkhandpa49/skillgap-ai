import { ResumeStatus } from '@prisma/client';
import { resumeService } from './resumeService.js';
import { resumeRepository } from '../repositories/resumeRepository.js';
import { candidateProfileRepository } from '../repositories/candidateProfileRepository.js';
import { matchRepository, PersistMatchInput } from '../repositories/matchRepository.js';
import { aiServiceClient } from '../clients/aiServiceClient.js';
import { CandidateProfileDTO, MatchDTO } from '../types/index.js';

export interface OrchestrationResultDTO {
  profile: CandidateProfileDTO;
  matches: MatchDTO[];
  totalMatches: number;
}

export class OrchestrationService {
  async analyzeAndMatchResume(
    resumeId: string,
    userId: string,
    topK = 10
  ): Promise<OrchestrationResultDTO> {
    // 1. Load resume and verify file path
    const { resume, filePath } = await resumeService.getResumeOrThrow(resumeId);

    // 2. Mark resume status as PROCESSING
    await resumeRepository.updateResumeStatus(resume.id, ResumeStatus.PROCESSING);

    try {
      // 3. Call FastAPI one-shot analyze-and-match endpoint
      const aiResult = await aiServiceClient.analyzeAndMatch(filePath, topK);

      // 4. Persist Candidate Profile & Skills
      const skillsToPersist = aiResult.candidate_profile.skills.map((s) => {
        let evidenceText: string | null = null;
        if (Array.isArray(s.evidence)) {
          evidenceText = s.evidence.join('; ');
        } else if (typeof s.evidence === 'string') {
          evidenceText = s.evidence;
        }

        const sourceSection =
          s.source_section ||
          (s.source_sections && s.source_sections.length > 0 ? s.source_sections.join(', ') : null);

        return {
          name: s.canonical_name || s.name,
          normalizedName: s.normalized_name || s.name.toLowerCase().trim(),
          confidence: s.confidence,
          evidence: evidenceText,
          sourceSection,
        };
      });

      const persistedProfile = await candidateProfileRepository.upsertProfileWithSkills({
        userId,
        resumeId: resume.id,
        summary: aiResult.candidate_profile.summary || null,
        analysisVersion: '1.0.0',
        skills: skillsToPersist,
      });

      // 5. Persist Matches and Skill Gaps
      const matchesToPersist: PersistMatchInput[] = aiResult.top_matches.map((m) => {
        const finalScore = m.match_score ?? m.final_score ?? 0;
        const skillOverlap = m.components?.skill_overlap ?? m.skill_overlap_score ?? 0;
        const tfidf =
          m.components?.tfidf_similarity ??
          m.components?.text_similarity ??
          m.tfidf_similarity ??
          0;
        const semantic = m.components?.semantic_similarity ?? m.semantic_similarity ?? 0;

        return {
          jobId: m.job_id,
          jobTitle: m.job_title,
          location: m.location,
          finalScore,
          skillOverlapScore: skillOverlap,
          tfidfSimilarity: tfidf,
          semanticSimilarity: semantic,
          matchingVersion: aiResult.matching_version || '1.0.0',
          matchedSkills: m.matched_skills || [],
          missingSkills: m.missing_skills || [],
          explanation: {
            formula: aiResult.formula,
            matchedSkills: m.matched_skills,
            missingSkills: m.missing_skills,
          },
        };
      });

      const persistedMatches = await matchRepository.saveMatchesWithGaps(
        persistedProfile.id,
        matchesToPersist
      );

      // 6. Mark resume status as PROCESSED
      await resumeRepository.updateResumeStatus(resume.id, ResumeStatus.PROCESSED);

      const profileDTO: CandidateProfileDTO = {
        id: persistedProfile.id,
        userId: persistedProfile.userId,
        resumeId: persistedProfile.resumeId,
        summary: persistedProfile.summary,
        analysisVersion: persistedProfile.analysisVersion,
        createdAt: persistedProfile.createdAt,
        updatedAt: persistedProfile.updatedAt,
        skills: persistedProfile.candidateSkills.map((cs: any) => ({
          id: cs.id,
          name: cs.skill.name,
          normalizedName: cs.skill.normalizedName,
          confidence: cs.confidence,
          evidence: cs.evidence,
          sourceSection: cs.sourceSection,
        })),
      };

      const matchesDTO: MatchDTO[] = persistedMatches.map((pm: any) => ({
        id: pm.id,
        candidateProfileId: pm.candidateProfileId,
        jobId: pm.jobId,
        jobTitle: pm.job.title,
        jobLocation: pm.job.location,
        scores: {
          finalScore: pm.finalScore,
          skillOverlapScore: pm.skillOverlapScore,
          tfidfSimilarity: pm.tfidfSimilarity,
          semanticSimilarity: pm.semanticSimilarity,
        },
        matchingVersion: pm.matchingVersion,
        matchedSkills: ((pm.explanation as any)?.matchedSkills as string[]) || [],
        missingSkills: pm.skillGaps.map((sg: any) => sg.skill.name),
        explanation: pm.explanation as Record<string, unknown>,
        createdAt: pm.createdAt,
      }));

      return {
        profile: profileDTO,
        matches: matchesDTO,
        totalMatches: matchesDTO.length,
      };
    } catch (err) {
      await resumeRepository.updateResumeStatus(resume.id, ResumeStatus.FAILED);
      throw err;
    }
  }
}

export const orchestrationService = new OrchestrationService();
