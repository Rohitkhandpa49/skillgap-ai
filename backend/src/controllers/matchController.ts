import { Request, Response, NextFunction } from 'express';
import { matchingService } from '../services/matchingService.js';
import { ApiResponse, MatchDTO } from '../types/index.js';
import { MatchIdParamSchema, MatchRequestSchema } from '../validators/requestValidators.js';

export class MatchController {
  async match(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const userId = req.devUser?.userId || 'dev_user_001';
      const body = MatchRequestSchema.parse(req.body);

      const matches = await matchingService.matchCandidate(userId, body.topK, body.candidateProfileId);

      const response: ApiResponse<{ matches: MatchDTO[]; totalMatches: number }> = {
        success: true,
        data: {
          matches,
          totalMatches: matches.length,
        },
        message: 'Candidate matched successfully against jobs using hybrid matcher',
      };
      res.status(200).json(response);
    } catch (err) {
      next(err);
    }
  }

  async getMatches(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const userId = req.devUser?.userId || 'dev_user_001';
      const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : 20;

      const matches = await matchingService.getMatchesForUser(userId, limit);

      const response: ApiResponse<{ matches: MatchDTO[]; totalMatches: number }> = {
        success: true,
        data: {
          matches,
          totalMatches: matches.length,
        },
      };
      res.status(200).json(response);
    } catch (err) {
      next(err);
    }
  }

  async getMatchById(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { matchId } = MatchIdParamSchema.parse(req.params);
      const match = await matchingService.getMatchById(matchId);

      const response: ApiResponse<MatchDTO> = {
        success: true,
        data: match,
      };
      res.status(200).json(response);
    } catch (err) {
      next(err);
    }
  }
}

export const matchController = new MatchController();
