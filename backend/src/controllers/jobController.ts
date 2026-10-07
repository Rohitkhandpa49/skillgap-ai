import { Request, Response, NextFunction } from 'express';
import { jobService } from '../services/jobService.js';
import { ApiResponse, JobDetailDTO, JobSummaryDTO, PaginatedResponse } from '../types/index.js';
import { JobIdParamSchema, PaginationQuerySchema } from '../validators/requestValidators.js';

export class JobController {
  async getJobs(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const query = PaginationQuerySchema.parse(req.query);
      const result = await jobService.getJobs(query.page, query.limit, query.search);

      const response: ApiResponse<PaginatedResponse<JobSummaryDTO>> = {
        success: true,
        data: result,
      };
      res.status(200).json(response);
    } catch (err) {
      next(err);
    }
  }

  async getJobById(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { jobId } = JobIdParamSchema.parse(req.params);
      const job = await jobService.getJobById(jobId);

      const response: ApiResponse<JobDetailDTO> = {
        success: true,
        data: job,
      };
      res.status(200).json(response);
    } catch (err) {
      next(err);
    }
  }
}

export const jobController = new JobController();
