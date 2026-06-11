import { getDb } from './index.js';

export function initSchema() {
  const db = getDb();

  db.exec(`
    CREATE TABLE IF NOT EXISTS groups (
      name TEXT PRIMARY KEY,
      teams_json TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS participants (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      predictions_json TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS standings (
      group_name TEXT PRIMARY KEY,
      position_1 TEXT NOT NULL,
      position_2 TEXT NOT NULL,
      position_3 TEXT NOT NULL,
      position_4 TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS meta (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL
    );
  `);

  // Initialize meta defaults
  const metaInsert = db.prepare(
    'INSERT OR IGNORE INTO meta (key, value) VALUES (?, ?)'
  );
  metaInsert.run('last_poll_at', '');
  metaInsert.run('last_poll_status', 'never');
  metaInsert.run('api_source', 'worldcup26.ir');
  metaInsert.run('next_poll_at', '');
}
