import { Hono } from 'hono';
import { getCurrentStandings, pollStandings } from '../services/poll.js';
import { getDb } from '../db/index.js';

const standings = new Hono();

// GET /api/standings — return current group standings
standings.get('/', (c) => {
  const standings = getCurrentStandings();
  const db = getDb();
  const metaRow = db
    .prepare('SELECT value FROM meta WHERE key = ?')
    .get('last_poll_at') as { value: string } | undefined;

  return c.json({
    standings,
    updatedAt: metaRow?.value || new Date().toISOString(),
  });
});

// POST /api/standings/refresh — trigger manual API poll
standings.post('/refresh', async (c) => {
  const result = await pollStandings();

  if (!result.success && result.error === 'Poll already in progress') {
    return c.json(
      {
        standings: result.standings,
        updatedAt: result.updatedAt,
        message: 'A refresh is already in progress',
      },
      409
    );
  }

  return c.json({
    standings: result.standings,
    updatedAt: result.updatedAt,
    success: result.success,
    error: result.error,
  });
});

export default standings;
