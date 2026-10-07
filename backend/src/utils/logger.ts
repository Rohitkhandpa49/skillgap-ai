const SENSITIVE_KEYS = new Set([
  'password',
  'passwordhash',
  'token',
  'authorization',
  'secret',
  'apikey',
  'rawtext',
]);

function sanitize(obj: unknown): unknown {
  if (obj === null || obj === undefined) return obj;
  if (typeof obj !== 'object') return obj;

  if (Array.isArray(obj)) {
    return obj.map(sanitize);
  }

  const sanitized: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
    if (SENSITIVE_KEYS.has(key.toLowerCase())) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof value === 'object') {
      sanitized[key] = sanitize(value);
    } else {
      sanitized[key] = value;
    }
  }
  return sanitized;
}

export const logger = {
  info(message: string, meta?: Record<string, unknown>) {
    const sanitizedMeta = meta ? sanitize(meta) : '';
    console.log(`[INFO] ${new Date().toISOString()} - ${message}`, sanitizedMeta ? JSON.stringify(sanitizedMeta) : '');
  },

  warn(message: string, meta?: Record<string, unknown>) {
    const sanitizedMeta = meta ? sanitize(meta) : '';
    console.warn(`[WARN] ${new Date().toISOString()} - ${message}`, sanitizedMeta ? JSON.stringify(sanitizedMeta) : '');
  },

  error(message: string, meta?: Record<string, unknown>) {
    const sanitizedMeta = meta ? sanitize(meta) : '';
    console.error(`[ERROR] ${new Date().toISOString()} - ${message}`, sanitizedMeta ? JSON.stringify(sanitizedMeta) : '');
  },

  debug(message: string, meta?: Record<string, unknown>) {
    if (process.env.LOG_LEVEL === 'debug') {
      const sanitizedMeta = meta ? sanitize(meta) : '';
      console.log(`[DEBUG] ${new Date().toISOString()} - ${message}`, sanitizedMeta ? JSON.stringify(sanitizedMeta) : '');
    }
  },
};
