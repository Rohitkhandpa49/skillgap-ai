import { prisma } from '../config/prisma.js';
import { aiServiceClient } from '../clients/aiServiceClient.js';

export class HealthService {
  async getHealth() {
    return {
      success: true as const,
      service: 'skillgap-backend',
      status: 'healthy',
      timestamp: new Date().toISOString(),
    };
  }

  async getReadiness() {
    let databaseStatus = 'ready';
    let aiServiceStatus = 'ready';
    let isOverallReady = true;

    // 1. Check PostgreSQL via Prisma
    try {
      await prisma.$queryRaw`SELECT 1;`;
    } catch {
      databaseStatus = 'unavailable';
      isOverallReady = false;
    }

    // 2. Check FastAPI AI Service
    try {
      const aiReady = await aiServiceClient.checkReadiness();
      if (aiReady.status !== 'ready') {
        aiServiceStatus = 'not_ready';
        isOverallReady = false;
      }
    } catch {
      aiServiceStatus = 'unavailable';
      isOverallReady = false;
    }

    return {
      success: true as const,
      status: isOverallReady ? 'ready' : 'degraded',
      components: {
        database: databaseStatus,
        ai_service: aiServiceStatus,
      },
      timestamp: new Date().toISOString(),
    };
  }
}

export const healthService = new HealthService();
