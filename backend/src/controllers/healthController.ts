import { Request, Response, NextFunction } from 'express';
import { healthService } from '../services/healthService.js';

export class HealthController {
  async getHealth(_req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const result = await healthService.getHealth();
      res.status(200).json(result);
    } catch (err) {
      next(err);
    }
  }

  async getReady(_req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const result = await healthService.getReadiness();
      const statusCode = result.status === 'ready' ? 200 : 503;
      res.status(statusCode).json(result);
    } catch (err) {
      next(err);
    }
  }
}

export const healthController = new HealthController();
