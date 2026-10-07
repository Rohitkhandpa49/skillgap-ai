import { Prisma } from '@prisma/client';
import { prisma } from '../config/prisma.js';
import { CandidateSkillDTO } from '../types/index.js';

export class CandidateProfileRepository {
  async getProfileByUserId(userId: string) {
    return prisma.candidateProfile.findFirst({
      where: { userId },
      include: {
        candidateSkills: {
          include: { skill: true },
        },
      },
      orderBy: { updatedAt: 'desc' },
    });
  }

  async getProfileById(profileId: string) {
    return prisma.candidateProfile.findUnique({
      where: { id: profileId },
      include: {
        candidateSkills: {
          include: { skill: true },
        },
      },
    });
  }

  async upsertProfileWithSkills(data: {
    userId: string;
    resumeId?: string;
    summary?: string | null;
    analysisVersion?: string;
    skills: CandidateSkillDTO[];
  }) {
    return prisma.$transaction(async (tx: Prisma.TransactionClient) => {
      // 1. Check for existing candidate profile for this user
      let profile = await tx.candidateProfile.findFirst({
        where: { userId: data.userId },
      });

      if (profile) {
        // Update profile
        profile = await tx.candidateProfile.update({
          where: { id: profile.id },
          data: {
            resumeId: data.resumeId || profile.resumeId,
            summary: data.summary,
            analysisVersion: data.analysisVersion || '1.0.0',
          },
        });

        // Delete existing candidate skills to avoid stale/duplicate skills
        await tx.candidateSkill.deleteMany({
          where: { candidateProfileId: profile.id },
        });
      } else {
        // Create new profile
        profile = await tx.candidateProfile.create({
          data: {
            userId: data.userId,
            resumeId: data.resumeId,
            summary: data.summary,
            analysisVersion: data.analysisVersion || '1.0.0',
          },
        });
      }

      // 2. Resolve canonical skills and create CandidateSkill join records
      for (const skillItem of data.skills) {
        const normName = skillItem.normalizedName.toLowerCase().trim();
        if (!normName) continue;

        // Find or create canonical skill
        let skill = await tx.skill.findUnique({
          where: { normalizedName: normName },
        });

        if (!skill) {
          skill = await tx.skill.create({
            data: {
              name: skillItem.name,
              normalizedName: normName,
              category: 'General Technical',
            },
          });
        }

        // Clamp confidence to valid [0.0, 1.0] range
        const confidence = Math.max(0.0, Math.min(1.0, skillItem.confidence));

        await tx.candidateSkill.create({
          data: {
            candidateProfileId: profile.id,
            skillId: skill.id,
            confidence,
            evidence: skillItem.evidence || null,
            sourceSection: skillItem.sourceSection || null,
          },
        });
      }

      // 3. Return full profile with skills
      return tx.candidateProfile.findUniqueOrThrow({
        where: { id: profile.id },
        include: {
          candidateSkills: {
            include: { skill: true },
          },
        },
      });
    });
  }
}

export const candidateProfileRepository = new CandidateProfileRepository();
