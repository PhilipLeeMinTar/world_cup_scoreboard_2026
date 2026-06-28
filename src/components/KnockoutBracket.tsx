import React, { useState } from 'react';
import { Select, Tag, Typography } from '@douyinfe/semi-ui';
import type { KnockoutPrediction, KnockoutStatus } from '../types';
import {
  R16_FROM_R32,
  QF_FROM_R16,
  SF_FROM_QF,
  R32_IN_VISUAL_ORDER,
  R16_IN_VISUAL_ORDER,
  r32PairsFromTeams,
  matchWinners,
} from '../data/bracketStructure';
import { getTeamInfo } from '../data/teamInfo';

const { Text } = Typography;

// ─── Layout constants ────────────────────────────────────────────────────────

const SLOT_H   = 100;  // height of one R32 slot (gap between match cards)
const CARD_W   = 168;  // match card width
const CONN_W   = 20;   // connector arm length
const COL_GAP  = 40;   // gap between round columns
const TOTAL_H  = 16 * SLOT_H;

// ─── Dark theme tokens ────────────────────────────────────────────────────────

const T = {
  bg:          'linear-gradient(160deg, #1a2f4e 0%, #1e3a60 45%, #152b48 100%)',
  cardBg:      'rgba(255,255,255,0.08)',
  cardBorder:  'rgba(255,255,255,0.18)',
  rowDivider:  'rgba(255,255,255,0.10)',
  connLine:    'rgba(255,255,255,0.25)',
  textPrimary: 'rgba(255,255,255,0.96)',
  textMuted:   'rgba(255,255,255,0.42)',
  textSecondary: 'rgba(255,255,255,0.75)',
  roundLabel:  '#fbbf24',  // amber
  pending:     { bg: 'rgba(59,130,246,0.18)', text: '#93c5fd', border: 'rgba(59,130,246,0.4)' },
  correct:     { bg: 'rgba(34,197,94,0.18)',  text: '#86efac', border: 'rgba(34,197,94,0.4)' },
  wrong:       { bg: 'rgba(239,68,68,0.18)',  text: '#fca5a5', border: 'rgba(239,68,68,0.4)' },
  champion:    { bg: 'rgba(251,191,36,0.15)', text: '#fcd34d', border: 'rgba(251,191,36,0.5)' },
};

// ─── Data types ───────────────────────────────────────────────────────────────

type MatchInfo = {
  team1: string | null;
  team2: string | null;
  winner: string | null;
  resultWinner?: string | null;
};

type BracketData = {
  r32: MatchInfo[];
  r16: MatchInfo[];
  qf:  MatchInfo[];
  sf:  MatchInfo[];
  final: MatchInfo;
  champion: string | null;
};

// ─── Build bracket data ────────────────────────────────────────────────────────

function buildResultsBracket(teams: string[], results: KnockoutStatus['results']): BracketData {
  const r32Pairs = r32PairsFromTeams(teams);
  const r32w = matchWinners(r32Pairs, results.r32Winners);

  const r16: MatchInfo[] = R16_FROM_R32.map(([a, b]) => {
    const t1 = r32w[a], t2 = r32w[b];
    const w = t1 && results.qfTeams.includes(t1) ? t1 : t2 && results.qfTeams.includes(t2) ? t2 : null;
    return { team1: t1, team2: t2, winner: w };
  });
  const r16w = R16_FROM_R32.map((_, j) => r16[j].winner);

  const qf: MatchInfo[] = QF_FROM_R16.map(([a, b]) => {
    const t1 = r16w[a], t2 = r16w[b];
    const w = t1 && results.sfTeams.includes(t1) ? t1 : t2 && results.sfTeams.includes(t2) ? t2 : null;
    return { team1: t1, team2: t2, winner: w };
  });
  const qfw = QF_FROM_R16.map((_, k) => qf[k].winner);

  const sf: MatchInfo[] = SF_FROM_QF.map(([a, b]) => {
    const t1 = qfw[a], t2 = qfw[b];
    const w = t1 && results.finalTeams.includes(t1) ? t1 : t2 && results.finalTeams.includes(t2) ? t2 : null;
    return { team1: t1, team2: t2, winner: w };
  });
  const sfw = SF_FROM_QF.map((_, l) => sf[l].winner);
  const champion = results.champion || null;

  return {
    r32: r32Pairs.map(([t1, t2], i) => ({ team1: t1, team2: t2, winner: r32w[i] })),
    r16, qf, sf,
    final: { team1: sfw[0], team2: sfw[1], winner: champion },
    champion,
  };
}

function buildPredictionsBracket(teams: string[], pred: KnockoutPrediction, results: KnockoutStatus['results'] | null): BracketData {
  const r32Pairs = r32PairsFromTeams(teams);
  const r32w = matchWinners(r32Pairs, pred.r32Picks);
  const rr32w = results ? matchWinners(r32Pairs, results.r32Winners) : Array(16).fill(null);

  const r16: MatchInfo[] = R16_FROM_R32.map(([a, b]) => {
    const t1 = r32w[a], t2 = r32w[b];
    const w = t1 && pred.qfPicks.includes(t1) ? t1 : t2 && pred.qfPicks.includes(t2) ? t2 : null;
    const rw = results
      ? (t1 && results.qfTeams.includes(t1) ? t1 : t2 && results.qfTeams.includes(t2) ? t2 : null)
      : null;
    return { team1: t1, team2: t2, winner: w, resultWinner: rw };
  });
  const r16w = R16_FROM_R32.map((_, j) => r16[j].winner);

  const qf: MatchInfo[] = QF_FROM_R16.map(([a, b]) => {
    const t1 = r16w[a], t2 = r16w[b];
    const w = t1 && pred.sfPicks.includes(t1) ? t1 : t2 && pred.sfPicks.includes(t2) ? t2 : null;
    const rw = results
      ? (t1 && results.sfTeams.includes(t1) ? t1 : t2 && results.sfTeams.includes(t2) ? t2 : null)
      : null;
    return { team1: t1, team2: t2, winner: w, resultWinner: rw };
  });
  const qfw = QF_FROM_R16.map((_, k) => qf[k].winner);

  const sf: MatchInfo[] = SF_FROM_QF.map(([a, b]) => {
    const t1 = qfw[a], t2 = qfw[b];
    const w = t1 && pred.finalPicks.includes(t1) ? t1 : t2 && pred.finalPicks.includes(t2) ? t2 : null;
    const rw = results
      ? (t1 && results.finalTeams.includes(t1) ? t1 : t2 && results.finalTeams.includes(t2) ? t2 : null)
      : null;
    return { team1: t1, team2: t2, winner: w, resultWinner: rw };
  });
  const sfw = SF_FROM_QF.map((_, l) => sf[l].winner);
  const champion = pred.championPick || null;
  const resultChampion = results?.champion || null;

  return {
    r32: r32Pairs.map(([t1, t2], i) => ({
      team1: t1, team2: t2, winner: r32w[i], resultWinner: rr32w[i] ?? null,
    })),
    r16, qf, sf,
    final: { team1: sfw[0], team2: sfw[1], winner: champion, resultWinner: resultChampion },
    champion,
  };
}

// ─── Team Row ─────────────────────────────────────────────────────────────────

function teamRowColors(
  team: string | null,
  winner: string | null,
  resultWinner: string | null | undefined,
  isPrediction: boolean,
): { bg: string; text: string; border?: string; strikethrough?: boolean } {
  if (!team) return { bg: 'transparent', text: T.textMuted };

  const isPicked = !!team && team === winner;
  const isElim   = !!winner && !isPicked;

  if (isElim) return { bg: 'transparent', text: T.textMuted, strikethrough: true };

  if (!isPrediction) {
    // Results view
    if (isPicked) return { bg: T.correct.bg, text: T.correct.text, border: T.correct.border };
    return { bg: 'transparent', text: T.textSecondary };
  }

  // Predictions view
  if (isPicked) {
    if (!resultWinner) {
      return { bg: T.pending.bg, text: T.pending.text, border: T.pending.border };
    }
    return team === resultWinner
      ? { bg: T.correct.bg, text: T.correct.text, border: T.correct.border }
      : { bg: T.wrong.bg,   text: T.wrong.text,   border: T.wrong.border };
  }
  return { bg: 'transparent', text: T.textSecondary };
}

function TeamRow({
  team, isTop, winner, resultWinner, isPrediction,
}: {
  team: string | null;
  isTop: boolean;
  winner: string | null;
  resultWinner: string | null | undefined;
  isPrediction: boolean;
}) {
  const info = team ? getTeamInfo(team) : null;
  const colors = teamRowColors(team, winner, resultWinner, isPrediction);

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      padding: '6px 10px',
      borderBottom: isTop ? `1px solid ${T.rowDivider}` : undefined,
      backgroundColor: colors.bg,
      borderLeft: colors.border ? `2px solid ${colors.border}` : '2px solid transparent',
      minHeight: 36,
      transition: 'background-color 0.2s',
    }}>
      <span style={{ fontSize: team ? 18 : 14, lineHeight: 1, flexShrink: 0, opacity: team ? 1 : 0.3 }}>
        {team ? info!.flag : '—'}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          color: colors.text,
          fontWeight: team && team === winner ? 700 : 500,
          fontSize: 13,
          textDecoration: colors.strikethrough ? 'line-through' : undefined,
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          lineHeight: 1.2,
        }}>
          {team ?? 'TBD'}
          {team && team === winner && <span style={{ marginLeft: 4, opacity: 0.8 }}>✓</span>}
        </div>
        {team && (
          <div style={{
            color: colors.strikethrough ? T.textMuted : 'rgba(255,255,255,0.68)',
            fontSize: 10,
            lineHeight: 1.2,
          }}>
            {info!.zh}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Match Card ───────────────────────────────────────────────────────────────

function MatchCard({ info, isPrediction }: { info: MatchInfo; isPrediction: boolean }) {
  return (
    <div style={{
      width: CARD_W,
      backgroundColor: T.cardBg,
      border: `1px solid ${T.cardBorder}`,
      borderRadius: 8,
      overflow: 'hidden',
      backdropFilter: 'blur(4px)',
      boxShadow: '0 2px 12px rgba(0,0,0,0.4)',
    }}>
      <TeamRow
        team={info.team1}
        isTop
        winner={info.winner}
        resultWinner={info.resultWinner}
        isPrediction={isPrediction}
      />
      <TeamRow
        team={info.team2}
        isTop={false}
        winner={info.winner}
        resultWinner={info.resultWinner}
        isPrediction={isPrediction}
      />
    </div>
  );
}

// ─── Connectors ───────────────────────────────────────────────────────────────

function RightConnectorTop() {
  return (
    <div style={{
      position: 'absolute',
      top: '50%',
      right: -CONN_W,
      bottom: 0,
      width: CONN_W,
      borderRight: `1.5px solid ${T.connLine}`,
      borderBottom: `1.5px solid ${T.connLine}`,
      borderBottomRightRadius: 4,
      pointerEvents: 'none',
    }} />
  );
}

function RightConnectorBottom() {
  return (
    <div style={{
      position: 'absolute',
      top: 0,
      right: -CONN_W,
      bottom: '50%',
      width: CONN_W,
      borderRight: `1.5px solid ${T.connLine}`,
      borderTop: `1.5px solid ${T.connLine}`,
      borderTopRightRadius: 4,
      pointerEvents: 'none',
    }} />
  );
}

function LeftConnector() {
  return (
    <div style={{
      position: 'absolute',
      top: '50%',
      left: -CONN_W,
      width: CONN_W,
      height: 1.5,
      backgroundColor: T.connLine,
      marginTop: -0.75,
      pointerEvents: 'none',
    }} />
  );
}

// ─── Match Slot ───────────────────────────────────────────────────────────────

function MatchSlot({
  top, height, isTop, isBottom, showLeftConn, showRightConn, children,
}: {
  top: number; height: number;
  isTop: boolean; isBottom: boolean;
  showLeftConn: boolean; showRightConn: boolean;
  children: React.ReactNode;
}) {
  return (
    <div style={{
      position: 'absolute',
      top, height,
      left: 0, width: CARD_W,
      display: 'flex',
      alignItems: 'center',
      overflow: 'visible',
    }}>
      {showLeftConn && <LeftConnector />}
      {children}
      {showRightConn && isTop    && <RightConnectorTop />}
      {showRightConn && isBottom && <RightConnectorBottom />}
    </div>
  );
}

// ─── Round Column ─────────────────────────────────────────────────────────────

const ROUND_LABELS: Record<string, string> = {
  R32: 'Round of 32',
  R16: 'Round of 16',
  QF:  'Quarter-Final',
  SF:  'Semi-Final',
  Final: 'Final',
};

interface RoundDef {
  key: string;
  matches: MatchInfo[];
  visualOrder: number[];
  slotsPerMatch: number;
  showLeftConn: boolean;
  showRightConn: boolean;
}

function RoundColumn({ round, isPrediction }: { round: RoundDef; isPrediction: boolean }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      {/* Label */}
      <div style={{
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: 1.5,
        color: T.roundLabel,
        textTransform: 'uppercase',
        marginBottom: 10,
        textAlign: 'center',
        whiteSpace: 'nowrap',
      }}>
        {ROUND_LABELS[round.key] ?? round.key}
      </div>
      {/* Matches */}
      <div style={{ position: 'relative', width: CARD_W, height: TOTAL_H, overflow: 'visible' }}>
        {round.visualOrder.map((matchIdx, visualPos) => {
          const slotTop    = visualPos * round.slotsPerMatch * SLOT_H;
          const slotHeight = round.slotsPerMatch * SLOT_H;
          const isTop    = visualPos % 2 === 0;
          const isBottom = visualPos % 2 === 1;
          return (
            <MatchSlot
              key={matchIdx}
              top={slotTop}
              height={slotHeight}
              isTop={isTop}
              isBottom={isBottom}
              showLeftConn={round.showLeftConn}
              showRightConn={round.showRightConn}
            >
              <MatchCard info={round.matches[matchIdx]} isPrediction={isPrediction} />
            </MatchSlot>
          );
        })}
      </div>
    </div>
  );
}

// ─── Champion Display ─────────────────────────────────────────────────────────

function ChampionDisplay({ team }: { team: string | null }) {
  if (!team) return null;
  const info = getTeamInfo(team);
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      paddingLeft: 16,
      height: TOTAL_H + 32,
      marginTop: 32, // offset for round label
    }}>
      <div style={{
        background: T.champion.bg,
        border: `1.5px solid ${T.champion.border}`,
        borderRadius: 12,
        padding: '16px 20px',
        textAlign: 'center',
        backdropFilter: 'blur(4px)',
        boxShadow: '0 0 24px rgba(251,191,36,0.15)',
      }}>
        <div style={{ fontSize: 28, marginBottom: 6 }}>🏆</div>
        <div style={{ fontSize: 24, marginBottom: 4 }}>{info.flag}</div>
        <div style={{ color: T.champion.text, fontWeight: 700, fontSize: 13 }}>{team}</div>
        <div style={{ color: T.textMuted, fontSize: 11, marginTop: 2 }}>{info.zh}</div>
      </div>
    </div>
  );
}

// ─── Legend ────────────────────────────────────────────────────────────────────

function Legend({ isPrediction }: { isPrediction: boolean }) {
  const dot = (bg: string, border: string, label: string) => (
    <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: T.textSecondary }}>
      <span style={{
        display: 'inline-block',
        width: 10, height: 10,
        borderRadius: 3,
        backgroundColor: bg,
        border: `1.5px solid ${border}`,
      }} />
      {label}
    </span>
  );

  if (!isPrediction) {
    return (
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {dot(T.correct.bg, T.correct.border, 'Winner / Advancing')}
      </div>
    );
  }
  return (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
      {dot(T.pending.bg, T.pending.border, 'Your pick (result pending)')}
      {dot(T.correct.bg, T.correct.border, 'Correct ✓')}
      {dot(T.wrong.bg,   T.wrong.border,   'Wrong ✗')}
    </div>
  );
}

// ─── Public Component ─────────────────────────────────────────────────────────

interface Props {
  predictions: KnockoutPrediction[];
  status: KnockoutStatus | null;
}

export function KnockoutBracket({ predictions, status }: Props) {
  const [selectedParticipant, setSelectedParticipant] = useState<string>('results');

  const teams   = status?.teams ?? [];
  const results = status?.results ?? { r32Winners: [], qfTeams: [], sfTeams: [], finalTeams: [], champion: '' };
  const hasTeams = teams.length === 32;

  const isPrediction   = selectedParticipant !== 'results';
  const predParticipant = predictions.find((p) => p.participantId === selectedParticipant);

  const data: BracketData | null = !hasTeams ? null
    : isPrediction && predParticipant
      ? buildPredictionsBracket(teams, predParticipant, results)
      : !isPrediction
        ? buildResultsBracket(teams, results)
        : null;

  const viewOptions = [
    { value: 'results', label: '📡 Live Results' },
    ...predictions.map((p) => ({ value: p.participantId, label: `👤 ${p.participantName}` })),
  ];

  const rounds: RoundDef[] = data ? [
    { key: 'R32',   matches: data.r32,   visualOrder: R32_IN_VISUAL_ORDER, slotsPerMatch: 1,  showLeftConn: false, showRightConn: true  },
    { key: 'R16',   matches: data.r16,   visualOrder: R16_IN_VISUAL_ORDER, slotsPerMatch: 2,  showLeftConn: true,  showRightConn: true  },
    { key: 'QF',    matches: data.qf,    visualOrder: [0, 1, 2, 3],        slotsPerMatch: 4,  showLeftConn: true,  showRightConn: true  },
    { key: 'SF',    matches: data.sf,    visualOrder: [0, 1],              slotsPerMatch: 8,  showLeftConn: true,  showRightConn: true  },
    { key: 'Final', matches: [data.final], visualOrder: [0],               slotsPerMatch: 16, showLeftConn: true,  showRightConn: false },
  ] : [];

  return (
    <div style={{
      background: T.bg,
      borderRadius: 16,
      padding: '24px 28px',
      marginBottom: 20,
      boxShadow: '0 8px 40px rgba(0,0,0,0.5)',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ color: T.roundLabel, fontWeight: 700, fontSize: 11, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4 }}>
            FIFA World Cup 2026
          </div>
          <div style={{ color: T.textPrimary, fontWeight: 700, fontSize: 20 }}>
            🗺️ Knockout Bracket &nbsp;
            <span style={{ color: T.textMuted, fontSize: 14, fontWeight: 400 }}>对阵图</span>
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ color: T.textSecondary, fontSize: 12 }}>View:</span>
            <Select
              value={selectedParticipant}
              onChange={(v) => setSelectedParticipant(v as string)}
              style={{ width: 220, '--semi-color-text-0': T.textPrimary } as React.CSSProperties}
              optionList={viewOptions}
            />
          </div>
          <Legend isPrediction={isPrediction} />
        </div>
      </div>

      {/* Tip */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        marginBottom: 20,
        padding: '10px 14px',
        background: 'rgba(251,191,36,0.08)',
        border: '1px solid rgba(251,191,36,0.2)',
        borderRadius: 8,
        fontSize: 12,
        color: 'rgba(251,191,36,0.85)',
      }}>
        <span style={{ fontSize: 15, flexShrink: 0 }}>💡</span>
        <span>
          Use the <strong style={{ color: '#fbbf24' }}>View</strong> dropdown to switch between the live bracket and each participant's predictions — see how everyone's picks hold up as the tournament progresses.
        </span>
      </div>

      {/* No data state */}
      {!hasTeams && (
        <div style={{ color: T.textSecondary, textAlign: 'center', padding: '40px 0' }}>
          R32 fixtures will appear here once the knockout stage begins.
        </div>
      )}

      {hasTeams && !data && (
        <div style={{ color: T.textSecondary, textAlign: 'center', padding: '40px 0' }}>
          No predictions found for this participant.
        </div>
      )}

      {/* Bracket */}
      {data && (
        <div style={{ overflowX: 'auto', overflowY: 'visible', paddingBottom: 16 }}>
          <div style={{
            display: 'flex',
            gap: COL_GAP,
            minWidth: rounds.length * (CARD_W + COL_GAP) + 140,
            overflow: 'visible',
          }}>
            {rounds.map((round) => (
              <RoundColumn key={round.key} round={round} isPrediction={isPrediction} />
            ))}
            <ChampionDisplay team={data.champion} />
          </div>
        </div>
      )}
    </div>
  );
}
