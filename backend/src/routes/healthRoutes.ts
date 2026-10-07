import { Router } from 'express';
import { healthController } from '../controllers/healthController.js';

export const healthRoutes = Router();

healthRoutes.get('/health', healthController.getHealth.bind(healthController));
healthRoutes.get('/ready', healthController.getReady.bind(healthController));
