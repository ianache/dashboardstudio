'use strict';

import express from 'express';
import config from '../config.js';

const router = express.Router();

// Helper function to check if a service is alive
async function checkService(url, options = {}) {
  try {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), 2000); // 2-second timeout
    const res = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(id);
    
    // 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout mean the service is down
    if (res.status === 502 || res.status === 503 || res.status === 504) {
      return false;
    }
    
    // Any other response (2xx, 3xx, 4xx) indicates the service is running and responding
    return true;
  } catch (err) {
    return false;
  }
}

router.get('/health', async (req, res) => {
  // Check /readyz first for CubeJS, fallback to cubejs-api path
  const [backendAlive, aiAlive, cubejsAlive] = await Promise.all([
    checkService(`${config.backendUrl}/health`),
    checkService(`${config.aiServiceUrl}/health`),
    checkService(`${config.cubejsUrl}/readyz`).then(alive => 
      alive ? true : checkService(`${config.cubejsUrl}/cubejs-api/v1/meta`)
    )
  ]);

  res.json({
    status: 'OK',
    services: {
      bff: 'green',
      backend: backendAlive ? 'green' : 'red',
      ai: aiAlive ? 'green' : 'red',
      cubejs: cubejsAlive ? 'green' : 'red'
    }
  });
});

export default router;
