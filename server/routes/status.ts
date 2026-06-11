import { Hono } from 'hono';
import { getDb } from '../db/index.js';

const status = new Hono();

// GET /api/status — return poll status info
status.get('/', (c) => {
  const db = getDb();
  const getMeta = (key: string) => {
    const row = db.prepare('SELECT value FROM meta WHERE key = ?').get(key) as { value: string } | undefined;
    return row?.value || '';
  };

  return c.json({
    lastPollAt: getMeta('last_poll_at'),
    lastPollStatus: getMeta('last_poll_status'),
    apiSource: getMeta('api_source'),
    pollIntervalMinutes: 120,
  });
});

export default status;
