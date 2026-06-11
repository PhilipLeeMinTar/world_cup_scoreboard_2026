import React from 'react';
import {
  Table,
  Tag,
  Typography,
  Card,
  Button,
} from '@douyinfe/semi-ui';
import { IconRefresh } from '@douyinfe/semi-icons';
import { GroupStanding } from '../types';
import { WORLD_CUP_2026_GROUPS } from '../data/groups';

const { Text } = Typography;

interface GroupStandingsViewerProps {
  standings: GroupStanding[];
  onRefresh: () => void;
  refreshing: boolean;
  updatedAt: string;
}

export function GroupStandingsViewer({ standings, onRefresh, refreshing, updatedAt }: GroupStandingsViewerProps) {
  const columns = [
    {
      title: 'Group',
      dataIndex: 'groupName',
      width: 80,
      render: (name: string) => (
        <Text strong style={{ fontSize: 16 }}>
          Group {name}
        </Text>
      ),
    },
    {
      title: '🥇 1st',
      dataIndex: 'positions',
      key: 'pos1',
      width: 180,
      render: (positions: GroupStanding['positions']) => {
        const team = findTeam(positions[1]);
        return team ? <span>{team.flag} {team.name}</span> : <span>{positions[1]}</span>;
      },
    },
    {
      title: '🥈 2nd',
      dataIndex: 'positions',
      key: 'pos2',
      width: 180,
      render: (positions: GroupStanding['positions']) => {
        const team = findTeam(positions[2]);
        return team ? <span>{team.flag} {team.name}</span> : <span>{positions[2]}</span>;
      },
    },
    {
      title: '3rd',
      dataIndex: 'positions',
      key: 'pos3',
      width: 180,
      render: (positions: GroupStanding['positions']) => {
        const team = findTeam(positions[3]);
        return team ? <span style={{ color: 'var(--semi-color-tertiary)' }}>{team.flag} {team.name}</span> : <span>{positions[3]}</span>;
      },
    },
    {
      title: '4th',
      dataIndex: 'positions',
      key: 'pos4',
      width: 180,
      render: (positions: GroupStanding['positions']) => {
        const team = findTeam(positions[4]);
        return team ? <span style={{ color: 'var(--semi-color-tertiary)' }}>{team.flag} {team.name}</span> : <span>{positions[4]}</span>;
      },
    },
  ];

  const formattedTime = updatedAt
    ? new Date(updatedAt).toLocaleString()
    : 'Not yet synced';

  return (
    <Card
      title="⚽ Group Standings — Live"
      style={{ marginBottom: 20 }}
      headerExtraContent={
        <Button
          icon={<IconRefresh />}
          onClick={onRefresh}
          loading={refreshing}
          theme="solid"
        >
          Refresh Scores
        </Button>
      }
    >
      <Text type="secondary" style={{ marginBottom: 12, display: 'block' }}>
        Standings are automatically synced from live match data every 2 hours.
        Click "Refresh Scores" for an immediate update.
      </Text>

      <Table
        columns={columns}
        dataSource={standings}
        rowKey="groupName"
        pagination={false}
        size="small"
      />

      <Text type="tertiary" style={{ marginTop: 12, display: 'block', fontSize: 12 }}>
        Last synced: {formattedTime}
      </Text>
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
