import type { GroupStanding, Participant, Prediction, TeamStats, KnockoutStatus, KnockoutPrediction, KnockoutResults } from '../types';
import { apiToOur } from '../utils/name-mapping';
import { INITIAL_PARTICIPANTS } from '../data/participants';
import { KNOCKOUT_PREDICTIONS } from '../data/knockoutPredictions';
import { getDefaultStandings } from '../utils/scoring';

// ============ Mode Detection ============

export type AppMode = 'backend' | 'direct';

let detectedMode: AppMode | null = null;

export async function detectMode(): Promise<AppMode> {
  if (detectedMode) return detectedMode;
  try {
    const res = await fetch('/api/health', { signal: AbortSignal.timeout(2000) });
    if (res.ok) {
      detectedMode = 'backend';
      return 'backend';
    }
  } catch {
    // Backend not available
  }
  detectedMode = 'direct';
  return 'direct';
}

export function getMode(): AppMode {
  return detectedMode || 'direct';
}

// ============ Backend API (original) ============

const API_BASE = '/api';

async function backendFetchStandings(): Promise<{
  standings: GroupStanding[];
  updatedAt: string;
}> {
  const res = await fetch(`${API_BASE}/standings`);
  if (!res.ok) throw new Error(`Failed to fetch standings: ${res.status}`);
  return res.json();
}

async function backendRefreshStandings(): Promise<{
  standings: GroupStanding[];
  updatedAt: string;
  success: boolean;
  error?: string;
}> {
  const res = await fetch(`${API_BASE}/standings/refresh`, { method: 'POST' });
  if (!res.ok && res.status !== 409) throw new Error(`Failed to refresh: ${res.status}`);
  return res.json();
}

async function backendFetchParticipants(): Promise<Participant[]> {
  const res = await fetch(`${API_BASE}/participants`);
  if (!res.ok) throw new Error(`Failed to fetch participants: ${res.status}`);
  return res.json();
}

async function backendAddParticipant(participant: Omit<Participant, 'id'>): Promise<Participant> {
  const res = await fetch(`${API_BASE}/participants`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(participant),
  });
  if (!res.ok) throw new Error(`Failed to add participant: ${res.status}`);
  return res.json();
}

async function backendUpdateParticipant(id: string, data: Partial<Participant>): Promise<void> {
  const res = await fetch(`${API_BASE}/participants/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`Failed to update participant: ${res.status}`);
}

async function backendDeleteParticipant(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/participants/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Failed to delete participant: ${res.status}`);
}

async function backendFetchStatus(): Promise<PollStatus> {
  const res = await fetch(`${API_BASE}/status`);
  if (!res.ok) throw new Error(`Failed to fetch status: ${res.status}`);
  return res.json();
}

async function backendGetKnockoutStatus(): Promise<KnockoutStatus> {
  const res = await fetch(`${API_BASE}/knockout`);
  if (!res.ok) throw new Error(`Failed to fetch knockout status: ${res.status}`);
  return res.json();
}

async function backendGetKnockoutPredictions(): Promise<KnockoutPrediction[]> {
  const res = await fetch(`${API_BASE}/knockout/predictions`);
  if (!res.ok) throw new Error(`Failed to fetch knockout predictions: ${res.status}`);
  return res.json();
}

async function backendSaveKnockoutPrediction(
  participantId: string,
  picks: Omit<KnockoutPrediction, 'participantId' | 'participantName' | 'updatedAt'>
): Promise<void> {
  const res = await fetch(`${API_BASE}/knockout/predictions/${participantId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(picks),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { error?: string };
    throw new Error(err.error || `Failed to save knockout prediction: ${res.status}`);
  }
}


async function backendDeleteKnockoutPrediction(participantId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/knockout/predictions/${participantId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Failed to delete knockout prediction: ${res.status}`);
}

async function backendToggleKnockoutLock(): Promise<{ locked: boolean }> {
  const res = await fetch(`${API_BASE}/knockout/lock`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to toggle knockout lock: ${res.status}`);
  return res.json();
}

async function backendRefreshKnockoutResults(): Promise<void> {
  const res = await fetch(`${API_BASE}/knockout/refresh`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to refresh knockout results: ${res.status}`);
}

// ============ Direct API (GitHub Pages mode) ============

const OPENFOOTBALL_URL =
  'https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json';

interface OFMatch {
  group?: string;
  team1: string;
  team2: string;
  score?: { ft?: [number, number] };
}

interface OFTeamRecord {
  mp: number; w: number; d: number; l: number; gf: number; ga: number;
}

function computeStandingsFromMatches(matches: OFMatch[]): GroupStanding[] {
  const groupMatches = new Map<string, OFMatch[]>();
  for (const m of matches) {
    if (!m.group || !m.group.startsWith('Group ') || !m.score?.ft) continue;
    const g = m.group.replace('Group ', '');
    if (!groupMatches.has(g)) groupMatches.set(g, []);
    groupMatches.get(g)!.push(m);
  }

  const standings: GroupStanding[] = [];

  for (const [groupName, gMatches] of groupMatches) {
    const teamNames = new Set<string>();
    for (const m of gMatches) {
      teamNames.add(apiToOur(m.team1));
      teamNames.add(apiToOur(m.team2));
    }

    const records = new Map<string, OFTeamRecord>();
    for (const name of teamNames) {
      records.set(name, { mp: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0 });
    }

    for (const m of gMatches) {
      const t1 = apiToOur(m.team1);
      const t2 = apiToOur(m.team2);
      const [g1, g2] = m.score!.ft!;
      const r1 = records.get(t1)!;
      const r2 = records.get(t2)!;
      r1.mp++; r1.gf += g1; r1.ga += g2;
      r2.mp++; r2.gf += g2; r2.ga += g1;
      if (g1 > g2) { r1.w++; r2.l++; }
      else if (g1 < g2) { r1.l++; r2.w++; }
      else { r1.d++; r2.d++; }
    }

    const pts = (r: OFTeamRecord) => r.w * 3 + r.d;
    const gd = (r: OFTeamRecord) => r.gf - r.ga;

    function h2h(tied: string[]) {
      const result = new Map<string, { pts: number; gd: number; gf: number }>();
      for (const t of tied) result.set(t, { pts: 0, gd: 0, gf: 0 });
      for (const m of gMatches) {
        const t1 = apiToOur(m.team1);
        const t2 = apiToOur(m.team2);
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

    const teamList = [...teamNames];
    teamList.sort((a, b) => {
      const ra = records.get(a)!;
      const rb = records.get(b)!;
      const ptsDiff = pts(rb) - pts(ra);
      if (ptsDiff !== 0) return ptsDiff;
      const gdDiff = gd(rb) - gd(ra);
      if (gdDiff !== 0) return gdDiff;
      const gfDiff = rb.gf - ra.gf;
      if (gfDiff !== 0) return gfDiff;
      const h = h2h([a, b]);
      const ha = h.get(a)!; const hb = h.get(b)!;
      if (hb.pts !== ha.pts) return hb.pts - ha.pts;
      if (hb.gd !== ha.gd) return hb.gd - ha.gd;
      if (hb.gf !== ha.gf) return hb.gf - ha.gf;
      return a.localeCompare(b);
    });

    const teamsStats: TeamStats[] = teamList.map((name, i) => {
      const r = records.get(name)!;
      return { name, position: i + 1, mp: r.mp, w: r.w, d: r.d, l: r.l, gf: r.gf, ga: r.ga, gd: gd(r), pts: pts(r) };
    });

    standings.push({
      groupName,
      positions: { 1: teamList[0], 2: teamList[1], 3: teamList[2], 4: teamList[3] },
      teams: teamsStats,
    });
  }

  return standings.sort((a, b) => a.groupName.localeCompare(b.groupName));
}

async function directFetchStandings(): Promise<{
  standings: GroupStanding[];
  updatedAt: string;
}> {
  const res = await fetch(OPENFOOTBALL_URL, { signal: AbortSignal.timeout(15000), cache: 'no-store' });
  if (!res.ok) throw new Error(`openfootball fetch returned ${res.status}`);
  const json = await res.json() as { matches: OFMatch[] };
  const computed = computeStandingsFromMatches(json.matches);

  // If no group stage results yet, fall back to defaults
  if (computed.length === 0) {
    return { standings: getDefaultStandings(), updatedAt: new Date().toISOString() };
  }

  // Merge: use computed standings where available, defaults for groups not yet started
  const defaults = getDefaultStandings();
  const merged = defaults.map((def) => {
    const live = computed.find((c) => c.groupName === def.groupName);
    return live ?? def;
  });

  return { standings: merged, updatedAt: new Date().toISOString() };
}

// LocalStorage helpers for direct mode participants
const LS_KEY = 'wc2026_direct_participants';
const LS_VERSION_KEY = 'wc2026_direct_participants_version';

// Simple hash of INITIAL_PARTICIPANTS so we can detect when the bundled
// data has been updated and invalidate stale localStorage caches.
function hashParticipants(ps: Participant[]): string {
  let s = '';
  for (const p of ps) {
    s += p.id + '|';
    for (const pr of p.predictions) {
      s += pr.groupName + pr.champion + pr.runnerUp;
    }
  }
  // DJB2 hash
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = (h * 33) ^ s.charCodeAt(i);
  return (h >>> 0).toString(36);
}

const INITIAL_VERSION = hashParticipants(INITIAL_PARTICIPANTS);

function loadDirectParticipants(): Participant[] {
  try {
    const storedVersion = localStorage.getItem(LS_VERSION_KEY);
    const stored = localStorage.getItem(LS_KEY);
    // If the bundled data version changed, localStorage is stale — reset it
    if (stored && storedVersion === INITIAL_VERSION) return JSON.parse(stored);
    if (stored) {
      localStorage.removeItem(LS_KEY);
      localStorage.removeItem(LS_VERSION_KEY);
    }
  } catch { /* ignore */ }
  return INITIAL_PARTICIPANTS;
}

function saveDirectParticipants(participants: Participant[]) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(participants));
    localStorage.setItem(LS_VERSION_KEY, INITIAL_VERSION);
  } catch { /* ignore */ }
}

// ============ Direct mode — Knockout ============

interface OFKnockoutMatch {
  round: string;
  team1: string;
  team2: string;
  score?: { ft?: [number, number]; et?: [number, number]; pen?: [number, number] };
}

function knockoutWinner(m: OFKnockoutMatch): string | null {
  const s = m.score;
  if (!s) return null;
  if (s.pen) return s.pen[0] > s.pen[1] ? apiToOur(m.team1) : apiToOur(m.team2);
  if (s.et) {
    if (s.et[0] > s.et[1]) return apiToOur(m.team1);
    if (s.et[1] > s.et[0]) return apiToOur(m.team2);
  }
  if (s.ft) {
    if (s.ft[0] > s.ft[1]) return apiToOur(m.team1);
    if (s.ft[1] > s.ft[0]) return apiToOur(m.team2);
  }
  return null;
}

async function directFetchKnockoutStatus(): Promise<KnockoutStatus> {
  const res = await fetch(OPENFOOTBALL_URL, { signal: AbortSignal.timeout(15000), cache: 'no-store' });
  if (!res.ok) throw new Error(`openfootball fetch returned ${res.status}`);
  const json = await res.json() as { matches: OFKnockoutMatch[] };

  const KNOCKOUT_ROUNDS = new Set(['Round of 32', 'Round of 16', 'Quarter-final', 'Semi-final', 'Final']);
  const km = (json.matches as OFKnockoutMatch[]).filter((m) => KNOCKOUT_ROUNDS.has(m.round));

  const r32 = km.filter((m) => m.round === 'Round of 32');
  const teams = r32.flatMap((m) => [apiToOur(m.team1), apiToOur(m.team2)]);

  const results: KnockoutResults = {
    r32Winners: r32.map(knockoutWinner).filter((w): w is string => w !== null),
    qfTeams:    km.filter((m) => m.round === 'Round of 16').map(knockoutWinner).filter((w): w is string => w !== null),
    sfTeams:    km.filter((m) => m.round === 'Quarter-final').map(knockoutWinner).filter((w): w is string => w !== null),
    finalTeams: km.filter((m) => m.round === 'Semi-final').map(knockoutWinner).filter((w): w is string => w !== null),
    champion:   knockoutWinner(km.find((m) => m.round === 'Final') ?? { round: 'Final', team1: '', team2: '' }) ?? '',
  };

  return { locked: false, teams, results };
}

// ============ Unified API ============

export interface PollStatus {
  lastPollAt: string;
  lastPollStatus: string;
  apiSource: string;
  pollIntervalMinutes: number;
}

let directLastPollAt = '';
let directLastPollStatus = 'never';

export async function fetchStandings(): Promise<{
  standings: GroupStanding[];
  updatedAt: string;
}> {
  if (getMode() === 'backend') {
    const result = await backendFetchStandings();
    result.standings.sort((a, b) => a.groupName.localeCompare(b.groupName));
    return result;
  }
  const result = await directFetchStandings();
  directLastPollAt = result.updatedAt;
  directLastPollStatus = 'success';
  return result;
}

export async function refreshStandings(): Promise<{
  standings: GroupStanding[];
  updatedAt: string;
  success: boolean;
  error?: string;
}> {
  if (getMode() === 'backend') {
    return backendRefreshStandings();
  }
  try {
    const result = await directFetchStandings();
    directLastPollAt = result.updatedAt;
    directLastPollStatus = 'success';
    return { ...result, success: true };
  } catch (err) {
    directLastPollStatus = 'error';
    return {
      standings: getDefaultStandings(),
      updatedAt: directLastPollAt || new Date().toISOString(),
      success: false,
      error: err instanceof Error ? err.message : String(err),
    };
  }
}

export async function fetchParticipants(): Promise<Participant[]> {
  let participants: Participant[];
  if (getMode() === 'backend') {
    participants = await backendFetchParticipants();
  } else {
    participants = loadDirectParticipants();
  }
  return participants.sort((a, b) => a.name.localeCompare(b.name));
}

export async function addParticipant(participant: Omit<Participant, 'id'>): Promise<Participant> {
  if (getMode() === 'backend') {
    return backendAddParticipant(participant);
  }
  const newP: Participant = {
    id: `p_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    ...participant,
  };
  const current = loadDirectParticipants();
  saveDirectParticipants([...current, newP]);
  return newP;
}

export async function updateParticipant(id: string, data: Partial<Participant>): Promise<void> {
  if (getMode() === 'backend') {
    return backendUpdateParticipant(id, data);
  }
  const current = loadDirectParticipants();
  const updated = current.map((p) =>
    p.id === id ? { ...p, ...data } : p
  );
  saveDirectParticipants(updated);
}

export async function deleteParticipant(id: string): Promise<void> {
  if (getMode() === 'backend') {
    return backendDeleteParticipant(id);
  }
  const current = loadDirectParticipants();
  saveDirectParticipants(current.filter((p) => p.id !== id));
}

export async function fetchStatus(): Promise<PollStatus> {
  if (getMode() === 'backend') {
    return backendFetchStatus();
  }
  return {
    lastPollAt: directLastPollAt,
    lastPollStatus: directLastPollStatus,
    apiSource: 'openfootball/worldcup.json (direct)',
    pollIntervalMinutes: 120,
  };
}

export async function getKnockoutStatus(): Promise<KnockoutStatus> {
  if (getMode() === 'backend') {
    return backendGetKnockoutStatus();
  }
  try {
    return await directFetchKnockoutStatus();
  } catch {
    return { locked: false, teams: [], results: { r32Winners: [], qfTeams: [], sfTeams: [], finalTeams: [], champion: '' } };
  }
}

export async function getKnockoutPredictions(): Promise<KnockoutPrediction[]> {
  if (getMode() === 'backend') {
    return backendGetKnockoutPredictions();
  }
  return KNOCKOUT_PREDICTIONS;
}

export async function saveKnockoutPrediction(
  participantId: string,
  picks: Omit<KnockoutPrediction, 'participantId' | 'participantName' | 'updatedAt'>
): Promise<void> {
  if (getMode() === 'backend') {
    return backendSaveKnockoutPrediction(participantId, picks);
  }
  throw new Error('Knockout predictions require backend mode');
}


export async function deleteKnockoutPrediction(participantId: string): Promise<void> {
  if (getMode() === 'backend') {
    return backendDeleteKnockoutPrediction(participantId);
  }
  throw new Error('Deleting knockout predictions requires backend mode');
}

export async function toggleKnockoutLock(): Promise<{ locked: boolean }> {
  if (getMode() === 'backend') {
    return backendToggleKnockoutLock();
  }
  throw new Error('Toggling knockout lock requires backend mode');
}

export async function refreshKnockoutResults(): Promise<void> {
  if (getMode() === 'backend') {
    return backendRefreshKnockoutResults();
  }
  throw new Error('Refreshing knockout results requires backend mode');
}
