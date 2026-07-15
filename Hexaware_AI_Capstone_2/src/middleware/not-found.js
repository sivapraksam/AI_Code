import { sendError } from '../utils/response.js';

export function notFoundHandler(req, res) {
  sendError(res, 404, 'NOT_FOUND', 'Route not found');
}
