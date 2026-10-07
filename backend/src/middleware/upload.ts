import multer from 'multer';
import path from 'path';
import { env } from '../config/environment.js';
import { ensureUploadDirExists, generateSafeStorageFilename } from '../utils/fileStorage.js';
import { UploadError } from '../errors/AppError.js';

ensureUploadDirExists();

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => {
    ensureUploadDirExists();
    cb(null, env.UPLOAD_DIR);
  },
  filename: (_req, file, cb) => {
    try {
      const safeName = generateSafeStorageFilename(file.originalname);
      cb(null, safeName);
    } catch (err) {
      cb(err as Error, '');
    }
  },
});

const ALLOWED_MIME_TYPES = new Set([
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword',
  'application/octet-stream', // Some browsers send octet-stream for docx
]);

const ALLOWED_EXTENSIONS = new Set(['.pdf', '.docx']);

export const uploadMiddleware = multer({
  storage,
  limits: {
    fileSize: env.MAX_FILE_SIZE_MB * 1024 * 1024,
    files: 1,
  },
  fileFilter: (_req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    if (!ALLOWED_EXTENSIONS.has(ext)) {
      return cb(new UploadError(`Unsupported file extension: '${ext}'. Only PDF and DOCX files are allowed.`, 415));
    }

    if (file.mimetype && !ALLOWED_MIME_TYPES.has(file.mimetype)) {
      return cb(new UploadError(`Unsupported MIME type: '${file.mimetype}'. Only PDF and DOCX documents are supported.`, 415));
    }

    cb(null, true);
  },
});
