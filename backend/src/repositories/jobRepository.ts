import { prisma } from '../config/prisma.js';

export class JobRepository {
  async getJobs(page = 1, limit = 20, search?: string) {
    const skip = (page - 1) * limit;

    const where: any = {};
    if (search && search.trim()) {
      const term = search.trim();
      where.OR = [
        { title: { contains: term, mode: 'insensitive' } },
        { normalizedTitle: { contains: term.toLowerCase(), mode: 'insensitive' } },
      ];
    }

    const [total, items] = await Promise.all([
      prisma.job.count({ where }),
      prisma.job.findMany({
        where,
        skip,
        take: limit,
        include: {
          jobSkills: {
            include: { skill: true },
          },
        },
        orderBy: { title: 'asc' },
      }),
    ]);

    return {
      items,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit) || 1,
      },
    };
  }

  async getJobById(id: string) {
    return prisma.job.findUnique({
      where: { id },
      include: {
        jobSkills: {
          include: { skill: true },
        },
      },
    });
  }
}

export const jobRepository = new JobRepository();
