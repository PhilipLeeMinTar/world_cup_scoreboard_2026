import type { GroupStanding, TeamStats } from '../../src/types.js';

const OPENFOOTBALL_URL =
  'https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json';

// openfootball team name → our internal name
const API_TO_OUR: Record<string, string> = {
  'Czech Republic': 'Czechia',
  'Turkey': 'Türkiye',
  'Iran': 'IR Iran',
  'Cape Verde': 'Cabo Verde',
  'DR Congo': 'Congo DR',
  'Bosnia & Herzegovina': 'Bosnia and Herzegovina',
  'USA': 'United States',
};

function toOur(name: string): string {
  return API_TO_OUR[name] ?? name;
}

interface MatchScore {
  ft?: [number, number];
}

interface Match {
  group?: string;
  team1: string;
  team2: string;
  score?: MatchScore;
}

interface TeamRecord {
  mp: number;
  w: number;
  d: number;
  l: number;
  gf: number;
  ga: number;
}

/**
 * Compute standings from raw match results following FIFA tiebreaker order:
 * 1. Points
 * 2. Goal difference (all group matches)
 * 3. Goals scored (all group matches)
 * 4. Head-to-head points among tied teams
 * 5. Head-to-head goal difference among tied teams
 * 6. Head-to-head goals scored among tied teams
 */
function computeStandings(matches: Match[]): GroupStanding[] {
  // Group matches by group name, only those with final scores
  const groupMatches = new Map<string, Match[]>();
  for (const m of matches) {
    if (!m.group || !m.group.startsWith('Group ') || !m.score?.ft) continue;
    const g = m.group.replace('Group ', '');
    if (!groupMatches.has(g)) groupMatches.set(g, []);
    groupMatches.get(g)!.push(m);
  }

  const standings: GroupStanding[] = [];

  for (const [groupName, gMatches] of groupMatches) {
    // Collect all teams in this group
    const teamNames = new Set<string>();
    for (const m of gMatches) {
      teamNames.add(toOur(m.team1));
      teamNames.add(toOur(m.team2));
    }

    // Build records from match results
    const records = new Map<string, TeamRecord>();
    for (const name of teamNames) {
      records.set(name, { mp: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0 });
    }

    for (const m of gMatches) {
      const t1 = toOur(m.team1);
      const t2 = toOur(m.team2);
      const [g1, g2] = m.score!.ft!;
      const r1 = records.get(t1)!;
      const r2 = records.get(t2)!;

      r1.mp++; r1.gf += g1; r1.ga += g2;
      r2.mp++; r2.gf += g2; r2.ga += g1;

      if (g1 > g2) { r1.w++; r2.l++; }
      else if (g1 < g2) { r1.l++; r2.w++; }
      else { r1.d++; r2.d++; }
    }

    const pts = (r: TeamRecord) => r.w * 3 + r.d;
    const gd = (r: TeamRecord) => r.gf - r.ga;

    // Head-to-head stats between a subset of teams
    function h2h(tied: string[]): Map<string, { pts: number; gd: number; gf: number }> {
      const result = new Map<string, { pts: number; gd: number; gf: number }>();
      for (const t of tied) result.set(t, { pts: 0, gd: 0, gf: 0 });

      for (const m of gMatches) {
        const t1 = toOur(m.team1);
        const t2 = toOur(m.team2);
        if (!tied.includes(t1) || !tied.includes(t2)) continue;
        const [g1, g2] = m.score!.ft!;
        const r1 = result.get(t1)!;
        const r2 = result.get(t2)!;

        r1.gf += g1; r1.gd += g1 - g2;
        r2.gf += g2; r2.gd += g2 - g1;

        if (g1 > g2) r1.pts += 3;
        else if (g1 < g2) r2.pts += 3;
        else { r1.pts += 1; r2.pts += 1; }
      }
      return result;
    }

    // Sort teams with full FIFA tiebreaker chain
    const teamList = [...teamNames];
    teamList.sort((a, b) => {
      const ra = records.get(a)!;
      const rb = records.get(b)!;

      // 1. Points
      const ptsDiff = pts(rb) - pts(ra);
      if (ptsDiff !== 0) return ptsDiff;

      // 2. Goal difference
      const gdDiff = gd(rb) - gd(ra);
      if (gdDiff !== 0) return gdDiff;

      // 3. Goals scored
      const gfDiff = rb.gf - ra.gf;
      if (gfDiff !== 0) return gfDiff;

      // 4-6. Head-to-head (between these two teams only)
      const h = h2h([a, b]);
      const ha = h.get(a)!;
      const hb = h.get(b)!;

      const h2hPts = hb.pts - ha.pts;
      if (h2hPts !== 0) return h2hPts;

      const h2hGd = hb.gd - ha.gd;
      if (h2hGd !== 0) return h2hGd;

      const h2hGf = hb.gf - ha.gf;
      if (h2hGf !== 0) return h2hGf;

      // Last resort: alphabetical (stable placeholder until disciplinary/ranking data available)
      return a.localeCompare(b);
    });

    const teamsStats: TeamStats[] = teamList.map((name, i) => {
      const r = records.get(name)!;
      return {
        name,
        position: i + 1,
        mp: r.mp,
        w: r.w,
        d: r.d,
        l: r.l,
        gf: r.gf,
        ga: r.ga,
        gd: gd(r),
        pts: pts(r),
      };
    });

    standings.push({
      groupName,
      positions: {
        1: teamList[0],
        2: teamList[1],
        3: teamList[2],
        4: teamList[3],
      },
      teams: teamsStats,
    });
  }

  return standings.sort((a, b) => a.groupName.localeCompare(b.groupName));
}

/**
 * Fetch current group standings from openfootball match data.
 * Computes standings from actual match results rather than relying on
 * a pre-sorted third-party API, ensuring accuracy.
 */
export async function fetchStandingsFromApi(): Promise<{
  standings: GroupStanding[];
  source: string;
}> {
  const res = await fetch(OPENFOOTBALL_URL);
  if (!res.ok) {
    throw new Error(`openfootball fetch returned ${res.status}`);
  }

  const json = await res.json() as { matches: Match[] };
  const standings = computeStandings(json.matches);

  return { standings, source: 'openfootball/worldcup.json' };
}
