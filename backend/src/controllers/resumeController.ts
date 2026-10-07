import { Request, Response, NextFunction } from 'express';
import { resumeService } from '../services/resumeService.js';
import { candidateProfileService } from '../services/candidateProfileService.js';
import { orchestrationService } from '../services/orchestrationService.js';
import { ApiResponse } from '../types/index.js';
import { ResumeIdParamSchema } from '../validators/requestValidators.js';

export class ResumeController {
  async upload(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const userId = req.devUser?.userId || 'dev_user_001';
      const result = await resumeService.handleUpload(userId, req.file);

      const response: ApiResponse<typeof result> = {
        success: true,
        data: result,
        message: 'Resume uploaded successfully',
      };
      res.status(201).json(response);
    } catch (err) {
      next(err);
    }
  }

  async analyze(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const userId = req.devUser?.userId || 'dev_user_001';
      // Support both route param :resumeId and request body { resumeId }
      const rawResumeId = req.params.resumeId || req.body.resumeId;
      const { resumeId } = ResumeIdParamSchema.parse({ resumeId: rawResumeId });

      const profile = await candidateProfileService.analyzeResume(resumeId, userId);

      const response: ApiResponse<{ resumeId: string; profile: typeof profile }> = {
        success: true,
        data: {
          resumeId,
          profile,
        },
        message: 'Resume analyzed and candidate profile persisted successfully',
      };
      res.status(200).json(response);
    } catch (err) {
      next(err);
    }
  }

  async analyzeAndMatch(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const userId = req.devUser?.userId || 'dev_user_001';
      const rawResumeId = req.params.resumeId || req.body.resumeId;
      const { resumeId } = ResumeIdParamSchema.parse({ resumeId: rawResumeId });

      const topK = req.query.top_k ? parseInt(req.query.top_k as string, 10) : 10;
      const result = await orchestrationService.analyzeAndMatchResume(resumeId, userId, topK);

      const response: ApiResponse<typeof result> = {
        success: true,
        data: result,
        message: 'Resume analyzed and ranked job matches persisted successfully',
      };
      res.status(200).json(response);
    } catch (err) {
      next(err);
    }
  }
}

export const resumeController = new ResumeController();
