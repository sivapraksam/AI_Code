import { HttpError } from '../../utils/http-error.js';

const PASSWORD_SPECIAL_REGEX = /[^A-Za-z0-9\s]/;

function isValidDate(dateString) {
  const date = new Date(dateString);
  return Number.isNaN(date.getTime()) === false;
}

export function validateSignupPayload(req, res, next) {
  const errors = [];
  const {
    userId,
    password,
    confirmPassword,
    securityQuestion,
    securityAnswer,
    name,
    gender,
    dateOfBirth,
    occupation,
    email,
    mobile,
    nationality
  } = req.body || {};

  if (!userId || typeof userId !== 'string' || !/^(?=.*[A-Za-z])(?=.*\d).+$/.test(userId)) {
    errors.push('userId must contain at least one alphabetic character and one numeric character.');
  }

  if (!password || typeof password !== 'string') {
    errors.push('password is required.');
  } else {
    if (password.length < 8) {
      errors.push('password must be at least 8 characters.');
    }
    if (!/[a-z]/.test(password)) {
      errors.push('password must include a lowercase letter.');
    }
    if (!/[A-Z]/.test(password)) {
      errors.push('password must include an uppercase letter.');
    }
    if (!/\d/.test(password)) {
      errors.push('password must include a number.');
    }
    if (!PASSWORD_SPECIAL_REGEX.test(password)) {
      errors.push('password must include a supported special character.');
    }
    if (/\s/.test(password)) {
      errors.push('password must not include spaces.');
    }
  }

  if (!confirmPassword || confirmPassword !== password) {
    errors.push('confirmPassword must exactly match password.');
  }

  if (!securityQuestion || typeof securityQuestion !== 'string') {
    errors.push('securityQuestion is required.');
  }

  if (!securityAnswer || typeof securityAnswer !== 'string' || securityAnswer.trim().length === 0) {
    errors.push('securityAnswer is required.');
  }

  if (!name || typeof name !== 'string' || name.trim().length === 0) {
    errors.push('name is required.');
  }

  if (!gender || typeof gender !== 'string' || !['Male', 'Female', 'Transgender'].includes(gender)) {
    errors.push('gender must be one of Male, Female, or Transgender.');
  }

  if (!dateOfBirth || typeof dateOfBirth !== 'string' || !isValidDate(dateOfBirth)) {
    errors.push('dateOfBirth must be a valid date string.');
  }

  if (!occupation || typeof occupation !== 'string' || occupation.trim().length === 0) {
    errors.push('occupation is required.');
  }

  if (!email || typeof email !== 'string' || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errors.push('email must be a valid email address.');
  }

  if (!mobile || typeof mobile !== 'string' || !/^\d{10,15}$/.test(mobile)) {
    errors.push('mobile must contain 10 to 15 digits.');
  }

  if (!nationality || typeof nationality !== 'string' || nationality.trim().length === 0) {
    errors.push('nationality is required.');
  }

  if (errors.length > 0) {
    next(new HttpError(400, 'VALIDATION_ERROR', 'Request validation failed.', errors));
    return;
  }

  next();
}
