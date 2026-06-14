import React, { useRef, useEffect, useState } from 'react';
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
      style={{ marginBottom: 20, overflow: 'visible' }}
      bodyStyle={{ overflow: 'visible' }}
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
        gridTemplateColumns: '1fr',
        gap: 12,
        overflow: 'visible',
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
  const scrollRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const [thumbStyle, setThumbStyle] = useState<React.CSSProperties>({ left: 0, width: '100%' });
  const [showBar, setShowBar] = useState(false);
  const isDragging = useRef(false);

  const updateThumb = () => {
    const el = scrollRef.current;
    if (!el) return;
    const maxScroll = el.scrollWidth - el.clientWidth;
    const overflow = maxScroll > 0;
    setShowBar(overflow);
    if (!overflow) return;
    const ratio = el.clientWidth / el.scrollWidth;
    const thumbW = Math.max(25, ratio * 100);
    const scrollRatio = el.scrollLeft / maxScroll;
    const left = scrollRatio * (100 - thumbW);
    setThumbStyle({
      position: 'absolute',
      top: 4,
      height: 20,
      width: `${thumbW}%`,
      left: `${left}%`,
      background: 'var(--semi-color-fill-2)',
      borderRadius: 6,
      userSelect: 'none',
      touchAction: 'none',
    });
  };

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener('scroll', updateThumb, { passive: true });
    const observer = new ResizeObserver(updateThumb);
    observer.observe(el);
    updateThumb();
    return () => {
      el.removeEventListener('scroll', updateThumb);
      observer.disconnect();
    };
  }, []);

  const scrollToPosition = (clientX: number) => {
    const el = scrollRef.current;
    const track = trackRef.current;
    if (!el || !track) return;
    const rect = track.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    el.scrollLeft = ratio * (el.scrollWidth - el.clientWidth);
  };

  const handlePointerDown = (e: React.PointerEvent) => {
    e.preventDefault();
    isDragging.current = true;
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    // Jump to where the user tapped
    scrollToPosition(e.clientX);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging.current) return;
    e.preventDefault();
    scrollToPosition(e.clientX);
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    isDragging.current = false;
  };

  const teams: TeamStats[] = standing.teams && standing.teams.length > 0
    ? standing.teams
    : [1, 2, 3, 4].map((pos) => ({
        name: standing.positions[pos as keyof GroupStanding['positions']],
        position: pos,
        mp: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, gd: 0, pts: 0,
      }));

  const dataSource = teams.map((t) => ({ ...t, key: t.name }));
  const needsScroll = scrollRef.current ? scrollRef.current.scrollWidth > scrollRef.current.clientWidth : false;

  return (
    <Card
      title={
        <Text strong style={{ fontSize: 14 }}>
          Group {standing.groupName}
        </Text>
      }
      style={{ marginBottom: 0, minWidth: 0, overflow: 'visible' }}
      bodyStyle={{ padding: 0, overflow: 'visible' }}
    >
      <div
        ref={scrollRef}
        style={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}
        className="group-table-scroll"
      >
        <Table
          columns={getFullColumns(isPlayed)}
          dataSource={dataSource}
          rowKey="key"
          pagination={false}
          size="small"
          style={{ fontSize: 13, minWidth: 460 }}
        />
      </div>
      {showBar && (
        <div
          ref={trackRef}
          style={{
            position: 'relative',
            height: 28,
            margin: '2px 8px 6px',
            background: 'var(--semi-color-fill-0)',
            borderRadius: 8,
            touchAction: 'none',
            userSelect: 'none',
          }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
        >
          <div style={thumbStyle} />
        </div>
      )}
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
