import fs from 'fs';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';
import { env } from '../config/environment.js';
import { UploadError } from '../errors/AppError.js';

export function ensureUploadDirExists(): void {
  if (!fs.existsSync(env.UPLOAD_DIR)) {
    fs.mkdirSync(env.UPLOAD_DIR, { recursive: true });
  }
}

export function generateSafeStorageFilename(originalFilename: string): string {
  const ext = path.extname(originalFilename).toLowerCase();
  const validExtensions = ['.pdf', '.docx'];
  if (!validExtensions.includes(ext)) {
    throw new UploadError(`Unsupported file extension: ${ext}. Only .pdf and .docx are permitted.`);
  }
  return `${uuidv4()}${ext}`;
}

export function getStorageFilePath(storedFilename: string): string {
  // Prevent directory traversal
  const sanitized = path.basename(storedFilename);
  return path.resolve(env.UPLOAD_DIR, sanitized);
}

export function removeStorageFile(storedFilename: string): void {
  try {
    const filePath = getStorageFilePath(storedFilename);
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
  } catch {
    // Ignore cleanup errors
  }
}
