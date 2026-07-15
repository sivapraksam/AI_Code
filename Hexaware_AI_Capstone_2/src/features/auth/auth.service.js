import { randomBytes, randomUUID, scrypt as nodeScrypt } from 'node:crypto';
import { promisify } from 'node:util';
import { HttpError } from '../../utils/http-error.js';

const scrypt = promisify(nodeScrypt);
const usersById = new Map();

async function hashPassword(plainTextPassword) {
  const salt = randomBytes(16).toString('hex');
  const derivedKey = await scrypt(plainTextPassword, salt, 64);
  return `${salt}:${derivedKey.toString('hex')}`;
}

export async function registerUser(input) {
  if (usersById.has(input.userId)) {
    throw new HttpError(409, 'USER_ID_ALREADY_EXISTS', 'User ID already exists');
  }

  const passwordHash = await hashPassword(input.password);

  const user = {
    id: randomUUID(),
    userId: input.userId,
    name: input.name.trim(),
    gender: input.gender,
    dateOfBirth: input.dateOfBirth,
    occupation: input.occupation.trim(),
    email: input.email.toLowerCase(),
    mobile: input.mobile,
    nationality: input.nationality,
    securityQuestion: input.securityQuestion,
    securityAnswer: input.securityAnswer.trim(),
    createdAt: new Date().toISOString(),
    passwordHash
  };

  usersById.set(user.userId, user);

  return {
    id: user.id,
    userId: user.userId,
    name: user.name,
    email: user.email,
    mobile: user.mobile,
    nationality: user.nationality,
    createdAt: user.createdAt
  };
}

export function resetUsersStore() {
  usersById.clear();
}
