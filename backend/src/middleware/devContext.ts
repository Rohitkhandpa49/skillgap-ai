import { Request, Response, NextFunction } from 'express';
import { prisma } from '../config/prisma.js';
import { DevUserContext } from '../types/index.js';
import { logger } from '../utils/logger.js';

declare global {
  namespace Express {
    interface Request {
      devUser?: DevUserContext;
    }
  }
}

let cachedDevUser: DevUserContext | null = null;

export async function devContextMiddleware(req: Request, _res: Response, next: NextFunction): Promise<void> {
  try {
    if (cachedDevUser) {
      req.devUser = cachedDevUser;
      return next();
    }

    const email = 'demo.candidate@example.com';
    let user = await prisma.user.findUnique({ where: { email } });

    if (!user) {
      logger.info('[DevContext] Creating development demo candidate for local testing');
      user = await prisma.user.create({
        data: {
          email,
          displayName: 'Demo Candidate',
          passwordHash: '$2b$10$epB/2R4Y7Pj1c8C4V8Mee.7pQe5w8L0r7dF1G3H4J5K6L7M8N9O0P',
        },
      });
    }

    cachedDevUser = {
      userId: user.id,
      email: user.email,
      displayName: user.displayName,
    };

    req.devUser = cachedDevUser;
    next();
  } catch (err) {
    logger.error('[DevContext] Error resolving development user context:', { error: (err as Error).message });
    next(err);
  }
}
