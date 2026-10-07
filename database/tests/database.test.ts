import { PrismaClient, UserRole, UserStatus, ResumeStatus } from '@prisma/client';

const prisma = new PrismaClient();

let testsPassed = 0;
let testsFailed = 0;

function assert(condition: boolean, message: string) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

async function runTest(name: string, fn: () => Promise<void>) {
  try {
    process.stdout.write(`TEST: ${name} ... `);
    await fn();
    console.log('PASS');
    testsPassed++;
  } catch (err: any) {
    console.log('FAIL');
    console.error(`  Error: ${err.message}\n`);
    testsFailed++;
  }
}

async function main() {
  console.log('====================================================');
  console.log('        SkillGap AI Database Test Suite             ');
  console.log('====================================================\n');

  // Test 1: Unique User Email
  await runTest('Unique User Email constraint enforcement', async () => {
    const testEmail = `test.unique.${Date.now()}@example.com`;
    await prisma.user.create({
      data: {
        email: testEmail,
        displayName: 'Test User 1',
        passwordHash: 'dummy_hash',
      },
    });

    let threwExpectedError = false;
    try {
      await prisma.user.create({
        data: {
          email: testEmail,
          displayName: 'Test User Duplicate',
          passwordHash: 'dummy_hash',
        },
      });
    } catch (err: any) {
      threwExpectedError = err.code === 'P2002' || err.message.includes('Unique constraint');
    }

    assert(threwExpectedError, 'Expected duplicate email creation to throw unique constraint violation');

    // Cleanup
    await prisma.user.delete({ where: { email: testEmail } });
  });

  // Test 2: Unique Normalized Skill
  await runTest('Unique Normalized Skill constraint enforcement', async () => {
    const testSkillName = `Test Skill ${Date.now()}`;
    const testNormalized = testSkillName.toLowerCase();

    const created = await prisma.skill.create({
      data: {
        name: testSkillName,
        normalizedName: testNormalized,
        category: 'Test Category',
      },
    });

    let threwExpectedError = false;
    try {
      await prisma.skill.create({
        data: {
          name: `${testSkillName} Variant`,
          normalizedName: testNormalized, // identical normalized name
          category: 'Test Category',
        },
      });
    } catch (err: any) {
      threwExpectedError = err.code === 'P2002' || err.message.includes('Unique constraint');
    }

    assert(threwExpectedError, 'Expected duplicate normalized skill name to throw unique constraint violation');

    // Cleanup
    await prisma.skill.delete({ where: { id: created.id } });
  });

  // Test 3: CandidateSkill Relationship and Uniqueness
  await runTest('CandidateSkill join table and composite uniqueness', async () => {
    const user = await prisma.user.create({
      data: {
        email: `candidate.skills.test.${Date.now()}@example.com`,
        displayName: 'Candidate Skill Tester',
        passwordHash: 'dummy_hash',
      },
    });

    const profile = await prisma.candidateProfile.create({
      data: {
        userId: user.id,
        summary: 'Profile for candidate skill testing',
      },
    });

    const skill = await prisma.skill.findFirstOrThrow();

    const candidateSkill = await prisma.candidateSkill.create({
      data: {
        candidateProfileId: profile.id,
        skillId: skill.id,
        confidence: 0.92,
        evidence: 'Demonstrated in production testing',
        sourceSection: 'PROJECTS',
      },
    });

    assert(candidateSkill.confidence === 0.92, 'Candidate skill confidence stored properly');

    let duplicateThrew = false;
    try {
      await prisma.candidateSkill.create({
        data: {
          candidateProfileId: profile.id,
          skillId: skill.id,
          confidence: 0.50,
        },
      });
    } catch (err: any) {
      duplicateThrew = err.code === 'P2002' || err.message.includes('Unique constraint');
    }

    assert(duplicateThrew, 'Duplicate (candidateProfileId, skillId) must throw unique constraint');

    // Cleanup
    await prisma.candidateProfile.delete({ where: { id: profile.id } });
    await prisma.user.delete({ where: { id: user.id } });
  });

  // Test 4: JobSkill Relationship and Uniqueness
  await runTest('JobSkill join table and composite uniqueness', async () => {
    const job = await prisma.job.create({
      data: {
        id: `test_job_${Date.now()}`,
        title: 'Senior Systems Engineer',
        normalizedTitle: 'senior systems engineer',
        description: 'Test job description',
      },
    });

    const skill = await prisma.skill.findFirstOrThrow();

    const jobSkill = await prisma.jobSkill.create({
      data: {
        jobId: job.id,
        skillId: skill.id,
        isRequired: true,
        importance: 1.0,
      },
    });

    assert(jobSkill.isRequired === true, 'Job skill isRequired flag properly persisted');

    let duplicateThrew = false;
    try {
      await prisma.jobSkill.create({
        data: {
          jobId: job.id,
          skillId: skill.id,
          isRequired: false,
        },
      });
    } catch (err: any) {
      duplicateThrew = err.code === 'P2002' || err.message.includes('Unique constraint');
    }

    assert(duplicateThrew, 'Duplicate (jobId, skillId) must throw unique constraint');

    // Cleanup
    await prisma.job.delete({ where: { id: job.id } });
  });

  // Test 5: Candidate Ownership Isolation
  await runTest('Candidate Ownership Isolation between different users', async () => {
    const userA = await prisma.user.create({
      data: {
        email: `candidate.a.${Date.now()}@example.com`,
        displayName: 'Candidate A',
        passwordHash: 'dummy_hash_a',
      },
    });

    const userB = await prisma.user.create({
      data: {
        email: `candidate.b.${Date.now()}@example.com`,
        displayName: 'Candidate B',
        passwordHash: 'dummy_hash_b',
      },
    });

    const profileA = await prisma.candidateProfile.create({
      data: {
        userId: userA.id,
        summary: 'Candidate A private resume summary',
      },
    });

    // Querying profiles by User B must NEVER return Profile A
    const profilesForB = await prisma.candidateProfile.findMany({
      where: { userId: userB.id },
    });

    assert(profilesForB.length === 0, 'User B must not see Candidate A profiles');
    assert(
      !profilesForB.some((p) => p.id === profileA.id),
      'User B cannot access Profile A under userId scope'
    );

    // Cleanup
    await prisma.candidateProfile.delete({ where: { id: profileA.id } });
    await prisma.user.delete({ where: { id: userA.id } });
    await prisma.user.delete({ where: { id: userB.id } });
  });

  // Test 6: Match Score Storage and Database Constraints
  await runTest('Match Score storage and range validation constraints', async () => {
    const user = await prisma.user.create({
      data: {
        email: `match.tester.${Date.now()}@example.com`,
        displayName: 'Match Tester',
        passwordHash: 'dummy_hash',
      },
    });

    const profile = await prisma.candidateProfile.create({
      data: {
        userId: user.id,
        summary: 'Profile for match testing',
      },
    });

    const job = await prisma.job.findFirstOrThrow();

    // Valid score storage
    const match = await prisma.match.create({
      data: {
        candidateProfileId: profile.id,
        jobId: job.id,
        finalScore: 88.5,
        skillOverlapScore: 0.85,
        tfidfSimilarity: 0.80,
        semanticSimilarity: 0.90,
        matchingVersion: 'v1.0.0',
        explanation: {
          matchedSkills: ['python', 'postgresql'],
          missingSkills: ['aws'],
        },
      },
    });

    assert(match.finalScore === 88.5, 'Valid finalScore stored');
    assert(match.skillOverlapScore === 0.85, 'Valid skillOverlapScore stored');

    // Invalid score should be rejected by PostgreSQL CHECK constraint
    let invalidScoreRejected = false;
    try {
      await prisma.$executeRawUnsafe(`
        INSERT INTO matches (id, "candidateProfileId", "jobId", "finalScore", "skillOverlapScore", "tfidfSimilarity", "semanticSimilarity", "matchingVersion", "createdAt", "updatedAt")
        VALUES ('invalid-match-uuid', '${profile.id}', '${job.id}', 150.0, 0.5, 0.5, 0.5, 'v1.0.0', NOW(), NOW());
      `);
    } catch {
      invalidScoreRejected = true;
    }

    assert(invalidScoreRejected, 'finalScore > 100 must be rejected by check constraint');

    // Cleanup
    await prisma.match.delete({ where: { id: match.id } });
    await prisma.candidateProfile.delete({ where: { id: profile.id } });
    await prisma.user.delete({ where: { id: user.id } });
  });

  // Test 7: SkillGap Relationship to Match
  await runTest('SkillGap relationship linked to Match and canonical Skill', async () => {
    const user = await prisma.user.create({
      data: {
        email: `gap.tester.${Date.now()}@example.com`,
        displayName: 'Gap Tester',
        passwordHash: 'dummy_hash',
      },
    });

    const profile = await prisma.candidateProfile.create({
      data: {
        userId: user.id,
      },
    });

    const job = await prisma.job.findFirstOrThrow();
    const skill = await prisma.skill.findFirstOrThrow();

    const match = await prisma.match.create({
      data: {
        candidateProfileId: profile.id,
        jobId: job.id,
        finalScore: 75.0,
        skillOverlapScore: 0.70,
        tfidfSimilarity: 0.72,
        semanticSimilarity: 0.78,
        matchingVersion: 'v1.0.0',
      },
    });

    const gap = await prisma.skillGap.create({
      data: {
        matchId: match.id,
        skillId: skill.id,
        priority: 'CRITICAL',
        reason: 'Required core competency for role',
      },
    });

    const fetchedMatch = await prisma.match.findUniqueOrThrow({
      where: { id: match.id },
      include: {
        skillGaps: { include: { skill: true } },
      },
    });

    assert(fetchedMatch.skillGaps.length === 1, 'SkillGap successfully retrieved through Match');
    assert(fetchedMatch.skillGaps[0].priority === 'CRITICAL', 'SkillGap priority preserved');
    assert(fetchedMatch.skillGaps[0].skill.id === skill.id, 'SkillGap links to canonical Skill');

    // Cleanup
    await prisma.candidateProfile.delete({ where: { id: profile.id } });
    await prisma.user.delete({ where: { id: user.id } });
  });

  // Test 8: Conservative Deletion / Deletion Policies
  await runTest('Conservative Deletion Policies protect vital parent records', async () => {
    const user = await prisma.user.create({
      data: {
        email: `delete.guard.${Date.now()}@example.com`,
        displayName: 'Delete Guard Tester',
        passwordHash: 'dummy_hash',
      },
    });

    const resume = await prisma.resume.create({
      data: {
        userId: user.id,
        originalFilename: 'test_doc.pdf',
        storedFilename: 'resumes/test_doc.pdf',
        mimeType: 'application/pdf',
        fileSize: 50000,
        status: ResumeStatus.UPLOADED,
      },
    });

    // Attempting to delete user while resume exists must be RESTRICTED
    let userDeletionRestricted = false;
    try {
      await prisma.user.delete({ where: { id: user.id } });
    } catch (err: any) {
      userDeletionRestricted = err.code === 'P2003' || err.message.includes('Foreign key constraint');
    }

    assert(userDeletionRestricted, 'Parent User deletion must be RESTRICTED when Resumes exist');

    // Cleanup in proper order
    await prisma.resume.delete({ where: { id: resume.id } });
    await prisma.user.delete({ where: { id: user.id } });
  });

  // Test 9: Cascade Deletion on Child Match/Gaps
  await runTest('Cascade Deletion cleans child SkillGaps when Match is removed', async () => {
    const user = await prisma.user.create({
      data: {
        email: `cascade.tester.${Date.now()}@example.com`,
        displayName: 'Cascade Tester',
        passwordHash: 'dummy_hash',
      },
    });

    const profile = await prisma.candidateProfile.create({
      data: { userId: user.id },
    });

    const job = await prisma.job.findFirstOrThrow();
    const skill = await prisma.skill.findFirstOrThrow();

    const match = await prisma.match.create({
      data: {
        candidateProfileId: profile.id,
        jobId: job.id,
        finalScore: 80.0,
        skillOverlapScore: 0.8,
        tfidfSimilarity: 0.8,
        semanticSimilarity: 0.8,
        matchingVersion: 'v1.0.0',
      },
    });

    const gap = await prisma.skillGap.create({
      data: {
        matchId: match.id,
        skillId: skill.id,
        priority: 'MEDIUM',
      },
    });

    // Delete Match
    await prisma.match.delete({ where: { id: match.id } });

    // Verify SkillGap was automatically cascaded
    const orphanGap = await prisma.skillGap.findUnique({
      where: { id: gap.id },
    });

    assert(orphanGap === null, 'SkillGap must be cascaded when parent Match is deleted');

    // Cleanup
    await prisma.candidateProfile.delete({ where: { id: profile.id } });
    await prisma.user.delete({ where: { id: user.id } });
  });

  console.log('\n====================================================');
  console.log(`TEST RUN COMPLETE: ${testsPassed} Passed, ${testsFailed} Failed`);
  console.log('====================================================');

  if (testsFailed > 0) {
    process.exit(1);
  }
}

main()
  .catch((err) => {
    console.error('Fatal test error:', err);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
