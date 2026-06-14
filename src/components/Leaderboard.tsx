import React from 'react';
import { Table, Tag, Typography, Card } from '@douyinfe/semi-ui';
import { Participant, ScoreBreakdown } from '../types';
import { WORLD_CUP_2026_GROUPS } from '../data/groups';
import { teamZh } from '../data/translations';

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

export function Leaderboard({ leaderboard }: LeaderboardProps) {
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
    <Card
      title="🏆 Leaderboard 排行榜"
      style={{ marginBottom: 20 }}
    >
      <Table
        columns={columns}
        dataSource={leaderboard}
        rowKey="id"
        pagination={false}
        size="small"
        empty={<Text>No participants yet</Text>}
      />
    </Card>
  );
}

interface ScoreDetailCardProps {
  participant: Participant & { score: ScoreBreakdown };
}

export function ScoreDetailCard({ participant }: ScoreDetailCardProps) {
  const columns = [
    {
      title: 'Group',
      dataIndex: 'groupName',
      width: 80,
      render: (name: string) => <Text strong>Group {name}</Text>,
    },
    {
      title: 'Predicted 🥇',
      dataIndex: 'predictedChampion',
      width: 160,
      render: (name: string) => {
        const team = findTeam(name);
        const zh = teamZh(name);
        return team
          ? <span>{team.flag} {name} <span style={{ fontSize: 11, color: 'var(--semi-color-tertiary)' }}>{zh !== name ? zh : ''}</span></span>
          : <span>{name}</span>;
      },
    },
    {
      title: 'Predicted 🥈',
      dataIndex: 'predictedRunnerUp',
      width: 160,
      render: (name: string) => {
        const team = findTeam(name);
        const zh = teamZh(name);
        return team
          ? <span>{team.flag} {name} <span style={{ fontSize: 11, color: 'var(--semi-color-tertiary)' }}>{zh !== name ? zh : ''}</span></span>
          : <span>{name}</span>;
      },
    },
    {
      title: 'Actual 🥇',
      dataIndex: 'actualChampion',
      width: 160,
      render: (name: string) => {
        const team = findTeam(name);
        const zh = teamZh(name);
        return team
          ? <span>{team.flag} {name} <span style={{ fontSize: 11, color: 'var(--semi-color-tertiary)' }}>{zh !== name ? zh : ''}</span></span>
          : <span>{name}</span>;
      },
    },
    {
      title: 'Actual 🥈',
      dataIndex: 'actualRunnerUp',
      width: 160,
      render: (name: string) => {
        const team = findTeam(name);
        const zh = teamZh(name);
        return team
          ? <span>{team.flag} {name} <span style={{ fontSize: 11, color: 'var(--semi-color-tertiary)' }}>{zh !== name ? zh : ''}</span></span>
          : <span>{name}</span>;
      },
    },
    {
      title: '🥇 Pts',
      dataIndex: 'championPoints',
      width: 70,
      render: (pts: number) => (
        <Tag color={pts === 5 ? 'green' : undefined}>{pts}</Tag>
      ),
    },
    {
      title: '🥈 Pts',
      dataIndex: 'runnerUpPoints',
      width: 70,
      render: (pts: number) => (
        <Tag color={pts === 3 ? 'blue' : undefined}>{pts}</Tag>
      ),
    },
    {
      title: 'Bonus',
      dataIndex: 'advancementBonus',
      width: 70,
      render: (pts: number) => (
        <Tag color={pts > 0 ? 'cyan' : undefined}>{pts}</Tag>
      ),
    },
    {
      title: 'Total',
      dataIndex: 'groupTotal',
      width: 70,
      render: (pts: number) => (
        <Text strong style={{
          color: pts >= 5 ? 'var(--semi-color-success)' :
                 pts > 0 ? 'var(--semi-color-primary)' :
                 'var(--semi-color-danger)'
        }}>
          {pts}
        </Text>
      ),
    },
  ];

  return (
    <Card
      title={`📊 ${participant.name} — ${participant.score.totalPoints} pts`}
      style={{ marginBottom: 20 }}
    >
      <Table
        columns={columns}
        dataSource={participant.score.details}
        rowKey="groupName"
        pagination={false}
        size="small"
      />
    </Card>
  );
}

function findTeam(name: string) {
  for (const group of WORLD_CUP_2026_GROUPS) {
    const team = group.teams.find((t) => t.name === name);
    if (team) return team;
  }
  return null;
}
