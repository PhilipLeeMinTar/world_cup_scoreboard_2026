import React from 'react';
import {
  Table,
  Typography,
  Card,
  Button,
} from '@douyinfe/semi-ui';
import { IconRefresh } from '@douyinfe/semi-icons';
import { GroupStanding, TeamStats } from '../types';
import { WORLD_CUP_2026_GROUPS } from '../data/groups';

const { Text } = Typography;

interface GroupStandingsViewerProps {
  standings: GroupStanding[];
  onRefresh: () => void;
  refreshing: boolean;
  updatedAt: string;
}

export function GroupStandingsViewer({ standings, onRefresh, refreshing, updatedAt }: GroupStandingsViewerProps) {
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

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(480px, 1fr))',
        gap: 12,
      }}>
        {standings.map((standing) => (
          <GroupTable key={standing.groupName} standing={standing} />
        ))}
      </div>

      <Text type="tertiary" style={{ marginTop: 12, display: 'block', fontSize: 12 }}>
        Last synced: {formattedTime}
      </Text>
    </Card>
  );
}

function GroupTable({ standing }: { standing: GroupStanding }) {
  const teams: TeamStats[] = standing.teams && standing.teams.length > 0
    ? standing.teams
    : [1, 2, 3, 4].map((pos) => ({
        name: standing.positions[pos as keyof GroupStanding['positions']],
        position: pos,
        mp: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, gd: 0, pts: 0,
      }));

  const dataSource = teams.map((t) => ({ ...t, key: t.name }));

  return (
    <Card
      title={
        <Text strong style={{ fontSize: 14 }}>
          Group {standing.groupName}
        </Text>
      }
      style={{ marginBottom: 0 }}
      bodyStyle={{ padding: 0 }}
    >
      <Table
        columns={getFullColumns()}
        dataSource={dataSource}
        rowKey="key"
        pagination={false}
        size="small"
        style={{ fontSize: 13 }}
      />
    </Card>
  );
}

function getFullColumns() {
  return [
    {
      title: '#',
      dataIndex: 'position',
      width: 32,
      render: (pos: number) => {
        const style: React.CSSProperties = {
          fontWeight: 600,
          fontSize: 12,
        };
        if (pos === 1) style.color = 'var(--semi-color-success)';
        if (pos === 2) style.color = 'var(--semi-color-success)';
        return <span style={style}>{pos}</span>;
      },
    },
    {
      title: 'Team',
      dataIndex: 'name',
      render: (name: string) => {
        const team = findTeam(name);
        return (
          <span style={team?.name !== name ? {} : undefined}>
            {team ? `${team.flag} ${team.name}` : name}
          </span>
        );
      },
    },
    {
      title: 'MP',
      dataIndex: 'mp',
      width: 36,
      align: 'center' as const,
    },
    {
      title: 'W',
      dataIndex: 'w',
      width: 36,
      align: 'center' as const,
    },
    {
      title: 'D',
      dataIndex: 'd',
      width: 36,
      align: 'center' as const,
    },
    {
      title: 'L',
      dataIndex: 'l',
      width: 36,
      align: 'center' as const,
    },
    {
      title: 'GF',
      dataIndex: 'gf',
      width: 36,
      align: 'center' as const,
    },
    {
      title: 'GA',
      dataIndex: 'ga',
      width: 36,
      align: 'center' as const,
    },
    {
      title: 'GD',
      dataIndex: 'gd',
      width: 40,
      align: 'center' as const,
      render: (gd: number) => (
        <span style={{ fontWeight: gd > 0 ? 600 : gd < 0 ? 600 : 400, color: gd > 0 ? 'var(--semi-color-success)' : gd < 0 ? 'var(--semi-color-danger)' : 'inherit' }}>
          {gd > 0 ? `+${gd}` : gd}
        </span>
      ),
    },
    {
      title: 'Pts',
      dataIndex: 'pts',
      width: 40,
      align: 'center' as const,
      render: (pts: number) => <Text strong>{pts}</Text>,
    },
  ];
}

function findTeam(name: string) {
  for (const group of WORLD_CUP_2026_GROUPS) {
    const team = group.teams.find((t) => t.name === name);
    if (team) return team;
  }
  return null;
}
