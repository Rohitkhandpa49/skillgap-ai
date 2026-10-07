import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

interface ValidationResult {
  check: string;
  passed: boolean;
  details: string;
}

async function validateDatabase() {
  console.log('====================================================');
  console.log('       SkillGap AI Database Validation Suite        ');
  console.log('====================================================\n');

  const results: ValidationResult[] = [];

  // 1. Database Connection
  try {
    const rawResult: any[] = await prisma.$queryRaw`SELECT 1 as connected;`;
    results.push({
      check: 'Database Connectivity',
      passed: rawResult.length > 0 && rawResult[0].connected === 1,
      details: 'Successfully connected and queried PostgreSQL',
    });
  } catch (err: any) {
    results.push({
      check: 'Database Connectivity',
      passed: false,
      details: `Connection failed: ${err.message}`,
    });
  }

  // 2. Expected Tables Exist
  try {
    const tables: any[] = await prisma.$queryRaw`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    `;
    const tableNames = new Set(tables.map((t) => t.table_name));
    const requiredTables = [
      'users',
      'resumes',
      'candidate_profiles',
      'skills',
      'candidate_skills',
      'jobs',
      'job_skills',
      'matches',
      'skill_gaps',
      'career_paths',
    ];

    const missingTables = requiredTables.filter((t) => !tableNames.has(t));
    results.push({
      check: 'Expected Tables Exist',
      passed: missingTables.length === 0,
      details: missingTables.length === 0
        ? `All ${requiredTables.length} core tables present in public schema`
        : `Missing tables: ${missingTables.join(', ')}`,
    });
  } catch (err: any) {
    results.push({
      check: 'Expected Tables Exist',
      passed: false,
      details: err.message,
    });
  }

  // 3. Canonical Skills Present
  try {
    const skillCount = await prisma.skill.count();
    results.push({
      check: 'Canonical Skills Present',
      passed: skillCount >= 90,
      details: `Found ${skillCount} canonical skills in database (expected >= 90)`,
    });
  } catch (err: any) {
    results.push({
      check: 'Canonical Skills Present',
      passed: false,
      details: err.message,
    });
  }

  // 4. Jobs Present
  try {
    const jobCount = await prisma.job.count();
    results.push({
      check: 'Jobs Present',
      passed: jobCount >= 50,
      details: `Found ${jobCount} seeded jobs in database (expected >= 50)`,
    });
  } catch (err: any) {
    results.push({
      check: 'Jobs Present',
      passed: false,
      details: err.message,
    });
  }

  // 5. Job-Skill Relations Present
  try {
    const jobSkillCount = await prisma.jobSkill.count();
    results.push({
      check: 'Job-Skill Relations Present',
      passed: jobSkillCount >= 100,
      details: `Found ${jobSkillCount} JobSkill relationships in database`,
    });
  } catch (err: any) {
    results.push({
      check: 'Job-Skill Relations Present',
      passed: false,
      details: err.message,
    });
  }

  // 6. No Duplicate Normalized Skill Names
  try {
    const duplicates: any[] = await prisma.$queryRaw`
      SELECT "normalizedName", COUNT(*) as count 
      FROM skills 
      GROUP BY "normalizedName" 
      HAVING COUNT(*) > 1;
    `;
    results.push({
      check: 'Skill Uniqueness Constraint',
      passed: duplicates.length === 0,
      details: duplicates.length === 0
        ? 'No duplicate normalized skill names detected'
        : `Found duplicates: ${JSON.stringify(duplicates)}`,
    });
  } catch (err: any) {
    results.push({
      check: 'Skill Uniqueness Constraint',
      passed: false,
      details: err.message,
    });
  }

  // 7. Referential Integrity Check (No Broken Foreign Keys)
  try {
    const brokenCandidateSkills: any[] = await prisma.$queryRaw`
      SELECT cs.id FROM candidate_skills cs
      LEFT JOIN candidate_profiles cp ON cs."candidateProfileId" = cp.id
      LEFT JOIN skills s ON cs."skillId" = s.id
      WHERE cp.id IS NULL OR s.id IS NULL;
    `;

    const brokenJobSkills: any[] = await prisma.$queryRaw`
      SELECT js.id FROM job_skills js
      LEFT JOIN jobs j ON js."jobId" = j.id
      LEFT JOIN skills s ON js."skillId" = s.id
      WHERE j.id IS NULL OR s.id IS NULL;
    `;

    const brokenMatches: any[] = await prisma.$queryRaw`
      SELECT m.id FROM matches m
      LEFT JOIN candidate_profiles cp ON m."candidateProfileId" = cp.id
      LEFT JOIN jobs j ON m."jobId" = j.id
      WHERE cp.id IS NULL OR j.id IS NULL;
    `;

    const brokenGaps: any[] = await prisma.$queryRaw`
      SELECT sg.id FROM skill_gaps sg
      LEFT JOIN matches m ON sg."matchId" = m.id
      LEFT JOIN skills s ON sg."skillId" = s.id
      WHERE m.id IS NULL OR s.id IS NULL;
    `;

    const totalBroken =
      brokenCandidateSkills.length +
      brokenJobSkills.length +
      brokenMatches.length +
      brokenGaps.length;

    results.push({
      check: 'Referential Integrity (Foreign Keys)',
      passed: totalBroken === 0,
      details: totalBroken === 0
        ? 'Zero orphan or dangling foreign keys detected'
        : `Broken relations found: CS=${brokenCandidateSkills.length}, JS=${brokenJobSkills.length}, M=${brokenMatches.length}, G=${brokenGaps.length}`,
    });
  } catch (err: any) {
    results.push({
      check: 'Referential Integrity (Foreign Keys)',
      passed: false,
      details: err.message,
    });
  }

  // 8. Development Candidate Integrity
  try {
    const devUser = await prisma.user.findUnique({
      where: { email: 'demo.candidate@example.com' },
      include: {
        candidateProfiles: {
          include: {
            candidateSkills: { include: { skill: true } },
            matches: { include: { job: true, skillGaps: { include: { skill: true } } } },
          },
        },
        resumes: true,
      },
    });

    const validDev =
      devUser !== null &&
      devUser.candidateProfiles.length > 0 &&
      devUser.candidateProfiles[0].candidateSkills.length > 0 &&
      devUser.candidateProfiles[0].matches.length > 0;

    results.push({
      check: 'Development Candidate Journey',
      passed: validDev,
      details: validDev
        ? `User -> Resume -> Profile (${devUser?.candidateProfiles[0].candidateSkills.length} skills) -> Match (${devUser?.candidateProfiles[0].matches.length} matches) complete`
        : 'Development candidate journey incomplete',
    });
  } catch (err: any) {
    results.push({
      check: 'Development Candidate Journey',
      passed: false,
      details: err.message,
    });
  }

  // Output Report
  let allPassed = true;
  for (const r of results) {
    const status = r.passed ? 'PASS' : 'FAIL';
    if (!r.passed) allPassed = false;
    console.log(`[${status}] ${r.check}`);
    console.log(`       Details: ${r.details}\n`);
  }

  console.log('====================================================');
  console.log(`FINAL STATUS: ${allPassed ? 'ALL CHECKS PASSED (PASS)' : 'VALIDATION FAILED (FAIL)'}`);
  console.log('====================================================');

  return allPassed;
}

validateDatabase()
  .then((passed) => {
    process.exit(passed ? 0 : 1);
  })
  .catch((err) => {
    console.error('Fatal validation error:', err);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
