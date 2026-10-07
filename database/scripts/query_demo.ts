import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function demonstrateQueries() {
  console.log('=== Step 39 Query Demonstration ===\n');

  // 1. Query sample skills
  console.log('1. Sample Canonical Skills:');
  const sampleSkills = await prisma.skill.findMany({
    take: 5,
    orderBy: { name: 'asc' },
  });
  for (const s of sampleSkills) {
    console.log(`   - [${s.category || 'General'}] ${s.name} (normalized: "${s.normalizedName}")`);
  }

  // 2. Query sample jobs + skills
  console.log('\n2. Sample Jobs with Required Skills:');
  const sampleJobs = await prisma.job.findMany({
    take: 3,
    include: {
      jobSkills: {
        include: { skill: true },
      },
    },
  });

  for (const j of sampleJobs) {
    console.log(`   - Job ID: ${j.id}`);
    console.log(`     Title: ${j.title}`);
    console.log(`     Location: ${j.location || 'N/A'}`);
    const skillsList = j.jobSkills.map((js) => js.skill.name).join(', ');
    console.log(`     Skills (${j.jobSkills.length}): ${skillsList || 'None specified'}\n`);
  }

  // 3. Query candidate journey
  console.log('3. Candidate End-to-End Profile & Match Snapshot:');
  const candidate = await prisma.user.findUnique({
    where: { email: 'demo.candidate@example.com' },
    include: {
      candidateProfiles: {
        include: {
          candidateSkills: { include: { skill: true } },
          matches: {
            include: {
              job: true,
              skillGaps: { include: { skill: true } },
            },
          },
        },
      },
    },
  });

  if (candidate && candidate.candidateProfiles.length > 0) {
    const prof = candidate.candidateProfiles[0];
    console.log(`   Candidate: ${candidate.displayName} (${candidate.email})`);
    console.log(`   Summary: ${prof.summary}`);
    console.log(
      `   Profile Skills: ${prof.candidateSkills.map((cs) => `${cs.skill.name} (${(cs.confidence * 100).toFixed(0)}%)`).join(', ')}`
    );
    if (prof.matches.length > 0) {
      const match = prof.matches[0];
      console.log(`   Matched Job: ${match.job.title}`);
      console.log(`   Score: ${match.finalScore}/100 (Semantic: ${match.semanticSimilarity}, TF-IDF: ${match.tfidfSimilarity})`);
      console.log(`   Identified Gaps: ${match.skillGaps.map((sg) => `${sg.skill.name} [${sg.priority}]`).join(', ')}`);
    }
  }

  console.log('\nQuery demonstration completed successfully.');
}

demonstrateQueries()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
