import React from 'react';
import { Card, Table, Typography, Collapse } from '@douyinfe/semi-ui';
import { Participant, ScoreBreakdown, GroupStanding } from '../types';
import { WORLD_CUP_2026_GROUPS } from '../data/groups';
import { teamZh } from '../data/translations';
import { calculateScore } from '../utils/scoring';
import { ScrollableTable } from './ScrollableTable';

const { Title, Text } = Typography;

interface AllScoresProps {
  participants: Participant[];
  standings: GroupStanding[];
  expandedParticipant: string | null;
  onExpand: (id: string | null) => void;
}

export function AllScoresView({ participants, standings, expandedParticipant, onExpand }: AllScoresProps) {
  if (participants.length === 0) {
    return null;
  }

  return (
    <Card title="📊 All Scores Breakdown 详细积分" style={{ marginBottom: 20 }}>
      <Collapse
        activeKey={expandedParticipant ? [expandedParticipant] : []}
        onChange={(activeKey: string | string[] | undefined) => {
          if (Array.isArray(activeKey) && activeKey.length > 0) {
            onExpand(activeKey[activeKey.length - 1]);
          } else {
            onExpand(null);
          }
        }}
      >
        {participants.map((participant) => {
          const score = calculateScore(participant, standings);
          return (
            <Collapse.Panel
              itemKey={participant.id}
              header={
                <span>
                  <Text strong style={{ fontSize: 15 }}>{participant.name}</Text>
                  <Tag color="blue" style={{ marginLeft: 12 }}>{score.totalPoints} pts</Tag>
                </span>
              }
            >
              <ScoreBreakdownTable score={score} />
            </Collapse.Panel>
          );
        })}
      </Collapse>
    </Card>
  );
}

function Tag({ color, children, style }: { color?: string; children: React.ReactNode; style?: React.CSSProperties }) {
  const bgColor = color === 'blue' ? '#e6f7ff' :
                  color === 'green' ? '#f6ffed' :
                  color === 'cyan' ? '#e6fffb' :
                  '#f0f0f0';
  const textColor = color === 'blue' ? '#1890ff' :
                    color === 'green' ? '#52c41a' :
                    color === 'cyan' ? '#13c2c2' :
                    '#666';
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: 4,
      fontSize: 12,
      backgroundColor: bgColor,
      color: textColor,
      ...style,
    }}>
      {children}
    </span>
  );
}

interface ScoreBreakdownTableProps {
  score: ScoreBreakdown;
}

function ScoreBreakdownTable({ score }: ScoreBreakdownTableProps) {
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
      width: 150,
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
      width: 150,
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
      width: 150,
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
      width: 60,
      render: (pts: number) => (
        <Tag color={pts > 0 ? 'cyan' : undefined}>{pts}</Tag>
      ),
    },
    {
      title: 'Total',
      dataIndex: 'groupTotal',
      width: 60,
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
    <ScrollableTable minWidth={700}>
    <Table
      columns={columns}
      dataSource={score.details}
      rowKey="groupName"
      pagination={false}
      size="small"
    />
    </ScrollableTable>
  );
}

function findTeam(name: string) {
  for (const group of WORLD_CUP_2026_GROUPS) {
    const team = group.teams.find((t) => t.name === name);
    if (team) return team;
  }
  return null;
}
