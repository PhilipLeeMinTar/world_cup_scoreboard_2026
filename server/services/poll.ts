import { getDb } from '../db/index.js';
import { fetchStandingsFromApi } from './api-client.js';
import type { GroupStanding } from '../../src/types.js';

const POLL_INTERVAL_MS = 2 * 60 * 60 * 1000; // 2 hours
let pollTimer: ReturnType<typeof setInterval> | null = null;
let isPolling = false;

/**
 * Perform a single poll: fetch from API and update the database.
 */
export async function pollStandings(): Promise<{
  success: boolean;
  standings: GroupStanding[];
  updatedAt: string;
  error?: string;
}> {
  if (isPolling) {
    return {
      success: false,
      standings: getCurrentStandings(),
      updatedAt: getMeta('last_poll_at') || new Date().toISOString(),
      error: 'Poll already in progress',
    };
  }

  isPolling = true;
  const db = getDb();

  try {
    const result = await fetchStandingsFromApi();
    const now = new Date().toISOString();

    // Always update meta on successful API call
    setMeta('last_poll_at', now);
    setMeta('last_poll_status', 'success');
    setMeta('api_source', result.source);

    if (result.standings.length > 0) {
      const upsertStanding = db.prepare(`
        INSERT INTO standings (group_name, position_1, position_2, position_3, position_4, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(group_name) DO UPDATE SET
          position_1 = excluded.position_1,
          position_2 = excluded.position_2,
          position_3 = excluded.position_3,
          position_4 = excluded.position_4,
          updated_at = excluded.updated_at
      `);

      for (const s of result.standings) {
        upsertStanding.run(
          s.groupName,
          s.positions[1],
          s.positions[2],
          s.positions[3],
          s.positions[4],
          now
        );
      }
    }

    return {
      success: true,
      standings: getCurrentStandings(),
      updatedAt: getMeta('last_poll_at') || new Date().toISOString(),
    };
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    console.error('Poll failed:', errorMsg);
    setMeta('last_poll_status', `error: ${errorMsg}`);

    return {
      success: false,
      standings: getCurrentStandings(),
      updatedAt: getMeta('last_poll_at') || new Date().toISOString(),
      error: errorMsg,
    };
  } finally {
    isPolling = false;
  }
}

/**
 * Start the automatic polling interval.
 */
export function startPolling() {
  if (pollTimer) return;

  // Poll immediately on startup
  pollStandings().then((result) => {
    if (result.success) {
      console.log('Initial poll successful');
    } else {
      console.warn('Initial poll failed:', result.error);
    }
  });

  // Then poll every 2 hours
  pollTimer = setInterval(async () => {
    const result = await pollStandings();
    if (result.success) {
      console.log('Scheduled poll successful');
    } else {
      console.warn('Scheduled poll failed:', result.error);
    }
  }, POLL_INTERVAL_MS);

  console.log(`Polling started (every ${POLL_INTERVAL_MS / 1000 / 60} minutes)`);
}

/**
 * Stop the automatic polling interval.
 */
export function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
    console.log('Polling stopped');
  }
}

/**
 * Read current standings from the database.
 */
export function getCurrentStandings(): GroupStanding[] {
  const db = getDb();
  const rows = db
    .prepare('SELECT group_name, position_1, position_2, position_3, position_4 FROM standings ORDER BY group_name')
    .all() as Array<{
    group_name: string;
    position_1: string;
    position_2: string;
    position_3: string;
    position_4: string;
  }>;

  return rows.map((r) => ({
    groupName: r.group_name,
    positions: {
      1: r.position_1,
      2: r.position_2,
      3: r.position_3,
      4: r.position_4,
    },
  }));
}

function getMeta(key: string): string {
  const db = getDb();
  const row = db.prepare('SELECT value FROM meta WHERE key = ?').get(key) as { value: string } | undefined;
  return row?.value || '';
}

function setMeta(key: string, value: string) {
  const db = getDb();
  db.prepare('INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value').run(key, value);
}
