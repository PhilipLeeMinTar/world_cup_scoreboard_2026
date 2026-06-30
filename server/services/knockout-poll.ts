import { getDb } from '../db/index.js';
import { apiToOur } from './name-mapping.js';

const OPENFOOTBALL_URL =
  'https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json';

interface MatchScore {
  ft?: [number, number];
  et?: [number, number];
  p?: [number, number]; // openfootball uses 'p' for penalty shootout
}

interface KnockoutMatch {
  round: string;
  team1: string;
  team2: string;
  score?: MatchScore;
}

function getWinner(match: KnockoutMatch): string | null {
  const s = match.score;
  if (!s) return null;
  // Penalty shootout takes priority for overall winner
  if (s.p) {
    return s.p[0] > s.p[1] ? apiToOur(match.team1) : apiToOur(match.team2);
  }
  // Extra time
  if (s.et) {
    if (s.et[0] > s.et[1]) return apiToOur(match.team1);
    if (s.et[1] > s.et[0]) return apiToOur(match.team2);
  }
  // Full time
  if (s.ft) {
    if (s.ft[0] > s.ft[1]) return apiToOur(match.team1);
    if (s.ft[1] > s.ft[0]) return apiToOur(match.team2);
  }
  return null;
}

export async function pollKnockoutResults(): Promise<{ success: boolean; error?: string }> {
  try {
    const res = await fetch(OPENFOOTBALL_URL);
    if (!res.ok) throw new Error(`openfootball fetch returned ${res.status}`);
    const json = await res.json() as { matches: KnockoutMatch[] };

    const KNOCKOUT_ROUNDS = new Set(['Round of 32', 'Round of 16', 'Quarter-final', 'Semi-final', 'Final']);
    const knockoutMatches = (json.matches as KnockoutMatch[]).filter((m) => KNOCKOUT_ROUNDS.has(m.round));

    // Auto-derive the 32 R32 teams from fixtures
    const r32Matches = knockoutMatches.filter((m) => m.round === 'Round of 32');
    const r32Teams = r32Matches.flatMap((m) => [apiToOur(m.team1), apiToOur(m.team2)]);

    // Winners per round (only from completed matches)
    const r32Winners = r32Matches.map(getWinner).filter((w): w is string => w !== null);

    const r16Matches = knockoutMatches.filter((m) => m.round === 'Round of 16');
    const qfTeams = r16Matches.map(getWinner).filter((w): w is string => w !== null);

    const qfMatches = knockoutMatches.filter((m) => m.round === 'Quarter-final');
    const sfTeams = qfMatches.map(getWinner).filter((w): w is string => w !== null);

    const sfMatches = knockoutMatches.filter((m) => m.round === 'Semi-final');
    const finalTeams = sfMatches.map(getWinner).filter((w): w is string => w !== null);

    const finalMatch = knockoutMatches.find((m) => m.round === 'Final');
    const champion = finalMatch ? (getWinner(finalMatch) ?? '') : '';

    const db = getDb();
    const now = new Date().toISOString();

    if (r32Teams.length > 0) {
      db.prepare('INSERT OR REPLACE INTO knockout_teams (id, teams_json) VALUES (1, ?)').run(
        JSON.stringify(r32Teams)
      );
    }

    db.prepare(`
      INSERT OR REPLACE INTO knockout_results
        (id, r32_winners_json, qf_teams_json, sf_teams_json, final_teams_json, champion, updated_at)
      VALUES (1, ?, ?, ?, ?, ?, ?)
    `).run(
      JSON.stringify(r32Winners),
      JSON.stringify(qfTeams),
      JSON.stringify(sfTeams),
      JSON.stringify(finalTeams),
      champion,
      now
    );

    console.log(
      `Knockout poll OK — R32 teams: ${r32Teams.length}, R32 done: ${r32Winners.length}/16, ` +
      `QF: ${qfTeams.length}/8, SF: ${sfTeams.length}/4, Final: ${finalTeams.length}/2, Champion: ${champion || 'TBD'}`
    );

    return { success: true };
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    console.error('Knockout poll failed:', errorMsg);
    return { success: false, error: errorMsg };
  }
}

const POLL_INTERVAL_MS = 30 * 60 * 1000; // 30 minutes
let knockoutTimer: ReturnType<typeof setInterval> | null = null;

export function startKnockoutPolling() {
  if (knockoutTimer) return;

  pollKnockoutResults().then((r) => {
    console.log(r.success ? 'Knockout initial poll successful' : `Knockout initial poll failed: ${r.error}`);
  });

  knockoutTimer = setInterval(() => {
    pollKnockoutResults();
  }, POLL_INTERVAL_MS);

  console.log('Knockout polling started (every 30 minutes)');
}

export function stopKnockoutPolling() {
  if (knockoutTimer) {
    clearInterval(knockoutTimer);
    knockoutTimer = null;
  }
}
