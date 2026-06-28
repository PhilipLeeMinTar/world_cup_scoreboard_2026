import React, { useState, useCallback } from 'react';
import { Card, Table, Tag, Typography } from '@douyinfe/semi-ui';
import type { KnockoutPrediction, KnockoutStatus, KnockoutScoreBreakdown, RankedKnockoutEntry } from '../types';
import { calculateKnockoutLeaderboard } from '../utils/knockoutScoring';
import { ScrollableTable } from './ScrollableTable';

const { Text } = Typography;

const COLLAPSE_MS = 200;

interface Props {
  predictions: KnockoutPrediction[];
  status: KnockoutStatus | null;
}

function getPositionDisplay(rank: number) {
  switch (rank) {
    case 1: return <Tag color="orange" size="large">🏆 1st</Tag>;
    case 2: return <Tag color="light-blue" size="large">🥈 2nd</Tag>;
    case 3: return <Tag color="violet" size="large">🥉 3rd</Tag>;
    default: return <Tag size="large">#{rank}</Tag>;
  }
}

function RoundScoreCell({ correct, possible, pts }: { correct: number; possible: number; pts: number }) {
  if (possible === 0) return <Tag color="grey">—</Tag>;
  return (
    <Tag color={correct === possible ? 'green' : correct > 0 ? 'blue' : undefined}>
      {correct}/{possible} ({pts}pts)
    </Tag>
  );
}

function BreakdownTable({ entry, results }: { entry: RankedKnockoutEntry; results: KnockoutStatus['results'] }) {
  const rounds: Array<{ label: string; picks: string[]; actuals: string[] }> = [
    { label: 'R32 Winners', picks: [], actuals: results.r32Winners },
    { label: 'QF Teams', picks: [], actuals: results.qfTeams },
    { label: 'SF Teams', picks: [], actuals: results.sfTeams },
    { label: 'Finalists', picks: [], actuals: results.finalTeams },
  ];

  // We need the raw prediction to show picks — stored in entry via participantId lookup
  // Instead, we show the score breakdown summary per round
  const { score } = entry;
  const rows = [
    { round: 'R32 (0.5pt each)', correct: score.r32.correct, possible: score.r32.possible, points: score.r32.points },
    { round: 'QF (1pt each)', correct: score.qf.correct, possible: score.qf.possible, points: score.qf.points },
    { round: 'SF (2pt each)', correct: score.sf.correct, possible: score.sf.possible, points: score.sf.points },
    { round: 'Final (4pt each)', correct: score.final.correct, possible: score.final.possible, points: score.final.points },
    { round: 'Champion (8pts)', correct: score.champion.correct, possible: score.champion.possible, points: score.champion.points },
  ];

  const columns = [
    { title: 'Round', dataIndex: 'round', width: 160, render: (v: string) => <Text strong>{v}</Text> },
    { title: 'Correct', dataIndex: 'correct', width: 80, render: (v: number, r: any) => <Tag color={v === r.possible && r.possible > 0 ? 'green' : v > 0 ? 'blue' : undefined}>{v}</Tag> },
    { title: 'Results In', dataIndex: 'possible', width: 90, render: (v: number) => <Text>{v}</Text> },
    { title: 'Points', dataIndex: 'points', width: 80, render: (v: number) => <Text strong style={{ color: v > 0 ? 'var(--semi-color-success)' : undefined }}>{v}</Text> },
  ];

  return (
    <div style={{ padding: '8px 0' }}>
      <Table columns={columns} dataSource={rows} rowKey="round" pagination={false} size="small" />
    </div>
  );
}

export function KnockoutLeaderboard({ predictions, status }: Props) {
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [collapsingKeys, setCollapsingKeys] = useState<Set<string>>(new Set());

  const results = status?.results ?? { r32Winners: [], qfTeams: [], sfTeams: [], finalTeams: [], champion: '' };
  const leaderboard = calculateKnockoutLeaderboard(predictions, results);

  const handleExpand = useCallback((expanded: boolean | undefined, record: RankedKnockoutEntry | undefined) => {
    if (!record) return;
    if (expanded) {
      setExpandedKeys((prev) => [...prev, record.participantId]);
    } else {
      setCollapsingKeys((prev) => new Set([...prev, record.participantId]));
      setTimeout(() => {
        setExpandedKeys((prev) => prev.filter((k) => k !== record.participantId));
        setCollapsingKeys((prev) => {
          const next = new Set(prev);
          next.delete(record.participantId);
          return next;
        });
      }, COLLAPSE_MS);
    }
  }, []);

  const columns = [
    {
      title: 'Rank',
      width: 80,
      render: (_: unknown, record: RankedKnockoutEntry) => getPositionDisplay(record.rank),
    },
    {
      title: 'Participant',
      dataIndex: 'participantName',
      width: 160,
      render: (name: string) => <Text strong style={{ fontSize: 15 }}>{name}</Text>,
    },
    {
      title: 'R32 (max 8)',
      width: 120,
      render: (_: unknown, r: RankedKnockoutEntry) => (
        <RoundScoreCell correct={r.score.r32.correct} possible={r.score.r32.possible} pts={r.score.r32.points} />
      ),
    },
    {
      title: 'QF (max 8)',
      width: 120,
      render: (_: unknown, r: RankedKnockoutEntry) => (
        <RoundScoreCell correct={r.score.qf.correct} possible={r.score.qf.possible} pts={r.score.qf.points} />
      ),
    },
    {
      title: 'SF (max 8)',
      width: 120,
      render: (_: unknown, r: RankedKnockoutEntry) => (
        <RoundScoreCell correct={r.score.sf.correct} possible={r.score.sf.possible} pts={r.score.sf.points} />
      ),
    },
    {
      title: 'Final (max 8)',
      width: 120,
      render: (_: unknown, r: RankedKnockoutEntry) => (
        <RoundScoreCell correct={r.score.final.correct} possible={r.score.final.possible} pts={r.score.final.points} />
      ),
    },
    {
      title: 'Champion (max 8)',
      width: 130,
      render: (_: unknown, r: RankedKnockoutEntry) => {
        if (r.score.champion.possible === 0) return <Tag color="grey">—</Tag>;
        return r.score.champion.correct === 1
          ? <Tag color="green">✓ 8pts</Tag>
          : <Tag color="red">✗ 0pts</Tag>;
      },
    },
    {
      title: 'Total',
      width: 80,
      render: (_: unknown, r: RankedKnockoutEntry) => (
        <Text strong style={{ fontSize: 18, color: 'var(--semi-color-primary)' }}>
          {r.score.total}
        </Text>
      ),
    },
  ];

  return (
    <Card title="🏟️ Knockout Leaderboard 淘汰赛排行" style={{ marginBottom: 20 }}>
      {predictions.length === 0 && (
        <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
          No knockout predictions submitted yet.
        </Text>
      )}
      <ScrollableTable minWidth={820}>
        <Table
          columns={columns}
          dataSource={leaderboard}
          rowKey="participantId"
          pagination={false}
          size="small"
          expandedRowKeys={expandedKeys}
          onExpand={handleExpand as any}
          expandRowByClick
          expandedRowRender={(record: RankedKnockoutEntry | undefined) => {
            if (!record) return null;
            const isCollapsing = collapsingKeys.has(record.participantId);
            return (
              <div className={isCollapsing ? 'wc-row-collapse' : 'wc-row-expand'}>
                <BreakdownTable entry={record} results={results} />
              </div>
            );
          }}
        />
      </ScrollableTable>
      {leaderboard.length > 0 && (
        <Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 12 }}>
          Click any row to expand the score breakdown. Max 40 pts total.
        </Text>
      )}
    </Card>
  );
}
