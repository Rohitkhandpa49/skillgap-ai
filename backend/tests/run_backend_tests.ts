import { runIntegrationTests } from './integration.test.js';
import { runFailureTests } from './failure.test.js';
import { prisma } from '../src/config/prisma.js';

async function runAll() {
  console.log('Starting SkillGap AI Backend Test Suite...\n');
  try {
    await runIntegrationTests();
    console.log('\n');
    await runFailureTests();
    console.log('\n====================================================');
    console.log('       ALL BACKEND TEST SUITES COMPLETED (PASS)     ');
    console.log('====================================================');
  } catch (err: any) {
    console.error('\n❌ Test Suite Failed:', err.message);
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

runAll();
