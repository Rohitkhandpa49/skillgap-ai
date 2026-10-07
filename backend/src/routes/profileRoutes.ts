import { Router } from 'express';
import { profileController } from '../controllers/profileController.js';

export const profileRoutes = Router();

profileRoutes.get('/', profileController.getProfile.bind(profileController));
profileRoutes.get('/skills', profileController.getProfileSkills.bind(profileController));
