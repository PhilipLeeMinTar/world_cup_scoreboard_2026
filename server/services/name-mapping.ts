/**
 * Bidirectional team name mapping between the football API and our groups.ts
 *
 * The API uses different names for 6 teams. This module provides
 * functions to convert between the two naming conventions.
 */

// API name → Our name (used when processing API data → our database)
const API_TO_OUR: Record<string, string> = {
  'Czech Republic': 'Czechia',
  'Turkey': 'Türkiye',
  'Iran': 'IR Iran',
  'Cape Verde': 'Cabo Verde',
  'Democratic Republic of the Congo': 'Congo DR',
  'DR Congo': 'Congo DR',
  'USA': 'United States',
  'Bosnia & Herzegovina': 'Bosnia and Herzegovina',
};

// Our name → API name (used when querying the API with our team names)
const OUR_TO_API: Record<string, string> = {
  'Czechia': 'Czech Republic',
  'Türkiye': 'Turkey',
  'IR Iran': 'Iran',
  'Cabo Verde': 'Cape Verde',
  'Congo DR': 'DR Congo',
  'United States': 'USA',
  'Bosnia and Herzegovina': 'Bosnia & Herzegovina',
};

/**
 * Convert an API team name to our internal name.
 * If no mapping exists, returns the name unchanged.
 */
export function apiToOur(name: string): string {
  return API_TO_OUR[name] || name;
}

/**
 * Convert our internal team name to the API's name.
 * If no mapping exists, returns the name unchanged.
 */
export function ourToApi(name: string): string {
  return OUR_TO_API[name] || name;
}

/**
 * Get all our internal team names (for validation).
 */
export function getAllOurNames(): string[] {
  return Object.values(API_TO_OUR);
}
