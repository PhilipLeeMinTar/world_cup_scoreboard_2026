import { getDb } from './index.js';
import { initSchema } from './schema.js';
import { WORLD_CUP_2026_GROUPS } from '../../src/data/groups.js';
import { INITIAL_PARTICIPANTS } from '../../src/data/participants.js';
import type { GroupStanding } from '../../src/types.js';

function getDefaultStandings(): GroupStanding[] {
  return WORLD_CUP_2026_GROUPS.map((g) => ({
    groupName: g.name,
    positions: {
      1: g.teams[0].name,
      2: g.teams[1].name,
      3: g.teams[2].name,
      4: g.teams[3].name,
    },
    teams: g.teams.map((t, i) => ({
      name: t.name,
      position: i + 1,
      mp: 0, w: 0, d: 0, l: 0,
      gf: 0, ga: 0, gd: 0, pts: 0,
    })),
  }));
}

export function seed() {
  const db = getDb();
  initSchema();

  // Seed groups
  const groupCount = db.prepare('SELECT COUNT(*) as count FROM groups').get() as { count: number };
  if (groupCount.count === 0) {
    const insertGroup = db.prepare(
      'INSERT INTO groups (name, teams_json) VALUES (?, ?)'
    );
    for (const group of WORLD_CUP_2026_GROUPS) {
      insertGroup.run(group.name, JSON.stringify(group.teams));
    }
    console.log(`Seeded ${WORLD_CUP_2026_GROUPS.length} groups`);
  }

  // Seed participants
  const participantCount = db.prepare('SELECT COUNT(*) as count FROM participants').get() as { count: number };
  if (participantCount.count === 0) {
    const insertParticipant = db.prepare(
      'INSERT INTO participants (id, name, predictions_json) VALUES (?, ?, ?)'
    );
    for (const p of INITIAL_PARTICIPANTS) {
      insertParticipant.run(p.id, p.name, JSON.stringify(p.predictions));
    }
    console.log(`Seeded ${INITIAL_PARTICIPANTS.length} participants`);
  }

  // Seed standings
  const standingsCount = db.prepare('SELECT COUNT(*) as count FROM standings').get() as { count: number };
  if (standingsCount.count === 0) {
    const insertStanding = db.prepare(
      'INSERT INTO standings (group_name, position_1, position_2, position_3, position_4, teams_json, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)'
    );
    const now = new Date().toISOString();
    for (const s of getDefaultStandings()) {
      insertStanding.run(
        s.groupName,
        s.positions[1],
        s.positions[2],
        s.positions[3],
        s.positions[4],
        s.teams ? JSON.stringify(s.teams) : null,
        now
      );
    }
    console.log(`Seeded ${getDefaultStandings().length} default standings`);
  }

  // Seed knockout_results default row
  const koResultsCount = db.prepare('SELECT COUNT(*) as count FROM knockout_results').get() as { count: number };
  if (koResultsCount.count === 0) {
    db.prepare(`INSERT INTO knockout_results (id, r32_winners_json, qf_teams_json, sf_teams_json, final_teams_json, champion, updated_at)
      VALUES (1, '[]', '[]', '[]', '[]', '', ?)`).run(new Date().toISOString());
    console.log('Seeded knockout_results default row');
  }

  console.log('Seed complete!');
}

// Only auto-run when executed directly, not when imported by the server
import { fileURLToPath } from 'url';
const __filename = fileURLToPath(import.meta.url);
if (process.argv[1] === __filename) {
  seed();
}
