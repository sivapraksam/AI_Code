import request from 'supertest';
import { describe, expect, it } from 'vitest';
import app from '../src/app.js';

describe('GET /health', () => {
  it('returns service health envelope', async () => {
    const response = await request(app).get('/health');

    expect(response.statusCode).toBe(200);
    expect(response.body).toEqual({
      success: true,
      data: { status: 'ok' },
      error: null
    });
  });
});
