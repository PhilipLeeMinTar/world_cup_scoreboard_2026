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
import { teamZh } from '../data/translations';

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
      title="⚽ Group Standings 小组积分榜 — Live"
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
        gridTemplateColumns: 'repeat(auto-fill, minmax(min(480px, 100%), 1fr))',
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
  const isPlayed = standing.teams ? standing.teams.some((t) => t.mp > 0) : false;

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
      style={{ marginBottom: 0, minWidth: 0 }}
      bodyStyle={{ padding: 0, minWidth: 420 }}
    >
      <div style={{ overflowX: 'auto' }}>
      <Table
        columns={getFullColumns(isPlayed)}
        dataSource={dataSource}
        rowKey="key"
        pagination={false}
        size="small"
        style={{ fontSize: 13 }}
      />
      </div>
    </Card>
  );
}

function getFullColumns(isPlayed: boolean) {
  const dashIfUnplayed = (val: number) => isPlayed ? val : '–';

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
        const display = team ? `${team.flag} ${team.name}` : name;
        const zh = teamZh(name);
        return (
          <span>
            {display}
            <span style={{ fontSize: 11, color: 'var(--semi-color-tertiary)', marginLeft: 4 }}>
              {zh !== name ? zh : ''}
            </span>
          </span>
        );
      },
    },
    {
      title: 'MP',
      dataIndex: 'mp',
      width: 36,
      align: 'center' as const,
      render: (val: number) => dashIfUnplayed(val),
    },
    {
      title: 'W',
      dataIndex: 'w',
      width: 36,
      align: 'center' as const,
      render: (val: number) => dashIfUnplayed(val),
    },
    {
      title: 'D',
      dataIndex: 'd',
      width: 36,
      align: 'center' as const,
      render: (val: number) => dashIfUnplayed(val),
    },
    {
      title: 'L',
      dataIndex: 'l',
      width: 36,
      align: 'center' as const,
      render: (val: number) => dashIfUnplayed(val),
    },
    {
      title: 'GF',
      dataIndex: 'gf',
      width: 36,
      align: 'center' as const,
      render: (val: number) => dashIfUnplayed(val),
    },
    {
      title: 'GA',
      dataIndex: 'ga',
      width: 36,
      align: 'center' as const,
      render: (val: number) => dashIfUnplayed(val),
    },
    {
      title: 'GD',
      dataIndex: 'gd',
      width: 40,
      align: 'center' as const,
      render: (gd: number) => {
        if (!isPlayed) return '–';
        return (
          <span style={{ fontWeight: gd > 0 ? 600 : gd < 0 ? 600 : 400, color: gd > 0 ? 'var(--semi-color-success)' : gd < 0 ? 'var(--semi-color-danger)' : 'inherit' }}>
            {gd > 0 ? `+${gd}` : gd}
          </span>
        );
      },
    },
    {
      title: 'Pts',
      dataIndex: 'pts',
      width: 40,
      align: 'center' as const,
      render: (pts: number) => isPlayed ? <Text strong>{pts}</Text> : '–',
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
