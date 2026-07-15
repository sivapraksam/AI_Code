const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';

export async function signup(payload) {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  const body = await response.json();

  if (!response.ok || body.success !== true) {
    const code = body?.error?.code || 'SIGNUP_FAILED';
    const message = body?.error?.message || 'Unable to complete signup.';
    const details = body?.error?.details || null;

    const error = new Error(message);
    error.code = code;
    error.details = details;
    throw error;
  }

  return body.data;
}
