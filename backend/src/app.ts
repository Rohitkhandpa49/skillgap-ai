import express, { Express } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { env } from './config/environment.js';
import { requestIdMiddleware } from './middleware/requestId.js';
import { requestLoggerMiddleware } from './middleware/requestLogger.js';
import { errorHandlerMiddleware, notFoundHandler } from './middleware/errorHandler.js';
import { globalRateLimiter } from './middleware/rateLimiter.js';
import { devContextMiddleware } from './middleware/devContext.js';

import { healthRoutes } from './routes/healthRoutes.js';
import { resumeRoutes } from './routes/resumeRoutes.js';
import { profileRoutes } from './routes/profileRoutes.js';
import { jobRoutes } from './routes/jobRoutes.js';
import { matchRoutes } from './routes/matchRoutes.js';

export function createApp(): Express {
  const app = express();

  // 1. Security Headers
  app.use(helmet());

  // 2. CORS configuration
  app.use(
    cors({
      origin: env.FRONTEND_URL,
      credentials: true,
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-Id'],
    })
  );

  // 3. Body Parsing
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true, limit: '10mb' }));

  // 4. Request Tracing & Logging
  app.use(requestIdMiddleware);
  app.use(requestLoggerMiddleware);

  // 5. Global Rate Limiter
  app.use(globalRateLimiter);

  // 6. Development Context (demo candidate ownership)
  app.use(devContextMiddleware);

  // 7. Route Registrations (/api/v1)
  app.use('/api/v1', healthRoutes);
  app.use('/api/v1/resumes', resumeRoutes);
  app.use('/api/v1/resume', resumeRoutes); // Singular alias for API contract compatibility
  app.use('/api/v1/profile', profileRoutes);
  app.use('/api/v1/jobs', jobRoutes);
  app.use('/api/v1/matches', matchRoutes);
  app.use('/api/v1/match', matchRoutes); // Singular alias for API contract compatibility

  // 8. 404 & Centralized Error Handling
  app.use(notFoundHandler);
  app.use(errorHandlerMiddleware);

  return app;
}

export const app = createApp();
