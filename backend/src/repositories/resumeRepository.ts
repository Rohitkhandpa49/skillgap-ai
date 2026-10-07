import { ResumeStatus } from '@prisma/client';
import { prisma } from '../config/prisma.js';

export class ResumeRepository {
  async createResume(data: {
    userId: string;
    originalFilename: string;
    storedFilename: string;
    mimeType: string;
    fileSize: number;
    status?: ResumeStatus;
  }) {
    return prisma.resume.create({
      data: {
        userId: data.userId,
        originalFilename: data.originalFilename,
        storedFilename: data.storedFilename,
        mimeType: data.mimeType,
        fileSize: data.fileSize,
        status: data.status || ResumeStatus.UPLOADED,
      },
    });
  }

  async getResumeById(id: string) {
    return prisma.resume.findUnique({
      where: { id },
    });
  }

  async updateResumeStatus(id: string, status: ResumeStatus) {
    return prisma.resume.update({
      where: { id },
      data: { status },
    });
  }
}

export const resumeRepository = new ResumeRepository();
