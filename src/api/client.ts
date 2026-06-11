import type { GroupStanding, Participant, Prediction } from '../types';
import { apiToOur } from '../utils/name-mapping';
import { INITIAL_PARTICIPANTS } from '../data/participants';
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

// ============ Direct API (GitHub Pages mode) ============

const LIVE_API_BASE = 'https://worldcup26.ir';

// CORS proxy for browser requests (worldcup26.ir doesn't set Access-Control-Allow-Origin
// for all origins, so we need a proxy when running from GitHub Pages or localhost)
const CORS_PROXY = 'https://corsproxy.io/?';

async function directFetch(url: string): Promise<Response> {
  // Try direct first (works if CORS is allowed)
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
    if (res.ok) return res;
  } catch {
    // Direct failed, try CORS proxy
  }
  const res = await fetch(`${CORS_PROXY}${encodeURIComponent(url)}`, {
    signal: AbortSignal.timeout(10000),
  });
  if (!res.ok) throw new Error(`API returned ${res.status}`);
  return res;
}

interface LiveApiTeam {
  id: string;
  name_en: string;
  groups: string;
}

interface LiveApiGroupTeam {
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

interface LiveApiGroup {
  name: string;
  teams: LiveApiGroupTeam[];
}

// Cache for direct mode
let cachedTeamMap: Map<string, string> | null = null;

async function getTeamMap(): Promise<Map<string, string>> {
  if (cachedTeamMap) return cachedTeamMap;
  const res = await directFetch(`${LIVE_API_BASE}/get/teams`);
  const data = await res.json() as { teams: LiveApiTeam[] };
  const map = new Map<string, string>();
  for (const t of data.teams) {
    map.set(t.id, apiToOur(t.name_en));
  }
  cachedTeamMap = map;
  return map;
}

async function directFetchStandings(): Promise<{
  standings: GroupStanding[];
  updatedAt: string;
}> {
  const teamMap = await getTeamMap();
  const res = await directFetch(`${LIVE_API_BASE}/get/groups`);
  const data = await res.json() as { groups: LiveApiGroup[] };

  const standings: GroupStanding[] = [];

  for (const group of data.groups) {
    const teams = group.teams;
    const hasResults = teams.some((t) => parseInt(t.mp || '0') > 0 || parseInt(t.pts || '0') > 0);

    if (!hasResults) {
      // Pre-tournament: use default standings
      const defaultStandings = getDefaultStandings();
      const defaultGroup = defaultStandings.find((s) => s.groupName === group.name);
      if (defaultGroup) standings.push(defaultGroup);
      continue;
    }

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

  return { standings, updatedAt: new Date().toISOString() };
}

// LocalStorage helpers for direct mode participants
const LS_KEY = 'wc2026_direct_participants';

function loadDirectParticipants(): Participant[] {
  try {
    const stored = localStorage.getItem(LS_KEY);
    if (stored) return JSON.parse(stored);
  } catch { /* ignore */ }
  return INITIAL_PARTICIPANTS;
}

function saveDirectParticipants(participants: Participant[]) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(participants));
  } catch { /* ignore */ }
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
    return backendFetchStandings();
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
  if (getMode() === 'backend') {
    return backendFetchParticipants();
  }
  return loadDirectParticipants();
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
    apiSource: 'worldcup26.ir (direct)',
    pollIntervalMinutes: 120,
  };
}
