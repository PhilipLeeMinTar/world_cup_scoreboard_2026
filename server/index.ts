import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { serveStatic } from '@hono/node-server/serve-static';
import { getDb, closeDb } from './db/index.js';
import { initSchema } from './db/schema.js';
import { startPolling, stopPolling } from './services/poll.js';
import standingsRoutes from './routes/standings.js';
import participantsRoutes from './routes/participants.js';
import statusRoutes from './routes/status.js';

const app = new Hono();
const PORT = parseInt(process.env.PORT || '3001', 10);

// Middleware
app.use('/api/*', cors());

// API routes
app.route('/api/standings', standingsRoutes);
app.route('/api/participants', participantsRoutes);
app.route('/api/status', statusRoutes);

// Health check
app.get('/api/health', (c) => c.json({ status: 'ok', timestamp: new Date().toISOString() }));

// In production, serve the built frontend as static files
if (process.env.NODE_ENV === 'production') {
  app.use('/*', serveStatic({ root: './dist' }));
}

// Initialize database and start server
async function start() {
  // Initialize database
  const db = getDb();
  initSchema();

  // Check if we need to seed (no standings in DB)
  const count = db.prepare('SELECT COUNT(*) as count FROM standings').get() as { count: number };
  if (count.count === 0) {
    console.log('No standings found. Run `npm run seed` to populate the database.');
  }

  // Start polling service
  startPolling();

  // Start HTTP server
  const { serve } = await import('@hono/node-server');
  serve({ fetch: app.fetch, port: PORT }, (info) => {
    console.log(`🚀 Server running at http://localhost:${info.port}`);
    console.log(`📊 API available at http://localhost:${info.port}/api/`);
  });

  // Graceful shutdown
  process.on('SIGINT', () => {
    console.log('\nShutting down...');
    stopPolling();
    closeDb();
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    stopPolling();
    closeDb();
    process.exit(0);
  });
}

start().catch((err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});

export default app;
