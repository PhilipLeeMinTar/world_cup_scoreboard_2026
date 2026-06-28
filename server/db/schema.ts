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

    CREATE TABLE IF NOT EXISTS knockout_teams (
      id INTEGER PRIMARY KEY,
      teams_json TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS knockout_predictions (
      participant_id TEXT PRIMARY KEY REFERENCES participants(id) ON DELETE CASCADE,
      r32_picks_json TEXT NOT NULL DEFAULT '[]',
      qf_picks_json TEXT NOT NULL DEFAULT '[]',
      sf_picks_json TEXT NOT NULL DEFAULT '[]',
      final_picks_json TEXT NOT NULL DEFAULT '[]',
      champion_pick TEXT NOT NULL DEFAULT '',
      updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS knockout_results (
      id INTEGER PRIMARY KEY,
      r32_winners_json TEXT NOT NULL DEFAULT '[]',
      qf_teams_json TEXT NOT NULL DEFAULT '[]',
      sf_teams_json TEXT NOT NULL DEFAULT '[]',
      final_teams_json TEXT NOT NULL DEFAULT '[]',
      champion TEXT NOT NULL DEFAULT '',
      updated_at TEXT NOT NULL
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
  metaInsert.run('knockout_predictions_locked', 'false');

  // Migration: add teams_json column to standings if not present
  try {
    db.exec('ALTER TABLE standings ADD COLUMN teams_json TEXT');
  } catch {
    // Column already exists
  }
}
