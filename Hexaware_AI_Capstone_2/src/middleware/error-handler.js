import { HttpError } from '../utils/http-error.js';
import { sendError } from '../utils/response.js';

export function errorHandler(err, req, res, next) {
  if (res.headersSent) {
    next(err);
    return;
  }

  if (err instanceof HttpError) {
    sendError(res, err.statusCode, err.code, err.message, err.details);
    return;
  }

  sendError(res, 500, 'INTERNAL_SERVER_ERROR', 'An unexpected error occurred');
}
