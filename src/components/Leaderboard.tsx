import React, { useState, useCallback } from 'react';
import { Table, Tag, Typography, Card } from '@douyinfe/semi-ui';
import { Participant, ScoreBreakdown } from '../types';
import { WORLD_CUP_2026_GROUPS } from '../data/groups';
import { teamZh } from '../data/translations';
import { ScrollableTable } from './ScrollableTable';

const { Text } = Typography;

interface LeaderboardProps {
  leaderboard: (Participant & { score: ScoreBreakdown })[];
}

function getPositionDisplay(position: number) {
  switch (position) {
    case 1:
      return <Tag color="orange" size="large">🏆 1st</Tag>;
    case 2:
      return <Tag color="light-blue" size="large">🥈 2nd</Tag>;
    case 3:
      return <Tag color="violet" size="large">🥉 3rd</Tag>;
    default:
      return <Tag size="large">#{position}</Tag>;
  }
}

function findTeam(name: string) {
  for (const group of WORLD_CUP_2026_GROUPS) {
    const team = group.teams.find((t) => t.name === name);
    if (team) return team;
  }
  return null;
}

function TeamName({ name }: { name: string }) {
  const team = findTeam(name);
  const zh = teamZh(name);
  if (!team) return <span>{name}</span>;
  return (
    <span>
      {team.flag} {name}
      {zh !== name && (
        <span style={{ fontSize: 11, color: 'var(--semi-color-tertiary)', marginLeft: 4 }}>{zh}</span>
      )}
    </span>
  );
}

function ScoreBreakdownTable({ score }: { score: ScoreBreakdown }) {
  const columns = [
    {
      title: 'Group',
      dataIndex: 'groupName',
      width: 70,
      render: (name: string) => <Text strong>Group {name}</Text>,
    },
    {
      title: 'Predicted 🥇',
      dataIndex: 'predictedChampion',
      width: 150,
      render: (name: string) => <TeamName name={name} />,
    },
    {
      title: 'Predicted 🥈',
      dataIndex: 'predictedRunnerUp',
      width: 150,
      render: (name: string) => <TeamName name={name} />,
    },
    {
      title: 'Actual 🥇',
      dataIndex: 'actualChampion',
      width: 150,
      render: (name: string) => <TeamName name={name} />,
    },
    {
      title: 'Actual 🥈',
      dataIndex: 'actualRunnerUp',
      width: 150,
      render: (name: string) => <TeamName name={name} />,
    },
    {
      title: '🥇 Pts',
      dataIndex: 'championPoints',
      width: 70,
      render: (pts: number) => <Tag color={pts === 5 ? 'green' : undefined}>{pts}</Tag>,
    },
    {
      title: '🥈 Pts',
      dataIndex: 'runnerUpPoints',
      width: 70,
      render: (pts: number) => <Tag color={pts === 3 ? 'blue' : undefined}>{pts}</Tag>,
    },
    {
      title: 'Bonus',
      dataIndex: 'advancementBonus',
      width: 60,
      render: (pts: number) => <Tag color={pts > 0 ? 'cyan' : undefined}>{pts}</Tag>,
    },
    {
      title: 'Total',
      dataIndex: 'groupTotal',
      width: 60,
      render: (pts: number) => (
        <Text strong style={{
          color: pts >= 5 ? 'var(--semi-color-success)' :
                 pts > 0 ? 'var(--semi-color-primary)' :
                 'var(--semi-color-danger)',
        }}>
          {pts}
        </Text>
      ),
    },
  ];

  return (
    <div style={{ padding: '8px 0' }}>
      <ScrollableTable minWidth={700}>
        <Table
          columns={columns}
          dataSource={score.details}
          rowKey="groupName"
          pagination={false}
          size="small"
        />
      </ScrollableTable>
    </div>
  );
}

const COLLAPSE_MS = 200;

export function Leaderboard({ leaderboard }: LeaderboardProps) {
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [collapsingKeys, setCollapsingKeys] = useState<Set<string>>(new Set());

  const handleExpand = useCallback((expanded: boolean | undefined, record: (Participant & { score: ScoreBreakdown }) | undefined) => {
    if (!record) return;
    if (expanded) {
      setExpandedKeys((prev) => [...prev, record.id]);
    } else {
      setCollapsingKeys((prev) => new Set([...prev, record.id]));
      setTimeout(() => {
        setExpandedKeys((prev) => prev.filter((k) => k !== record.id));
        setCollapsingKeys((prev) => {
          const next = new Set(prev);
          next.delete(record.id);
          return next;
        });
      }, COLLAPSE_MS);
    }
  }, []);

  const columns = [
    {
      title: 'Rank',
      width: 70,
      render: (_: unknown, __: unknown, index: number) => getPositionDisplay(index + 1),
    },
    {
      title: 'Participant',
      dataIndex: 'name',
      width: 160,
      render: (name: string) => <Text strong style={{ fontSize: 15 }}>{name}</Text>,
    },
    {
      title: 'Total Points',
      dataIndex: 'score',
      width: 120,
      render: (score: ScoreBreakdown) => (
        <Text strong style={{ fontSize: 20, color: 'var(--semi-color-primary)' }}>
          {score.totalPoints}
        </Text>
      ),
    },
    {
      title: 'Perfect Champions (5pts)',
      width: 140,
      render: (_: unknown, record: Participant & { score: ScoreBreakdown }) => {
        const count = record.score.details.filter((d) => d.championPoints === 5).length;
        return <Tag color="green">{count}/12</Tag>;
      },
    },
    {
      title: 'Perfect Runner-ups (3pts)',
      width: 140,
      render: (_: unknown, record: Participant & { score: ScoreBreakdown }) => {
        const count = record.score.details.filter((d) => d.runnerUpPoints === 3).length;
        return <Tag color="blue">{count}/12</Tag>;
      },
    },
    {
      title: 'Advancement Bonuses (1pts)',
      width: 140,
      render: (_: unknown, record: Participant & { score: ScoreBreakdown }) => {
        const total = record.score.details.reduce((sum, d) => sum + d.advancementBonus, 0);
        return <Tag color="cyan">+{total}</Tag>;
      },
    },
  ];

  return (
    <Card title="🏆 Leaderboard 排行榜" style={{ marginBottom: 20 }}>
      <ScrollableTable minWidth={600}>
        <Table
          columns={columns}
          dataSource={leaderboard}
          rowKey="id"
          pagination={false}
          size="small"
          empty={<Text>No participants yet</Text>}
          expandedRowKeys={expandedKeys}
          onExpand={handleExpand as any}
          expandRowByClick
          expandedRowRender={(record: (Participant & { score: ScoreBreakdown }) | undefined) => {
            if (!record) return null;
            const isCollapsing = collapsingKeys.has(record.id);
            return (
              <div className={isCollapsing ? 'wc-row-collapse' : 'wc-row-expand'}>
                <ScoreBreakdownTable score={record.score} />
              </div>
            );
          }}
        />
      </ScrollableTable>
      {leaderboard.length > 0 && (
        <Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 12 }}>
          Click any row to expand the detailed score breakdown
        </Text>
      )}
    </Card>
  );
}
