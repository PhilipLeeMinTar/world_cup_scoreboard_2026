import {
  Participant,
  GroupStanding,
  ScoreBreakdown,
  GroupScoreDetail,
  Prediction,
} from '../types';
import { WORLD_CUP_2026_GROUPS } from '../data/groups';

/**
 * Scoring rules:
 * - Correct champion (1st place) guess: +5
 * - Correct runner-up (2nd place) guess: +3
 * - Incorrect position guess, but team still advances (1st or 2nd): +1 per team
 *
 * Note: In World Cup 2026, top 2 from each group advance + 8 best 3rd-place teams.
 * For the purposes of this group-stage betting, "advancing" means finishing 1st or 2nd in the group.
 */

const POINTS_CORRECT_CHAMPION = 5;
const POINTS_CORRECT_RUNNER_UP = 3;
const POINTS_ADVANCEMENT_BONUS = 1;

export function calculateScore(
  participant: Participant,
  standings: GroupStanding[]
): ScoreBreakdown {
  const details: GroupScoreDetail[] = [];

  for (const standing of standings) {
    const prediction = participant.predictions.find(
      (p) => p.groupName === standing.groupName
    );

    if (!prediction) {
      details.push({
        groupName: standing.groupName,
        predictedChampion: '-',
        predictedRunnerUp: '-',
        actualChampion: standing.positions[1],
        actualRunnerUp: standing.positions[2],
        championPoints: 0,
        runnerUpPoints: 0,
        advancementBonus: 0,
        groupTotal: 0,
        championReason: 'No prediction',
        runnerUpReason: 'No prediction',
        advancementReason: 'No prediction',
      });
      continue;
    }

    let championPoints = 0;
    let runnerUpPoints = 0;
    let advancementBonus = 0;
    let championReason = '';
    let runnerUpReason = '';
    let advancementReason = '';

    // Check champion prediction
    if (prediction.champion === standing.positions[1]) {
      championPoints = POINTS_CORRECT_CHAMPION;
      championReason = `Correct! ${prediction.champion} finished 1st (+5)`;
    } else if (
      prediction.champion === standing.positions[2]
    ) {
      advancementBonus += POINTS_ADVANCEMENT_BONUS;
      championReason = `${prediction.champion} finished 2nd, not 1st (+1 advancement bonus)`;
    } else {
      championReason = `${prediction.champion} did not finish 1st or 2nd (+0)`;
    }

    // Check runner-up prediction
    if (prediction.runnerUp === standing.positions[2]) {
      runnerUpPoints = POINTS_CORRECT_RUNNER_UP;
      runnerUpReason = `Correct! ${prediction.runnerUp} finished 2nd (+3)`;
    } else if (
      prediction.runnerUp === standing.positions[1]
    ) {
      advancementBonus += POINTS_ADVANCEMENT_BONUS;
      runnerUpReason = `${prediction.runnerUp} finished 1st, not 2nd (+1 advancement bonus)`;
    } else {
      runnerUpReason = `${prediction.runnerUp} did not finish 1st or 2nd (+0)`;
    }

    const groupTotal = championPoints + runnerUpPoints + advancementBonus;

    if (advancementBonus > 0) {
      const bonusTeams: string[] = [];
      if (prediction.champion !== standing.positions[1] && (prediction.champion === standing.positions[1] || prediction.champion === standing.positions[2])) {
        // Already handled above
      }
      advancementReason = `Advancement bonus: +${advancementBonus}`;
    } else {
      advancementReason = 'No advancement bonus';
    }

    details.push({
      groupName: standing.groupName,
      predictedChampion: prediction.champion,
      predictedRunnerUp: prediction.runnerUp,
      actualChampion: standing.positions[1],
      actualRunnerUp: standing.positions[2],
      championPoints,
      runnerUpPoints,
      advancementBonus,
      groupTotal,
      championReason,
      runnerUpReason,
      advancementReason,
    });
  }

  const totalPoints = details.reduce((sum, d) => sum + d.groupTotal, 0);

  return { totalPoints, details };
}

export function calculateLeaderboard(
  participants: Participant[],
  standings: GroupStanding[]
): (Participant & { score: ScoreBreakdown })[] {
  return participants
    .map((p) => ({
      ...p,
      score: calculateScore(p, standings),
    }))
    .sort((a, b) => b.score.totalPoints - a.score.totalPoints);
}

export function getDefaultStandings(): GroupStanding[] {
  return WORLD_CUP_2026_GROUPS.map((g) => ({
    groupName: g.name,
    positions: {
      1: g.teams[0].name,
      2: g.teams[1].name,
      3: g.teams[2].name,
      4: g.teams[3].name,
    },
  }));
}

export function getDefaultPredictions(): Prediction[] {
  return WORLD_CUP_2026_GROUPS.map((g) => ({
    groupName: g.name,
    champion: g.teams[0].name,
    runnerUp: g.teams[1].name,
  }));
}

export function getMaxPossiblePoints(): number {
  // 12 groups, max per group = 5 (champion) + 3 (runner-up) = 8
  return 12 * (POINTS_CORRECT_CHAMPION + POINTS_CORRECT_RUNNER_UP);
}
