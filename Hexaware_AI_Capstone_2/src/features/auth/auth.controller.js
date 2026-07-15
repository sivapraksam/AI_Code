import { registerUser } from './auth.service.js';
import { sendSuccess } from '../../utils/response.js';

export async function signupController(req, res, next) {
  try {
    const createdUser = await registerUser(req.body);
    sendSuccess(res, 201, {
      user: createdUser
    });
  } catch (error) {
    next(error);
  }
}
