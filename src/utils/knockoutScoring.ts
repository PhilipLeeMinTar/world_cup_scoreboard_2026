import type { KnockoutPrediction, KnockoutResults, KnockoutScoreBreakdown, RankedKnockoutEntry } from '../types';

const WEIGHTS = { r32: 0.5, qf: 1, sf: 2, final: 4, champion: 8 };

function intersectCount(picks: string[], actuals: string[]): number {
  const actual = new Set(actuals);
  return picks.filter((p) => actual.has(p)).length;
}

export function calculateKnockoutScore(
  pred: KnockoutPrediction,
  results: KnockoutResults
): KnockoutScoreBreakdown {
  const r32Correct = intersectCount(pred.r32Picks, results.r32Winners);
  const qfCorrect = intersectCount(pred.qfPicks, results.qfTeams);
  const sfCorrect = intersectCount(pred.sfPicks, results.sfTeams);
  const finalCorrect = intersectCount(pred.finalPicks, results.finalTeams);
  const champCorrect = results.champion && pred.championPick === results.champion ? 1 : 0;

  return {
    r32: { correct: r32Correct, possible: results.r32Winners.length, points: r32Correct * WEIGHTS.r32 },
    qf:  { correct: qfCorrect,  possible: results.qfTeams.length,    points: qfCorrect  * WEIGHTS.qf  },
    sf:  { correct: sfCorrect,  possible: results.sfTeams.length,     points: sfCorrect  * WEIGHTS.sf  },
    final: { correct: finalCorrect, possible: results.finalTeams.length, points: finalCorrect * WEIGHTS.final },
    champion: { correct: champCorrect, possible: results.champion ? 1 : 0, points: champCorrect * WEIGHTS.champion },
    total: r32Correct * 0.5 + qfCorrect * 1 + sfCorrect * 2 + finalCorrect * 4 + champCorrect * 8,
  };
}

export function calculateKnockoutLeaderboard(
  predictions: KnockoutPrediction[],
  results: KnockoutResults
): RankedKnockoutEntry[] {
  const scored = predictions
    .map((p) => ({
      participantId: p.participantId,
      participantName: p.participantName,
      score: calculateKnockoutScore(p, results),
    }))
    .sort((a, b) => b.score.total - a.score.total);

  let rank = 1;
  return scored.map((entry, i) => {
    if (i > 0 && entry.score.total < scored[i - 1].score.total) rank = i + 1;
    return { ...entry, rank };
  });
}
