import { jobRepository } from '../repositories/jobRepository.js';
import { NotFoundError } from '../errors/AppError.js';
import { JobDetailDTO, JobSummaryDTO, PaginatedResponse } from '../types/index.js';

export class JobService {
  async getJobs(page = 1, limit = 20, search?: string): Promise<PaginatedResponse<JobSummaryDTO>> {
    const result = await jobRepository.getJobs(page, limit, search);

    const items: JobSummaryDTO[] = result.items.map((j: any) => ({
      id: j.id,
      title: j.title,
      normalizedTitle: j.normalizedTitle,
      jobType: j.jobType,
      location: j.location,
      minExperienceYears: j.minExperienceYears,
      maxExperienceYears: j.maxExperienceYears,
      salaryRaw: j.salaryRaw,
      skills: j.jobSkills.map((js: any) => js.skill.name),
    }));

    return {
      items,
      pagination: result.pagination,
    };
  }

  async getJobById(id: string): Promise<JobDetailDTO> {
    const job = await jobRepository.getJobById(id);
    if (!job) {
      throw new NotFoundError(`Job with ID '${id}' was not found`);
    }

    return {
      id: job.id,
      title: job.title,
      normalizedTitle: job.normalizedTitle,
      jobType: job.jobType,
      location: job.location,
      description: job.description,
      minExperienceYears: job.minExperienceYears,
      maxExperienceYears: job.maxExperienceYears,
      salaryRaw: job.salaryRaw,
      source: job.source,
      skills: job.jobSkills.map((js: any) => js.skill.name),
      requiredSkills: job.jobSkills.map((js: any) => ({
        name: js.skill.name,
        normalizedName: js.skill.normalizedName,
        importance: js.importance,
        isRequired: js.isRequired,
      })),
    };
  }
}

export const jobService = new JobService();
