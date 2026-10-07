import dotenv from 'dotenv';
import path from 'path';
import { z } from 'zod';

// Load .env relative to current working directory or backend root
dotenv.config();

const EnvironmentSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.coerce.number().default(5000),
  DATABASE_URL: z.string().min(1, 'DATABASE_URL is required'),
  AI_SERVICE_URL: z.string().url().default('http://localhost:8000'),
  AI_SERVICE_TIMEOUT_MS: z.coerce.number().default(30000),
  FRONTEND_URL: z.string().default('http://localhost:5173'),
  UPLOAD_DIR: z.string().default('../uploads'),
  MAX_FILE_SIZE_MB: z.coerce.number().default(10),
  LOG_LEVEL: z.string().default('info'),
});

export type Environment = z.infer<typeof EnvironmentSchema>;

function loadConfig(): Environment {
  const result = EnvironmentSchema.safeParse(process.env);
  if (!result.success) {
    console.error('❌ Invalid backend environment configuration:', result.error.format());
    throw new Error('Mandatory environment configuration validation failed');
  }

  // Resolve upload directory to absolute path
  const config = result.data;
  const resolvedUploadDir = path.isAbsolute(config.UPLOAD_DIR)
    ? config.UPLOAD_DIR
    : path.resolve(process.cwd(), config.UPLOAD_DIR);

  return {
    ...config,
    UPLOAD_DIR: resolvedUploadDir,
  };
}

export const env = loadConfig();
