import axios, { AxiosInstance } from 'axios';
import fs from 'fs';
import path from 'path';
import FormData from 'form-data';
import { env } from '../config/environment.js';
import { AIServiceError, AITimeoutError } from '../errors/AppError.js';
import { logger } from '../utils/logger.js';
import {
  AIAnalyzeResponseSchema,
  AIMatchResponseSchema,
  AIAnalyzeAndMatchResponseSchema,
} from '../validators/aiResponseValidators.js';

export class AIServiceClient {
  private client: AxiosInstance;

  constructor(baseURL = env.AI_SERVICE_URL, timeout = env.AI_SERVICE_TIMEOUT_MS) {
    this.client = axios.create({
      baseURL,
      timeout,
    });
  }

  private handleError(error: unknown, context: string): never {
    if (axios.isAxiosError(error)) {
      if (error.code === 'ECONNABORTED' || error.message.toLowerCase().includes('timeout')) {
        logger.error(`[AI Client] Timeout during ${context}`, { timeout: env.AI_SERVICE_TIMEOUT_MS });
        throw new AITimeoutError(`AI service timed out during ${context}`);
      }

      if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
        logger.error(`[AI Client] Connection refused to ${env.AI_SERVICE_URL} during ${context}`);
        throw new AIServiceError('AI service is currently unavailable', 503);
      }

      const status = error.response?.status || 502;
      const detail = error.response?.data?.detail || error.response?.data?.message || error.message;
      logger.error(`[AI Client] Error during ${context}`, { status, detail });
      throw new AIServiceError(`AI service request failed: ${detail}`, status);
    }

    logger.error(`[AI Client] Unexpected error during ${context}`, { error });
    throw new AIServiceError(`Unexpected failure communicating with AI service: ${(error as Error).message}`);
  }

  async checkHealth(): Promise<{ status: string; service: string }> {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (err) {
      this.handleError(err, 'checkHealth');
    }
  }

  async checkReadiness(): Promise<{ status: string; components?: Record<string, string> }> {
    try {
      const response = await this.client.get('/ready');
      return response.data;
    } catch (err) {
      this.handleError(err, 'checkReadiness');
    }
  }

  async analyzeResume(filePath: string) {
    try {
      const form = new FormData();
      const filename = path.basename(filePath);
      form.append('file', fs.createReadStream(filePath), { filename });

      const response = await this.client.post('/api/v1/resume/analyze', form, {
        headers: form.getHeaders(),
      });

      const parsed = AIAnalyzeResponseSchema.safeParse(response.data);
      if (!parsed.success) {
        logger.error('[AI Client] Invalid candidate profile response shape from FastAPI', {
          issues: parsed.error.issues,
        });
        throw new AIServiceError('AI service returned malformed candidate profile response', 502);
      }

      return parsed.data.data.candidate_profile;
    } catch (err) {
      this.handleError(err, 'analyzeResume');
    }
  }

  async matchCandidate(skills: string[], summary = '', topK = 10) {
    try {
      const payload = {
        skills,
        summary,
        top_k: topK,
      };

      const response = await this.client.post('/api/v1/match', payload, {
        headers: { 'Content-Type': 'application/json' },
      });

      const parsed = AIMatchResponseSchema.safeParse(response.data);
      if (!parsed.success) {
        logger.error('[AI Client] Invalid match response shape from FastAPI', {
          issues: parsed.error.issues,
        });
        throw new AIServiceError('AI service returned malformed match response', 502);
      }

      return parsed.data.data;
    } catch (err) {
      this.handleError(err, 'matchCandidate');
    }
  }

  async analyzeAndMatch(filePath: string, topK = 10) {
    try {
      const form = new FormData();
      const filename = path.basename(filePath);
      form.append('file', fs.createReadStream(filePath), { filename });

      const response = await this.client.post(`/api/v1/resume/analyze-and-match?top_k=${topK}`, form, {
        headers: form.getHeaders(),
      });

      const parsed = AIAnalyzeAndMatchResponseSchema.safeParse(response.data);
      if (!parsed.success) {
        logger.error('[AI Client] Invalid analyze-and-match response shape from FastAPI', {
          issues: parsed.error.issues,
        });
        throw new AIServiceError('AI service returned malformed analyze-and-match response', 502);
      }

      return parsed.data.data;
    } catch (err) {
      this.handleError(err, 'analyzeAndMatch');
    }
  }
}

export const aiServiceClient = new AIServiceClient();
