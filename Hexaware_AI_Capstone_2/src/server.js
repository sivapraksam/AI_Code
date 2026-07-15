import app from './app.js';
import env from './config/env.js';

app.listen(env.port, () => {
  console.info(`Server running on port ${env.port} in ${env.nodeEnv} mode.`);
});
