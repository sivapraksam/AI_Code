export function sendSuccess(res, statusCode, data) {
  res.status(statusCode).json({
    success: true,
    data,
    error: null
  });
}

export function sendError(res, statusCode, code, message, details = null) {
  res.status(statusCode).json({
    success: false,
    data: null,
    error: {
      code,
      message,
      details
    }
  });
}
