---
description: "Use when creating or modifying Node.js API code with Express, including routes, controllers, middleware, and server setup. Enforces ES modules and 2-space indentation."
name: "Express API Standards"
applyTo: ["**/*.js", "**/*.mjs", "**/*.cjs"]
---
# Express API Standards

- Runtime: MUST use Node.js API patterns for Express services and middleware.
- Modules: MUST use ES modules only (`import` and `export`). MUST NOT use `require`, `module.exports`, or `exports`.
- Formatting: MUST use 2-space indentation in all JavaScript files.
- Routing: MUST keep route handlers thin and delegate business logic to controller or service functions.
- Async handling: MUST use `async` or `await` for asynchronous code and MUST handle errors via `next(error)` or centralized error middleware.
- Responses: MUST return JSON with explicit HTTP status codes and a standard envelope shape: `{ success, data, error }`.
- Validation: MUST validate request input at the route or middleware boundary before invoking business logic.
- Config: MUST read environment variables through a dedicated config module instead of scattered `process.env` access.
- Project structure: MUST keep API code organized by feature or domain (routes, controllers, services, middleware, validators).
- Testing: MUST add or update tests for behavior changes in routes, controllers, and middleware.

## ES Module Example

```js
import express from 'express';

const router = express.Router();

router.get('/health', async (req, res, next) => {
  try {
    res.status(200).json({ success: true, data: { status: 'ok' }, error: null });
  } catch (error) {
    next(error);
  }
});

export default router;
```
