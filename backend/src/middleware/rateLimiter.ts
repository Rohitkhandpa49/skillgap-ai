import rateLimit from 'express-rate-limit';
import { ApiErrorResponse } from '../types/index.js';

export const globalRateLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100, // 100 requests per minute
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    const response: ApiErrorResponse = {
      success: false,
      error: {
        code: 'RATE_LIMIT_EXCEEDED',
        message: 'Too many requests. Please slow down and try again later.',
      },
      requestId: req.id,
    };
    res.status(429).json(response);
  },
});

export const expensiveOperationsRateLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 30, // 30 requests per minute for expensive AI / upload operations
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    const response: ApiErrorResponse = {
      success: false,
      error: {
        code: 'RATE_LIMIT_EXCEEDED',
        message: 'Rate limit exceeded for document analysis / matching operations.',
      },
      requestId: req.id,
    };
    res.status(429).json(response);
  },
});
