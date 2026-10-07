import { Prisma } from '@prisma/client';
import { prisma } from '../config/prisma.js';

export interface PersistMatchInput {
  jobId: string;
  finalScore: number;
  skillOverlapScore: number;
  tfidfSimilarity: number;
  semanticSimilarity: number;
  matchingVersion?: string;
  matchedSkills: string[];
  missingSkills: string[];
  explanation?: Record<string, unknown>;
  jobTitle?: string;
  location?: string | null;
}

export class MatchRepository {
  async saveMatchesWithGaps(candidateProfileId: string, matches: PersistMatchInput[]) {
    return prisma.$transaction(async (tx: Prisma.TransactionClient) => {
      const savedMatches = [];

      for (const m of matches) {
        // Clamp scores to valid PostgreSQL CHECK constraint ranges
        const finalScore = Math.max(0.0, Math.min(100.0, m.finalScore));
        const skillOverlapScore = Math.max(0.0, Math.min(1.0, m.skillOverlapScore));
        const tfidfSimilarity = Math.max(0.0, Math.min(1.0, m.tfidfSimilarity));
        const semanticSimilarity = Math.max(0.0, Math.min(1.0, m.semanticSimilarity));

        // Ensure referenced job exists in database
        const existingJob = await tx.job.findUnique({
          where: { id: m.jobId },
          select: { id: true },
        });

        if (!existingJob) {
          const title = m.jobTitle || 'Analytics Role';
          await tx.job.create({
            data: {
              id: m.jobId,
              title,
              normalizedTitle: title.toLowerCase().trim(),
              location: m.location || 'Remote',
              description: `Job requisition for ${title} evaluated via matching engine.`,
              source: 'analytics_jobs',
            },
          });
        }

        // Delete any existing match between this profile and job
        const existing = await tx.match.findFirst({
          where: { candidateProfileId, jobId: m.jobId },
        });
        if (existing) {
          await tx.match.delete({ where: { id: existing.id } });
        }

        // Create match record
        const matchRecord = await tx.match.create({
          data: {
            candidateProfileId,
            jobId: m.jobId,
            finalScore,
            skillOverlapScore,
            tfidfSimilarity,
            semanticSimilarity,
            matchingVersion: m.matchingVersion || '1.0.0',
            explanation: (m.explanation || {
              matchedSkills: m.matchedSkills,
              missingSkills: m.missingSkills,
            }) as any,
          },
        });

        // Persist missing skills as SkillGaps
        for (const missingSkillName of m.missingSkills) {
          const normName = missingSkillName.toLowerCase().trim();
          if (!normName) continue;

          let skill = await tx.skill.findUnique({
            where: { normalizedName: normName },
          });

          if (!skill) {
            skill = await tx.skill.create({
              data: {
                name: missingSkillName,
                normalizedName: normName,
                category: 'Job Requirement',
              },
            });
          }

          await tx.skillGap.create({
            data: {
              matchId: matchRecord.id,
              skillId: skill.id,
              priority: 'HIGH',
              reason: 'Required qualification identified during job matching analysis',
            },
          });
        }

        savedMatches.push(matchRecord);
      }

      // Fetch persisted matches with relations
      return tx.match.findMany({
        where: {
          id: { in: savedMatches.map((sm) => sm.id) },
        },
        include: {
          job: true,
          skillGaps: {
            include: { skill: true },
          },
        },
        orderBy: { finalScore: 'desc' },
      });
    });
  }

  async getMatchesByProfileId(candidateProfileId: string, limit = 20) {
    return prisma.match.findMany({
      where: { candidateProfileId },
      include: {
        job: true,
        skillGaps: {
          include: { skill: true },
        },
      },
      orderBy: { finalScore: 'desc' },
      take: limit,
    });
  }

  async getMatchById(id: string) {
    return prisma.match.findUnique({
      where: { id },
      include: {
        job: true,
        skillGaps: {
          include: { skill: true },
        },
      },
    });
  }
}

export const matchRepository = new MatchRepository();
