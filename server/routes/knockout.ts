import { Hono } from 'hono';
import { getDb } from '../db/index.js';
import { pollKnockoutResults } from '../services/knockout-poll.js';
import type { KnockoutPrediction, KnockoutResults, KnockoutStatus } from '../../src/types.js';

const knockout = new Hono();

// GET /api/knockout — status: locked flag, R32 teams, results
knockout.get('/', (c) => {
  const db = getDb();

  const lockedRow = db.prepare("SELECT value FROM meta WHERE key = 'knockout_predictions_locked'").get() as { value: string } | undefined;
  const locked = lockedRow?.value === 'true';

  const teamsRow = db.prepare('SELECT teams_json FROM knockout_teams WHERE id = 1').get() as { teams_json: string } | undefined;
  const teams: string[] = teamsRow ? JSON.parse(teamsRow.teams_json) : [];

  const resultsRow = db.prepare('SELECT * FROM knockout_results WHERE id = 1').get() as {
    r32_winners_json: string;
    qf_teams_json: string;
    sf_teams_json: string;
    final_teams_json: string;
    champion: string;
    updated_at: string;
  } | undefined;

  const results: KnockoutResults = resultsRow
    ? {
        r32Winners: JSON.parse(resultsRow.r32_winners_json),
        qfTeams: JSON.parse(resultsRow.qf_teams_json),
        sfTeams: JSON.parse(resultsRow.sf_teams_json),
        finalTeams: JSON.parse(resultsRow.final_teams_json),
        champion: resultsRow.champion,
      }
    : { r32Winners: [], qfTeams: [], sfTeams: [], finalTeams: [], champion: '' };

  const lastUpdated = resultsRow?.updated_at ?? '';

  const status: KnockoutStatus & { lastUpdated: string } = { locked, teams, results, lastUpdated };
  return c.json(status);
});

// GET /api/knockout/predictions — all predictions joined with participant name
knockout.get('/predictions', (c) => {
  const db = getDb();
  const rows = db.prepare(`
    SELECT kp.participant_id, p.name, kp.r32_picks_json, kp.qf_picks_json,
           kp.sf_picks_json, kp.final_picks_json, kp.champion_pick, kp.updated_at
    FROM knockout_predictions kp
    JOIN participants p ON p.id = kp.participant_id
    ORDER BY p.name
  `).all() as Array<{
    participant_id: string;
    name: string;
    r32_picks_json: string;
    qf_picks_json: string;
    sf_picks_json: string;
    final_picks_json: string;
    champion_pick: string;
    updated_at: string;
  }>;

  const result: KnockoutPrediction[] = rows.map((r) => ({
    participantId: r.participant_id,
    participantName: r.name,
    r32Picks: JSON.parse(r.r32_picks_json),
    qfPicks: JSON.parse(r.qf_picks_json),
    sfPicks: JSON.parse(r.sf_picks_json),
    finalPicks: JSON.parse(r.final_picks_json),
    championPick: r.champion_pick,
    updatedAt: r.updated_at,
  }));

  return c.json(result);
});

// PUT /api/knockout/predictions/:participantId — save a participant's picks
knockout.put('/predictions/:participantId', async (c) => {
  const db = getDb();
  const lockedRow = db.prepare("SELECT value FROM meta WHERE key = 'knockout_predictions_locked'").get() as { value: string } | undefined;
  if (lockedRow?.value === 'true') {
    return c.json({ error: 'Predictions are locked' }, 403);
  }

  const participantId = c.req.param('participantId');
  const body = await c.req.json() as {
    r32Picks: string[];
    qfPicks: string[];
    sfPicks: string[];
    finalPicks: string[];
    championPick: string;
  };

  const participant = db.prepare('SELECT id FROM participants WHERE id = ?').get(participantId);
  if (!participant) {
    return c.json({ error: 'Participant not found' }, 404);
  }

  db.prepare(`
    INSERT OR REPLACE INTO knockout_predictions
      (participant_id, r32_picks_json, qf_picks_json, sf_picks_json, final_picks_json, champion_pick, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).run(
    participantId,
    JSON.stringify(body.r32Picks),
    JSON.stringify(body.qfPicks),
    JSON.stringify(body.sfPicks),
    JSON.stringify(body.finalPicks),
    body.championPick,
    new Date().toISOString()
  );

  return c.json({ success: true });
});

// DELETE /api/knockout/predictions/:participantId — remove a participant's predictions
knockout.delete('/predictions/:participantId', (c) => {
  const db = getDb();
  const participantId = c.req.param('participantId');
  db.prepare('DELETE FROM knockout_predictions WHERE participant_id = ?').run(participantId);
  return c.json({ success: true });
});

// POST /api/knockout/refresh — manually trigger a live data poll
knockout.post('/refresh', async (c) => {
  const result = await pollKnockoutResults();
  if (result.success) {
    return c.json({ success: true });
  }
  return c.json({ success: false, error: result.error }, 500);
});

// POST /api/knockout/lock — toggle predictions locked/unlocked
knockout.post('/lock', (c) => {
  const db = getDb();
  const row = db.prepare("SELECT value FROM meta WHERE key = 'knockout_predictions_locked'").get() as { value: string } | undefined;
  const current = row?.value === 'true';
  const next = !current;
  db.prepare("INSERT OR REPLACE INTO meta (key, value) VALUES ('knockout_predictions_locked', ?)").run(next ? 'true' : 'false');
  return c.json({ locked: next });
});

export default knockout;
