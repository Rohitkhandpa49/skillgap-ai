import { Request, Response, NextFunction } from 'express';
import { ZodError } from 'zod';
import multer from 'multer';
import { AppError } from '../errors/AppError.js';
import { ApiErrorResponse } from '../types/index.js';
import { logger } from '../utils/logger.js';

export function errorHandlerMiddleware(
  err: unknown,
  req: Request,
  res: Response,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  next: NextFunction
): void {
  const requestId = req.id;

  // 1. Domain AppError
  if (err instanceof AppError) {
    logger.warn(`AppError [${err.code}]: ${err.message}`, {
      code: err.code,
      statusCode: err.statusCode,
      requestId,
      details: err.details,
    });

    const response: ApiErrorResponse = {
      success: false,
      error: {
        code: err.code,
        message: err.message,
        details: err.details,
      },
      requestId,
    };
    res.status(err.statusCode).json(response);
    return;
  }

  // 2. Zod Validation Errors
  if (err instanceof ZodError) {
    const formattedDetails = err.errors.map((e) => ({
      field: e.path.join('.'),
      message: e.message,
    }));

    logger.warn(`ValidationError: ${err.message}`, {
      requestId,
      details: formattedDetails,
    });

    const response: ApiErrorResponse = {
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid request data',
        details: formattedDetails,
      },
      requestId,
    };
    res.status(400).json(response);
    return;
  }

  // 3. Multer Upload Errors
  if (err instanceof multer.MulterError) {
    let message = err.message;
    let statusCode = 400;

    if (err.code === 'LIMIT_FILE_SIZE') {
      message = 'File size exceeds maximum permitted limit';
      statusCode = 413;
    }

    logger.warn(`MulterError [${err.code}]: ${message}`, { requestId });

    const response: ApiErrorResponse = {
      success: false,
      error: {
        code: 'UPLOAD_ERROR',
        message,
        details: { multerCode: err.code },
      },
      requestId,
    };
    res.status(statusCode).json(response);
    return;
  }

  // 4. Unhandled/Unknown Errors
  const internalError = err as Error;
  logger.error(`Unhandled Server Error: ${internalError.message}`, {
    stack: internalError.stack,
    requestId,
  });

  const response: ApiErrorResponse = {
    success: false,
    error: {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'An unexpected internal error occurred. Please try again later.',
    },
    requestId,
  };
  res.status(500).json(response);
}

export function notFoundHandler(req: Request, res: Response): void {
  const response: ApiErrorResponse = {
    success: false,
    error: {
      code: 'NOT_FOUND',
      message: `Cannot ${req.method} ${req.originalUrl}`,
    },
    requestId: req.id,
  };
  res.status(404).json(response);
}
