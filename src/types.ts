export interface Team {
  name: string;
  flag: string; // emoji flag
}

export interface Group {
  name: string; // A, B, C, ... L
  teams: Team[];
}

export interface GroupStanding {
  groupName: string;
  positions: {
    1: string; // team name in 1st
    2: string; // team name in 2nd
    3: string; // team name in 3rd
    4: string; // team name in 4th
  };
}

export interface Prediction {
  groupName: string;
  champion: string; // predicted 1st place
  runnerUp: string; // predicted 2nd place
}

export interface Participant {
  id: string;
  name: string;
  predictions: Prediction[];
}

export interface ScoreBreakdown {
  totalPoints: number;
  details: GroupScoreDetail[];
}

export interface GroupScoreDetail {
  groupName: string;
  predictedChampion: string;
  predictedRunnerUp: string;
  actualChampion: string;
  actualRunnerUp: string;
  championPoints: number;
  runnerUpPoints: number;
  advancementBonus: number;
  groupTotal: number;
  championReason: string;
  runnerUpReason: string;
  advancementReason: string;
}
