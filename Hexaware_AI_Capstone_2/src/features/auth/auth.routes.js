import express from 'express';
import { signupController } from './auth.controller.js';
import { validateSignupPayload } from './auth.validator.js';

const router = express.Router();

router.post('/signup', validateSignupPayload, signupController);

export default router;
