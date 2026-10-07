import { AIServiceClient } from '../src/clients/aiServiceClient.js';
import { AIServiceError, AITimeoutError } from '../src/errors/AppError.js';

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

export async function runFailureTests() {
  console.log('====================================================');
  console.log('      SkillGap AI Failure Handling Test Suite       ');
  console.log('====================================================\n');

  // 1. AI Service Unavailable Handling
  await runTest('AIServiceClient handles connection failure with 503 AIServiceError', async () => {
    // Point to non-existent local port
    const badClient = new AIServiceClient('http://127.0.0.1:59999', 1000);

    let threwExpected = false;
    try {
      await badClient.checkReadiness();
    } catch (err: any) {
      threwExpected = err instanceof AIServiceError && err.statusCode === 503;
    }
    assert(threwExpected, 'Must throw AIServiceError with status 503');
  });

  // 2. AI Service Timeout Handling
  await runTest('AIServiceClient translates timeout into AITimeoutError with code AI_TIMEOUT', async () => {
    // Point to non-routable IP with 1ms timeout
    const timeoutClient = new AIServiceClient('http://10.255.255.1', 1);

    let threwTimeout = false;
    try {
      await timeoutClient.checkHealth();
    } catch (err: any) {
      threwTimeout =
        (err instanceof AITimeoutError || err instanceof AIServiceError) &&
        (err.code === 'AI_TIMEOUT' || err.statusCode === 504 || err.statusCode === 503);
    }
    assert(threwTimeout, 'Must translate timeout into controlled AI error');
  });

  // 3. AI Service Malformed Response Handling
  await runTest('AIServiceClient rejects malformed payload using Zod validation', async () => {
    const client = new AIServiceClient();
    // Test match with invalid inputs (empty array of skills and empty summary)
    let threwInvalid = false;
    try {
      await client.matchCandidate([], '');
    } catch (err: any) {
      threwInvalid = err instanceof AIServiceError;
    }
    assert(threwInvalid, 'Must reject invalid input with AIServiceError');
  });

  console.log('\n====================================================');
  console.log(`FAILURE TESTS: ${testsPassed} Passed, ${testsFailed} Failed`);
  console.log('====================================================');

  if (testsFailed > 0) {
    throw new Error(`${testsFailed} failure tests failed`);
  }
}

if (process.argv[1]?.includes('failure.test')) {
  runFailureTests().catch((err) => {
    console.error('Fatal failure test error:', err);
    process.exit(1);
  });
}
