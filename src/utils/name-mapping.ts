/**
 * Bidirectional team name mapping between the football API and our groups.ts
 * Shared between frontend and backend.
 */

// openfootball team name → our internal name
const API_TO_OUR: Record<string, string> = {
  'Czech Republic': 'Czechia',
  'Turkey': 'Türkiye',
  'Iran': 'IR Iran',
  'Cape Verde': 'Cabo Verde',
  'Democratic Republic of the Congo': 'Congo DR',
  'DR Congo': 'Congo DR',
  'Bosnia & Herzegovina': 'Bosnia and Herzegovina',
  'USA': 'United States',
};

/**
 * Convert an API team name to our internal name.
 * If no mapping exists, returns the name unchanged.
 */
export function apiToOur(name: string): string {
  return API_TO_OUR[name] || name;
}
