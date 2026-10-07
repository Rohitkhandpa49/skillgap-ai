import { Router } from 'express';
import { matchController } from '../controllers/matchController.js';
import { expensiveOperationsRateLimiter } from '../middleware/rateLimiter.js';

export const matchRoutes = Router();

matchRoutes.post('/', expensiveOperationsRateLimiter, matchController.match.bind(matchController));
matchRoutes.get('/', matchController.getMatches.bind(matchController));
matchRoutes.get('/:matchId', matchController.getMatchById.bind(matchController));
