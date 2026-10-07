import { createApp } from './app.js';
import { env } from './config/environment.js';
import { disconnectPrisma } from './config/prisma.js';
import { logger } from './utils/logger.js';
import { Server } from 'http';

const app = createApp();
let server: Server;

export function startServer(): Server {
  server = app.listen(env.PORT, () => {
    logger.info(`🚀 SkillGap Backend API running on port ${env.PORT}`, {
      env: env.NODE_ENV,
      aiServiceUrl: env.AI_SERVICE_URL,
      corsOrigin: env.FRONTEND_URL,
    });
  });

  const shutdown = async (signal: string) => {
    logger.info(`Received ${signal}. Gracefully shutting down SkillGap Backend...`);

    if (server) {
      server.close(async () => {
        logger.info('HTTP server closed.');
        try {
          await disconnectPrisma();
          logger.info('Database connections closed cleanly.');
          process.exit(0);
        } catch (err) {
          logger.error('Error during database disconnect:', { error: (err as Error).message });
          process.exit(1);
        }
      });
    } else {
      process.exit(0);
    }
  };

  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));

  return server;
}

if (process.argv[1]?.includes('server')) {
  startServer();
}
