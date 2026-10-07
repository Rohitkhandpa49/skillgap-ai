import { resumeRepository } from '../repositories/resumeRepository.js';
import { NotFoundError, UploadError } from '../errors/AppError.js';
import { getStorageFilePath } from '../utils/fileStorage.js';
import fs from 'fs';

export class ResumeService {
  async handleUpload(userId: string, file?: Express.Multer.File) {
    if (!file) {
      throw new UploadError('No file was uploaded. Expected multipart form field: file');
    }

    const resume = await resumeRepository.createResume({
      userId,
      originalFilename: file.originalname,
      storedFilename: file.filename,
      mimeType: file.mimetype,
      fileSize: file.size,
    });

    return {
      resumeId: resume.id,
      filename: resume.originalFilename,
      status: resume.status,
      fileSize: resume.fileSize,
      mimeType: resume.mimeType,
    };
  }

  async getResumeOrThrow(resumeId: string) {
    const resume = await resumeRepository.getResumeById(resumeId);
    if (!resume) {
      throw new NotFoundError(`Resume with ID '${resumeId}' was not found`);
    }

    const filePath = getStorageFilePath(resume.storedFilename);
    if (!fs.existsSync(filePath)) {
      throw new NotFoundError(`Stored resume file '${resume.storedFilename}' was not found on disk`);
    }

    return { resume, filePath };
  }
}

export const resumeService = new ResumeService();
