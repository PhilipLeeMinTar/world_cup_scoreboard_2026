/**
 * Bidirectional team name mapping between the football API and our groups.ts
 * Shared between frontend and backend.
 */

// API name → Our name (used when processing API data → our database)
const API_TO_OUR: Record<string, string> = {
  'Czech Republic': 'Czechia',
  'Turkey': 'Türkiye',
  'Iran': 'IR Iran',
  'Cape Verde': 'Cabo Verde',
  'Democratic Republic of the Congo': 'Congo DR',
  'DR Congo': 'Congo DR',
};

/**
 * Convert an API team name to our internal name.
 * If no mapping exists, returns the name unchanged.
 */
export function apiToOur(name: string): string {
  return API_TO_OUR[name] || name;
}
