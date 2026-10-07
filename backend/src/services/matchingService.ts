import { candidateProfileRepository } from '../repositories/candidateProfileRepository.js';
import { matchRepository, PersistMatchInput } from '../repositories/matchRepository.js';
import { aiServiceClient } from '../clients/aiServiceClient.js';
import { MatchDTO } from '../types/index.js';
import { NotFoundError, ValidationError } from '../errors/AppError.js';

export class MatchingService {
  async matchCandidate(userId: string, topK = 10, candidateProfileId?: string): Promise<MatchDTO[]> {
    // 1. Retrieve Candidate Profile from PostgreSQL
    let profile = candidateProfileId
      ? await candidateProfileRepository.getProfileById(candidateProfileId)
      : await candidateProfileRepository.getProfileByUserId(userId);

    if (!profile) {
      throw new NotFoundError(
        'Candidate profile not found. Please upload and analyze a resume before requesting matching.'
      );
    }

    const skills = profile.candidateSkills.map((cs: any) => cs.skill.name);
    const summary = profile.summary || '';

    if (skills.length === 0 && !summary.trim()) {
      throw new ValidationError(
        'Candidate profile has no extracted skills or professional summary to perform matching.'
      );
    }

    // 2. Call FastAPI Hybrid Matcher
    const aiMatchResult = await aiServiceClient.matchCandidate(skills, summary, topK);

    // 3. Prepare match records for persistence
    const matchesToPersist: PersistMatchInput[] = aiMatchResult.matches.map((m) => {
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
        matchingVersion: aiMatchResult.matching_version || '1.0.0',
        matchedSkills: m.matched_skills || [],
        missingSkills: m.missing_skills || [],
        explanation: {
          formula: aiMatchResult.formula,
          matchedSkills: m.matched_skills,
          missingSkills: m.missing_skills,
        },
      };
    });

    // 4. Transactionally persist matches and identified gaps in PostgreSQL
    const persistedMatches = await matchRepository.saveMatchesWithGaps(profile.id, matchesToPersist);

    // 5. Format to MatchDTOs
    return persistedMatches.map((pm: any) => ({
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
  }

  async getMatchesForUser(userId: string, limit = 20): Promise<MatchDTO[]> {
    const profile = await candidateProfileRepository.getProfileByUserId(userId);
    if (!profile) {
      return [];
    }

    const matches = await matchRepository.getMatchesByProfileId(profile.id, limit);

    return matches.map((pm: any) => ({
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
  }

  async getMatchById(matchId: string): Promise<MatchDTO> {
    const pm: any = await matchRepository.getMatchById(matchId);
    if (!pm) {
      throw new NotFoundError(`Match with ID '${matchId}' was not found`);
    }

    return {
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
    };
  }
}

export const matchingService = new MatchingService();
