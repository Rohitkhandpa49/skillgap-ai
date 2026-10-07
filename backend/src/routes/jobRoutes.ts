import { Router } from 'express';
import { jobController } from '../controllers/jobController.js';

export const jobRoutes = Router();

jobRoutes.get('/', jobController.getJobs.bind(jobController));
jobRoutes.get('/:jobId', jobController.getJobById.bind(jobController));
