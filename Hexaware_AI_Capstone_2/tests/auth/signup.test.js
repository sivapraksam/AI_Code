import request from 'supertest';
import { beforeEach, describe, expect, it } from 'vitest';
import app from '../../src/app.js';
import { resetUsersStore } from '../../src/features/auth/auth.service.js';

function buildValidPayload() {
  return {
    userId: 'User123',
    password: 'Welcome@123',
    confirmPassword: 'Welcome@123',
    securityQuestion: 'What is your favorite author?',
    securityAnswer: 'Tagore',
    name: 'John Doe',
    gender: 'Male',
    dateOfBirth: '1991-04-20',
    occupation: 'Hotel Owner',
    email: 'john@example.com',
    mobile: '9876543210',
    nationality: 'INDIA'
  };
}

describe('POST /api/v1/auth/signup', () => {
  beforeEach(() => {
    resetUsersStore();
  });

  it('creates a user when payload is valid', async () => {
    const response = await request(app)
      .post('/api/v1/auth/signup')
      .send(buildValidPayload());

    expect(response.statusCode).toBe(201);
    expect(response.body.success).toBe(true);
    expect(response.body.error).toBeNull();
    expect(response.body.data.user.userId).toBe('User123');
    expect(response.body.data.user.email).toBe('john@example.com');
  });

  it('returns validation error when payload is invalid', async () => {
    const invalidPayload = {
      ...buildValidPayload(),
      password: 'weak',
      confirmPassword: 'notMatch'
    };

    const response = await request(app)
      .post('/api/v1/auth/signup')
      .send(invalidPayload);

    expect(response.statusCode).toBe(400);
    expect(response.body.success).toBe(false);
    expect(response.body.error.code).toBe('VALIDATION_ERROR');
    expect(Array.isArray(response.body.error.details)).toBe(true);
    expect(response.body.error.details.length).toBeGreaterThan(0);
  });

  it('returns duplicate error when userId already exists', async () => {
    await request(app)
      .post('/api/v1/auth/signup')
      .send(buildValidPayload());

    const response = await request(app)
      .post('/api/v1/auth/signup')
      .send(buildValidPayload());

    expect(response.statusCode).toBe(409);
    expect(response.body.success).toBe(false);
    expect(response.body.error.code).toBe('USER_ID_ALREADY_EXISTS');
  });
});
