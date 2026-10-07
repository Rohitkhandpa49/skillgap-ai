import { Request, Response, NextFunction } from 'express';
import { candidateProfileService } from '../services/candidateProfileService.js';
import { ApiResponse, CandidateProfileDTO, CandidateSkillDTO } from '../types/index.js';

export class ProfileController {
  async getProfile(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const userId = req.devUser?.userId || 'dev_user_001';
      const profile = await candidateProfileService.getProfileForUser(userId);

      const response: ApiResponse<CandidateProfileDTO> = {
        success: true,
        data: profile,
      };
      res.status(200).json(response);
    } catch (err) {
      next(err);
    }
  }

  async getProfileSkills(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const userId = req.devUser?.userId || 'dev_user_001';
      const profile = await candidateProfileService.getProfileForUser(userId);

      const response: ApiResponse<{ skills: CandidateSkillDTO[]; totalSkills: number }> = {
        success: true,
        data: {
          skills: profile.skills,
          totalSkills: profile.skills.length,
        },
      };
      res.status(200).json(response);
    } catch (err) {
      next(err);
    }
  }
}

export const profileController = new ProfileController();
