/**
 * World Cup 2026 knockout bracket structure.
 * Encodes which R32 matches feed into which R16 matches, etc.
 * Derived from the openfootball API fixture W-codes.
 *
 * R32 match indices (0-15) correspond to the flat `status.teams` array:
 *   match i teams = [teams[2i], teams[2i+1]]
 *
 * The 16 R32 matches in API order:
 *  0: South Africa vs Canada
 *  1: Germany vs Paraguay
 *  2: Netherlands vs Morocco
 *  3: Brazil vs Japan
 *  4: France vs Sweden
 *  5: Ivory Coast vs Norway
 *  6: Mexico vs Ecuador
 *  7: England vs Congo DR
 *  8: USA vs Bosnia & Herzegovina
 *  9: Belgium vs Senegal
 * 10: Portugal vs Croatia
 * 11: Spain vs Austria
 * 12: Switzerland vs Algeria
 * 13: Argentina vs Cabo Verde
 * 14: Colombia vs Ghana
 * 15: Australia vs Egypt
 */

/** Which two R32 match winners play each R16 match. */
export const R16_FROM_R32: [number, number][] = [
  [1, 4],   // R16[0]: W74(Germany/Paraguay) vs W77(France/Sweden)
  [0, 2],   // R16[1]: W73(S.Africa/Canada) vs W75(Netherlands/Morocco)
  [3, 5],   // R16[2]: W76(Brazil/Japan) vs W78(Ivory Coast/Norway)
  [6, 7],   // R16[3]: W79(Mexico/Ecuador) vs W80(England/Congo DR)
  [10, 11], // R16[4]: W83(Portugal/Croatia) vs W84(Spain/Austria)
  [8, 9],   // R16[5]: W81(USA/Bosnia) vs W82(Belgium/Senegal)
  [13, 15], // R16[6]: W86(Argentina/Cabo Verde) vs W88(Australia/Egypt)
  [12, 14], // R16[7]: W85(Switzerland/Algeria) vs W87(Colombia/Ghana)
];

/** Which two R16 match winners play each QF match. */
export const QF_FROM_R16: [number, number][] = [
  [0, 1], // QF[0]: W89(R16[0]) vs W90(R16[1])
  [4, 5], // QF[1]: W93(R16[4]) vs W94(R16[5])
  [2, 3], // QF[2]: W91(R16[2]) vs W92(R16[3])
  [6, 7], // QF[3]: W95(R16[6]) vs W96(R16[7])
];

/** Which two QF match winners play each SF match. */
export const SF_FROM_QF: [number, number][] = [
  [0, 1], // SF[0]: W97(QF[0]) vs W98(QF[1])
  [2, 3], // SF[1]: W99(QF[2]) vs W100(QF[3])
];

/**
 * Visual top-to-bottom order of R32 matches in the bracket.
 * Groups matches that feed the same R16 match together.
 * Even-indexed in visual order = "top" of pair, Odd = "bottom".
 *
 * Visual grouping:
 *  Slots 0-1:   R32[1,4]    → R16[0]  → QF[0] → SF[0]
 *  Slots 2-3:   R32[0,2]    → R16[1]  → QF[0] → SF[0]
 *  Slots 4-5:   R32[10,11]  → R16[4]  → QF[1] → SF[0]
 *  Slots 6-7:   R32[8,9]    → R16[5]  → QF[1] → SF[0]
 *  Slots 8-9:   R32[3,5]    → R16[2]  → QF[2] → SF[1]
 *  Slots 10-11: R32[6,7]    → R16[3]  → QF[2] → SF[1]
 *  Slots 12-13: R32[13,15]  → R16[6]  → QF[3] → SF[1]
 *  Slots 14-15: R32[12,14]  → R16[7]  → QF[3] → SF[1]
 */
export const R32_IN_VISUAL_ORDER = [1, 4, 0, 2, 10, 11, 8, 9, 3, 5, 6, 7, 13, 15, 12, 14];

/**
 * Visual top-to-bottom order of R16 matches in the bracket.
 * Each R16 match spans 2 R32 visual slots.
 */
export const R16_IN_VISUAL_ORDER = [0, 1, 4, 5, 2, 3, 6, 7];

// QF [0,1,2,3] and SF [0,1] are already in correct visual order.

/**
 * Given the flat status.teams array (pairs: teams[2i], teams[2i+1] = match i),
 * return the 16 match pairs as [team1, team2][].
 */
export function r32PairsFromTeams(teams: string[]): [string, string][] {
  const pairs: [string, string][] = [];
  for (let i = 0; i + 1 < teams.length; i += 2) {
    pairs.push([teams[i], teams[i + 1]]);
  }
  return pairs;
}

/**
 * For each R32 match, determine which team was picked/won.
 * Uses membership check so old unordered pick arrays work correctly.
 */
export function matchWinners(
  pairs: [string, string][],
  pickedTeams: string[],
): (string | null)[] {
  const set = new Set(pickedTeams);
  return pairs.map(([t1, t2]) =>
    set.has(t1) ? t1 : set.has(t2) ? t2 : null
  );
}
