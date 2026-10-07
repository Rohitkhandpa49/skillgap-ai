import request from 'supertest';
import path from 'path';
import fs from 'fs';
import { createApp } from '../src/app.js';
import { prisma } from '../src/config/prisma.js';

const app = createApp();

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

export async function runIntegrationTests() {
  console.log('====================================================');
  console.log('        SkillGap AI Backend Integration Tests       ');
  console.log('====================================================\n');

  const repoRoot = path.resolve(process.cwd(), '..');
  const samplePdfPath = path.resolve(repoRoot, 'ai-service', 'tests', 'fixtures', 'resumes', 'sample_resume.pdf');
  const multipagePdfPath = path.resolve(repoRoot, 'ai-service', 'tests', 'fixtures', 'resumes', 'multipage_resume.pdf');

  let uploadedResumeId: string;
  let sampleJobId: string;
  let generatedMatchId: string;

  // 1. Health Endpoint
  await runTest('GET /api/v1/health returns 200 healthy', async () => {
    const res = await request(app).get('/api/v1/health');
    assert(res.status === 200, `Expected 200, got ${res.status}`);
    assert(res.body.success === true, 'Expected success === true');
    assert(res.body.status === 'healthy', 'Expected status === healthy');
  });

  // 2. Readiness Endpoint
  await runTest('GET /api/v1/ready checks Prisma and FastAPI', async () => {
    const res = await request(app).get('/api/v1/ready');
    assert(res.status === 200, `Expected 200, got ${res.status}`);
    assert(res.body.status === 'ready', 'Expected overall status ready');
    assert(res.body.components.database === 'ready', 'Database should be ready');
    assert(res.body.components.ai_service === 'ready', 'AI service should be ready');
  });

  // 3. Job Listing Endpoint
  await runTest('GET /api/v1/jobs returns paginated jobs', async () => {
    const res = await request(app).get('/api/v1/jobs?page=1&limit=5');
    assert(res.status === 200, `Expected 200, got ${res.status}`);
    assert(res.body.success === true, 'Expected success === true');
    assert(Array.isArray(res.body.data.items), 'Expected items array');
    assert(res.body.data.items.length > 0, 'Expected seeded jobs in list');
    sampleJobId = res.body.data.items[0].id;
    assert(sampleJobId.length > 0, 'Valid sampleJobId extracted');
  });

  // 4. Job Details Endpoint
  await runTest('GET /api/v1/jobs/:jobId returns single job detail', async () => {
    const res = await request(app).get(`/api/v1/jobs/${sampleJobId}`);
    assert(res.status === 200, `Expected 200, got ${res.status}`);
    assert(res.body.data.id === sampleJobId, 'Expected matching jobId');
    assert(Array.isArray(res.body.data.requiredSkills), 'Expected requiredSkills array');
  });

  // 5. Job Not Found
  await runTest('GET /api/v1/jobs/:jobId with nonexistent ID returns 404', async () => {
    const res = await request(app).get('/api/v1/jobs/nonexistent_job_99999');
    assert(res.status === 404, `Expected 404, got ${res.status}`);
    assert(res.body.success === false, 'Expected success === false');
    assert(res.body.error.code === 'NOT_FOUND', 'Expected NOT_FOUND code');
  });

  // 6. Valid Resume Upload
  await runTest('POST /api/v1/resumes/upload uploads valid PDF', async () => {
    assert(fs.existsSync(samplePdfPath), `Sample PDF exists at ${samplePdfPath}`);
    const res = await request(app)
      .post('/api/v1/resumes/upload')
      .attach('file', samplePdfPath);

    assert(res.status === 201, `Expected 201, got ${res.status}: ${JSON.stringify(res.body)}`);
    assert(res.body.success === true, 'Upload should succeed');
    assert(res.body.data.resumeId, 'Expected returned resumeId');
    assert(res.body.data.status === 'UPLOADED', 'Expected UPLOADED status');
    uploadedResumeId = res.body.data.resumeId;
  });

  // 7. Invalid File Upload (Unsupported Extension)
  await runTest('POST /api/v1/resumes/upload rejects unsupported extension', async () => {
    const res = await request(app)
      .post('/api/v1/resumes/upload')
      .attach('file', Buffer.from('executable binary code'), 'malicious.exe');

    assert(res.status === 415, `Expected 415 Unsupported Media Type, got ${res.status}`);
    assert(res.body.success === false, 'Expected rejection');
    assert(res.body.error.code === 'UPLOAD_ERROR', 'Expected UPLOAD_ERROR code');
  });

  // 8. Missing File Upload
  await runTest('POST /api/v1/resumes/upload rejects empty request', async () => {
    const res = await request(app).post('/api/v1/resumes/upload');
    assert(res.status === 400, `Expected 400, got ${res.status}`);
    assert(res.body.success === false, 'Expected rejection');
  });

  // 9. Resume Analysis & Candidate Profile Persistence
  await runTest('POST /api/v1/resumes/:resumeId/analyze orchestrates AI and persists profile', async () => {
    const res = await request(app).post(`/api/v1/resumes/${uploadedResumeId}/analyze`);
    assert(res.status === 200, `Expected 200, got ${res.status}: ${JSON.stringify(res.body)}`);
    assert(res.body.success === true, 'Expected analysis success');
    assert(res.body.data.profile, 'Expected candidate profile');
    assert(res.body.data.profile.skills.length > 0, 'Expected extracted skills in profile');

    // Verify database record
    const dbProfile = await prisma.candidateProfile.findFirst({
      where: { resumeId: uploadedResumeId },
      include: { candidateSkills: { include: { skill: true } } },
    });
    assert(dbProfile !== null, 'Candidate profile must exist in database');
    assert(dbProfile!.candidateSkills.length > 0, 'Candidate skills must be persisted in database');
  });

  // 10. Idempotent Analysis
  await runTest('POST /api/v1/resumes/:resumeId/analyze is idempotent (no duplicate profiles)', async () => {
    const beforeCount = await prisma.candidateProfile.count({
      where: { resumeId: uploadedResumeId },
    });

    const res = await request(app).post(`/api/v1/resumes/${uploadedResumeId}/analyze`);
    assert(res.status === 200, `Expected 200 on re-analysis, got ${res.status}`);

    const afterCount = await prisma.candidateProfile.count({
      where: { resumeId: uploadedResumeId },
    });

    assert(beforeCount === afterCount, 'Profile count must remain identical after re-analysis');
  });

  // 11. Profile Retrieval
  await runTest('GET /api/v1/profile and /profile/skills retrieve persisted candidate data', async () => {
    const profileRes = await request(app).get('/api/v1/profile');
    assert(profileRes.status === 200, `Expected 200, got ${profileRes.status}`);
    assert(profileRes.body.data.skills.length > 0, 'Profile skills should be populated');

    const skillsRes = await request(app).get('/api/v1/profile/skills');
    assert(skillsRes.status === 200, `Expected 200, got ${skillsRes.status}`);
    assert(skillsRes.body.data.totalSkills > 0, 'Expected positive totalSkills count');
  });

  // 12. Candidate Matching
  await runTest('POST /api/v1/matches runs FastAPI hybrid matcher and persists matches', async () => {
    const res = await request(app)
      .post('/api/v1/matches')
      .send({ topK: 5 });

    assert(res.status === 200, `Expected 200, got ${res.status}: ${JSON.stringify(res.body)}`);
    assert(res.body.success === true, 'Matching should succeed');
    assert(Array.isArray(res.body.data.matches), 'Expected matches array');
    assert(res.body.data.matches.length > 0, 'Expected ranked matches');

    const topMatch = res.body.data.matches[0];
    generatedMatchId = topMatch.id;

    // Verify valid score constraints
    assert(topMatch.scores.finalScore >= 0 && topMatch.scores.finalScore <= 100, 'finalScore in [0, 100]');
    assert(topMatch.scores.semanticSimilarity >= 0 && topMatch.scores.semanticSimilarity <= 1, 'semantic in [0, 1]');
    assert(topMatch.scores.skillOverlapScore >= 0 && topMatch.scores.skillOverlapScore <= 1, 'overlap in [0, 1]');
    assert(topMatch.scores.tfidfSimilarity >= 0 && topMatch.scores.tfidfSimilarity <= 1, 'tfidf in [0, 1]');

    // Verify database record
    const dbMatch = await prisma.match.findUnique({
      where: { id: topMatch.id },
      include: { skillGaps: true },
    });
    assert(dbMatch !== null, 'Match record must be persisted in database');
  });

  // 13. Match Retrieval
  await runTest('GET /api/v1/matches and /matches/:matchId return persisted matches', async () => {
    const listRes = await request(app).get('/api/v1/matches?limit=10');
    assert(listRes.status === 200, `Expected 200, got ${listRes.status}`);
    assert(listRes.body.data.matches.length > 0, 'Expected persisted matches in list');

    const detailRes = await request(app).get(`/api/v1/matches/${generatedMatchId}`);
    assert(detailRes.status === 200, `Expected 200, got ${detailRes.status}`);
    assert(detailRes.body.data.id === generatedMatchId, 'Expected matching matchId');
  });

  // 14. One-Shot Analyze and Match
  await runTest('POST /api/v1/resumes/:resumeId/analyze-and-match executes full pipeline', async () => {
    // First upload another document
    const uploadRes = await request(app)
      .post('/api/v1/resumes/upload')
      .attach('file', multipagePdfPath);
    assert(uploadRes.status === 201, 'Multipage upload should succeed');
    const secondResumeId = uploadRes.body.data.resumeId;

    // Execute one-shot endpoint
    const res = await request(app).post(`/api/v1/resumes/${secondResumeId}/analyze-and-match?top_k=5`);
    assert(res.status === 200, `Expected 200, got ${res.status}: ${JSON.stringify(res.body)}`);
    assert(res.body.success === true, 'One-shot analysis should succeed');
    assert(res.body.data.profile.skills.length > 0, 'Expected profile skills');
    assert(res.body.data.matches.length > 0, 'Expected top matches');
  });

  // 15. Centralized 404 Route Handling
  await runTest('GET /api/v1/invalid-route returns standardized 404', async () => {
    const res = await request(app).get('/api/v1/invalid-route');
    assert(res.status === 404, `Expected 404, got ${res.status}`);
    assert(res.body.success === false, 'Expected success === false');
    assert(res.body.error.code === 'NOT_FOUND', 'Expected NOT_FOUND code');
    assert(res.body.requestId, 'Expected requestId in error response');
  });

  console.log('\n====================================================');
  console.log(`INTEGRATION TESTS: ${testsPassed} Passed, ${testsFailed} Failed`);
  console.log('====================================================');

  if (testsFailed > 0) {
    throw new Error(`${testsFailed} integration tests failed`);
  }
}

if (process.argv[1]?.includes('integration.test')) {
  runIntegrationTests()
    .then(() => prisma.$disconnect())
    .catch((err) => {
      console.error('Fatal error:', err);
      process.exit(1);
    });
}
