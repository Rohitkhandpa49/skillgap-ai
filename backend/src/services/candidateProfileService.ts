import { ResumeStatus } from '@prisma/client';
import { resumeService } from './resumeService.js';
import { resumeRepository } from '../repositories/resumeRepository.js';
import { candidateProfileRepository } from '../repositories/candidateProfileRepository.js';
import { aiServiceClient } from '../clients/aiServiceClient.js';
import { CandidateProfileDTO } from '../types/index.js';
import { NotFoundError } from '../errors/AppError.js';

export class CandidateProfileService {
  async analyzeResume(resumeId: string, userId: string): Promise<CandidateProfileDTO> {
    // 1. Load resume and verify file exists on disk
    const { resume, filePath } = await resumeService.getResumeOrThrow(resumeId);

    // 2. Mark resume as PROCESSING
    await resumeRepository.updateResumeStatus(resume.id, ResumeStatus.PROCESSING);

    try {
      // 3. Call FastAPI resume analysis endpoint
      const aiProfile = await aiServiceClient.analyzeResume(filePath);

      // 4. Transform AI skills to CandidateSkillDTOs
      const skillsToPersist = aiProfile.skills.map((s) => {
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

      // 5. Transactionally upsert profile and skills in PostgreSQL
      const persistedProfile = await candidateProfileRepository.upsertProfileWithSkills({
        userId,
        resumeId: resume.id,
        summary: aiProfile.summary || null,
        analysisVersion: '1.0.0',
        skills: skillsToPersist,
      });

      // 6. Mark resume as PROCESSED
      await resumeRepository.updateResumeStatus(resume.id, ResumeStatus.PROCESSED);

      return {
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
    } catch (err) {
      // Mark resume as FAILED on error
      await resumeRepository.updateResumeStatus(resume.id, ResumeStatus.FAILED);
      throw err;
    }
  }

  async getProfileForUser(userId: string): Promise<CandidateProfileDTO> {
    const profile = await candidateProfileRepository.getProfileByUserId(userId);
    if (!profile) {
      throw new NotFoundError('No candidate profile found. Please upload and analyze a resume first.');
    }

    return {
      id: profile.id,
      userId: profile.userId,
      resumeId: profile.resumeId,
      summary: profile.summary,
      analysisVersion: profile.analysisVersion,
      createdAt: profile.createdAt,
      updatedAt: profile.updatedAt,
      skills: profile.candidateSkills.map((cs: any) => ({
        id: cs.id,
        name: cs.skill.name,
        normalizedName: cs.skill.normalizedName,
        confidence: cs.confidence,
        evidence: cs.evidence,
        sourceSection: cs.sourceSection,
      })),
    };
  }
}

export const candidateProfileService = new CandidateProfileService();
