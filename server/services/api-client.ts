import { apiToOur } from './name-mapping.js';
import type { GroupStanding } from '../../src/types.js';

const API_BASE = 'https://worldcup26.ir';

interface ApiTeam {
  id: string;
  name_en: string;
  groups: string;
}

interface ApiGroupTeam {
  team_id: string;
  mp: string;
  w: string;
  d: string;
  l: string;
  pts: string;
  gf: string;
  ga: string;
  gd: string;
}

interface ApiGroup {
  name: string;
  teams: ApiGroupTeam[];
}

/**
 * Fetch current group standings from the World Cup API.
 * Returns mapped GroupStanding[] using our internal team names.
 */
export async function fetchStandingsFromApi(): Promise<{
  standings: GroupStanding[];
  source: string;
}> {
  // Fetch teams for name mapping
  const teamsRes = await fetch(`${API_BASE}/get/teams`);
  if (!teamsRes.ok) {
    throw new Error(`Teams API returned ${teamsRes.status}`);
  }
  const teamsJson = await teamsRes.json() as { teams: ApiTeam[] };
  const teamMap = new Map<string, string>();
  for (const t of teamsJson.teams) {
    teamMap.set(t.id, apiToOur(t.name_en));
  }

  // Fetch groups/standings
  const groupsRes = await fetch(`${API_BASE}/get/groups`);
  if (!groupsRes.ok) {
    throw new Error(`Groups API returned ${groupsRes.status}`);
  }
  const groupsJson = await groupsRes.json() as { groups: ApiGroup[] };

  const standings: GroupStanding[] = [];

  for (const group of groupsJson.groups) {
    const teams = group.teams;

    // Check if any team has played matches (all zeroes = pre-tournament)
    const hasResults = teams.some((t) => parseInt(t.mp || '0') > 0 || parseInt(t.pts || '0') > 0);

    if (!hasResults) {
      // Keep existing default standings for this group - don't overwrite
      continue;
    }

    // Sort by: pts desc, goal diff desc, goals for desc
    const sorted = [...teams].sort((a, b) => {
      const ptsDiff = parseInt(b.pts || '0') - parseInt(a.pts || '0');
      if (ptsDiff !== 0) return ptsDiff;
      const gdDiff = parseInt(b.gd || '0') - parseInt(a.gd || '0');
      if (gdDiff !== 0) return gdDiff;
      return parseInt(b.gf || '0') - parseInt(a.gf || '0');
    });

    const positions: GroupStanding['positions'] = {
      1: teamMap.get(sorted[0]?.team_id) || `Team ${sorted[0]?.team_id}`,
      2: teamMap.get(sorted[1]?.team_id) || `Team ${sorted[1]?.team_id}`,
      3: teamMap.get(sorted[2]?.team_id) || `Team ${sorted[2]?.team_id}`,
      4: teamMap.get(sorted[3]?.team_id) || `Team ${sorted[3]?.team_id}`,
    };

    standings.push({ groupName: group.name, positions });
  }

  return { standings, source: 'worldcup26.ir' };
}
