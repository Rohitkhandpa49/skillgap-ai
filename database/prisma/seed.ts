import { PrismaClient, UserRole, UserStatus, ResumeStatus } from '@prisma/client';
import fs from 'fs';
import path from 'path';

const prisma = new PrismaClient();

// Helper to categorize canonical skills based on known categories
function categorizeSkill(name: string): string {
  const n = name.toLowerCase();
  if (['python', 'c', 'c++', 'c#', 'java', 'javascript', 'typescript', 'r', 'php', 'ruby', 'scala', 'go'].includes(n)) {
    return 'Programming Languages';
  }
  if (['react', 'react.js', 'angular', 'vue', 'html', 'css', 'jquery', 'frontend'].includes(n)) {
    return 'Frontend Development';
  }
  if (['node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'spring boot', '.net', 'backend'].includes(n)) {
    return 'Backend Development';
  }
  if (['postgresql', 'mysql', 'mongodb', 'oracle', 'sql', 'nosql', 'redis', 'cassandra', 'hive'].includes(n)) {
    return 'Databases & Storage';
  }
  if (['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'ci/cd', 'linux', 'devops'].includes(n)) {
    return 'Cloud & DevOps';
  }
  if (['machine learning', 'deep learning', 'nlp', 'natural language processing', 'computer vision', 'data science', 'artificial intelligence'].includes(n)) {
    return 'AI & Machine Learning';
  }
  if (['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'data analysis', 'data engineering', 'etl', 'big data', 'hadoop', 'spark'].includes(n)) {
    return 'Data Engineering & Analytics';
  }
  return 'General Technical';
}

async function seedSkills(repoRoot: string): Promise<Map<string, string>> {
  const skillsFilePath = path.resolve(repoRoot, 'data', 'skills.json');
  console.log(`[Seed] Loading canonical skills from: ${skillsFilePath}`);

  if (!fs.existsSync(skillsFilePath)) {
    throw new Error(`skills.json not found at: ${skillsFilePath}`);
  }

  const rawSkills: string[] = JSON.parse(fs.readFileSync(skillsFilePath, 'utf-8'));
  console.log(`[Seed] Found ${rawSkills.length} canonical skills to process.`);

  const skillMap = new Map<string, string>(); // normalizedName -> id

  for (const skillName of rawSkills) {
    const trimmed = skillName.trim();
    if (!trimmed) continue;
    const normalizedName = trimmed.toLowerCase();
    const category = categorizeSkill(trimmed);

    const record = await prisma.skill.upsert({
      where: { normalizedName },
      update: {
        name: trimmed,
        category,
      },
      create: {
        name: trimmed,
        normalizedName,
        category,
      },
    });

    skillMap.set(normalizedName, record.id);
  }

  console.log(`[Seed] Successfully seeded ${skillMap.size} canonical skills.`);
  return skillMap;
}

async function seedJobs(repoRoot: string, skillMap: Map<string, string>, limit = 100) {
  const jobsFilePath = path.resolve(repoRoot, 'data', 'processed', 'analytics_jobs', 'job_profiles.json');
  console.log(`[Seed] Loading jobs from: ${jobsFilePath} (target limit: ${limit})`);

  if (!fs.existsSync(jobsFilePath)) {
    console.warn(`[Seed] Warning: job_profiles.json not found at ${jobsFilePath}. Skipping job seed.`);
    return { jobsCount: 0, relationsCount: 0 };
  }

  const allJobs: any[] = JSON.parse(fs.readFileSync(jobsFilePath, 'utf-8'));
  const jobsToSeed = allJobs.slice(0, limit);

  let seededJobsCount = 0;
  let seededJobSkillsCount = 0;

  for (const job of jobsToSeed) {
    const jobId: string = job.job_id;
    const title: string = job.job_title || 'Untitled Job';
    const normalizedTitle: string = job.job_title_normalized || title.toLowerCase().trim();
    const jobType: string | null = job.job_type || job.job_type_normalized || null;
    const location: string | null = job.location || null;
    const description: string | null = job.job_description || null;
    const salaryRaw: string | null = job.salary_raw || null;
    const minExp: number | null = job.experience?.min_years ?? null;
    const maxExp: number | null = job.experience?.max_years ?? null;

    const upsertedJob = await prisma.job.upsert({
      where: { id: jobId },
      update: {
        title,
        normalizedTitle,
        jobType,
        location,
        description,
        salaryRaw,
        minExperienceYears: minExp,
        maxExperienceYears: maxExp,
        source: 'analytics_jobs',
      },
      create: {
        id: jobId,
        title,
        normalizedTitle,
        jobType,
        location,
        description,
        salaryRaw,
        minExperienceYears: minExp,
        maxExperienceYears: maxExp,
        source: 'analytics_jobs',
      },
    });
    seededJobsCount++;

    // Resolve job skills against canonical taxonomy
    const skillsList: string[] = Array.isArray(job.skills) ? job.skills : [];
    for (const rawJobSkill of skillsList) {
      const normSkill = rawJobSkill.trim().toLowerCase();
      let skillId = skillMap.get(normSkill);

      // If not in map directly, check if existing skill row exists
      if (!skillId) {
        const found = await prisma.skill.findUnique({ where: { normalizedName: normSkill } });
        if (found) {
          skillId = found.id;
          skillMap.set(normSkill, skillId);
        }
      }

      if (skillId) {
        await prisma.jobSkill.upsert({
          where: {
            jobId_skillId: {
              jobId: upsertedJob.id,
              skillId: skillId,
            },
          },
          update: {
            isRequired: true,
            importance: 1.0,
          },
          create: {
            jobId: upsertedJob.id,
            skillId: skillId,
            isRequired: true,
            importance: 1.0,
          },
        });
        seededJobSkillsCount++;
      }
    }
  }

  console.log(`[Seed] Seeded ${seededJobsCount} jobs and ${seededJobSkillsCount} JobSkill relationships.`);
  return { jobsCount: seededJobsCount, relationsCount: seededJobSkillsCount };
}

async function seedDevelopmentCandidate(skillMap: Map<string, string>, firstJobId?: string) {
  console.log('[Seed] Seeding synthetic development candidate...');

  const devEmail = 'demo.candidate@example.com';
  // Secure development dummy password hash (never plaintext)
  const dummyPasswordHash = '$2b$10$epB/2R4Y7Pj1c8C4V8Mee.7pQe5w8L0r7dF1G3H4J5K6L7M8N9O0P';

  const user = await prisma.user.upsert({
    where: { email: devEmail },
    update: {
      displayName: 'Demo Candidate',
      role: UserRole.CANDIDATE,
      status: UserStatus.ACTIVE,
    },
    create: {
      email: devEmail,
      displayName: 'Demo Candidate',
      passwordHash: dummyPasswordHash,
      role: UserRole.CANDIDATE,
      status: UserStatus.ACTIVE,
    },
  });

  // Seed sample resume metadata
  let resume = await prisma.resume.findFirst({
    where: { userId: user.id, originalFilename: 'demo_resume.pdf' },
  });

  if (!resume) {
    resume = await prisma.resume.create({
      data: {
        userId: user.id,
        originalFilename: 'demo_resume.pdf',
        storedFilename: 'resumes/demo_candidate_001.pdf',
        mimeType: 'application/pdf',
        fileSize: 102400,
        status: ResumeStatus.PROCESSED,
      },
    });
  }

  // Seed candidate profile
  let profile = await prisma.candidateProfile.findFirst({
    where: { userId: user.id },
  });

  if (!profile) {
    profile = await prisma.candidateProfile.create({
      data: {
        userId: user.id,
        resumeId: resume.id,
        summary: 'Experienced Software Engineer specializing in Python, Machine Learning, and distributed PostgreSQL systems.',
        analysisVersion: 'v1.0.0',
      },
    });
  }

  // Link sample CandidateSkills
  const targetCandidateSkills = [
    { name: 'python', confidence: 0.95, evidence: '5 years building production Python services' },
    { name: 'machine learning', confidence: 0.88, evidence: 'Deployed transformer models and evaluation pipelines' },
    { name: 'postgresql', confidence: 0.90, evidence: 'Schema design, indexing, and migration management' },
    { name: 'docker', confidence: 0.85, evidence: 'Containerized multi-tier microservices' },
  ];

  for (const s of targetCandidateSkills) {
    const skillId = skillMap.get(s.name);
    if (skillId) {
      await prisma.candidateSkill.upsert({
        where: {
          candidateProfileId_skillId: {
            candidateProfileId: profile.id,
            skillId,
          },
        },
        update: {
          confidence: s.confidence,
          evidence: s.evidence,
          sourceSection: 'EXPERIENCE',
        },
        create: {
          candidateProfileId: profile.id,
          skillId,
          confidence: s.confidence,
          evidence: s.evidence,
          sourceSection: 'EXPERIENCE',
        },
      });
    }
  }

  // If a job was seeded, create a representative Match and SkillGap
  if (firstJobId) {
    let match = await prisma.match.findFirst({
      where: { candidateProfileId: profile.id, jobId: firstJobId },
    });

    if (!match) {
      match = await prisma.match.create({
        data: {
          candidateProfileId: profile.id,
          jobId: firstJobId,
          finalScore: 84.5,
          skillOverlapScore: 0.80,
          tfidfSimilarity: 0.82,
          semanticSimilarity: 0.89,
          matchingVersion: 'v1.0.0',
          explanation: {
            matchedSkills: ['python', 'postgresql', 'docker'],
            missingSkills: ['oracle', 'pl/sql'],
            scoringWeights: { overlap: 0.4, semantic: 0.4, tfidf: 0.2 },
          },
        },
      });

      // Add a SkillGap
      const oracleSkill = skillMap.get('oracle');
      if (oracleSkill) {
        await prisma.skillGap.create({
          data: {
            matchId: match.id,
            skillId: oracleSkill,
            priority: 'HIGH',
            reason: 'Target position requires deep enterprise Oracle database knowledge.',
          },
        });
      }
    }

    // Seed a sample CareerPath milestone
    const existingCareerPath = await prisma.careerPath.findFirst({
      where: { jobId: firstJobId, sequenceOrder: 1 },
    });

    if (!existingCareerPath) {
      const mlSkill = skillMap.get('machine learning');
      await prisma.careerPath.create({
        data: {
          jobId: firstJobId,
          targetRole: 'Senior AI/Data Platform Architect',
          title: 'Master Enterprise Database Architecture',
          description: 'Bridge high-performance PostgreSQL and enterprise storage engines.',
          sequenceOrder: 1,
          recommendedSkillId: mlSkill || null,
          projectSuggestion: 'Build a distributed pipeline integrating PostgreSQL with vector embeddings.',
        },
      });
    }
  }

  console.log('[Seed] Successfully seeded synthetic development candidate, profile, skills, match, gap, and career path.');
}

async function main() {
  console.log('=== Starting SkillGap AI Database Seed ===');
  const repoRoot = path.resolve(__dirname, '..', '..');

  const skillMap = await seedSkills(repoRoot);
  const { jobsCount, relationsCount } = await seedJobs(repoRoot, skillMap, 100);

  // Get first job id if available
  const sampleJob = await prisma.job.findFirst();
  await seedDevelopmentCandidate(skillMap, sampleJob?.id);

  console.log('=== Seed Completed Successfully ===');
  console.log(`Summary:`);
  console.log(`- Canonical Skills: ${skillMap.size}`);
  console.log(`- Jobs Seeded: ${jobsCount}`);
  console.log(`- JobSkill Relations: ${relationsCount}`);
  console.log(`- Dev Candidate: demo.candidate@example.com`);
}

main()
  .catch((e) => {
    console.error('[Seed] Error during seeding:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
