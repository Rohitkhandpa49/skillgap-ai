import { Router } from 'express';
import { resumeController } from '../controllers/resumeController.js';
import { uploadMiddleware } from '../middleware/upload.js';
import { expensiveOperationsRateLimiter } from '../middleware/rateLimiter.js';

export const resumeRoutes = Router();

// Upload route
resumeRoutes.post(
  '/upload',
  expensiveOperationsRateLimiter,
  uploadMiddleware.single('file'),
  resumeController.upload.bind(resumeController)
);

// Route-parameter analyze endpoint: /api/v1/resumes/:resumeId/analyze
resumeRoutes.post(
  '/:resumeId/analyze',
  expensiveOperationsRateLimiter,
  resumeController.analyze.bind(resumeController)
);

// Body-payload analyze endpoint: /api/v1/resume/analyze with { resumeId }
resumeRoutes.post(
  '/analyze',
  expensiveOperationsRateLimiter,
  resumeController.analyze.bind(resumeController)
);

// One-shot analyze-and-match orchestration
resumeRoutes.post(
  '/:resumeId/analyze-and-match',
  expensiveOperationsRateLimiter,
  resumeController.analyzeAndMatch.bind(resumeController)
);
