import React, { useState } from 'react';
import { Card, Button, Tag, Typography, Notification } from '@douyinfe/semi-ui';
import type { KnockoutStatus } from '../types';
import { toggleKnockoutLock, refreshKnockoutResults } from '../api/client';

const { Text } = Typography;

interface Props {
  status: KnockoutStatus | null;
  onStatusChange: () => void;
}

function formatTime(iso: string): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function KnockoutAdmin({ status, onStatusChange }: Props) {
  const [togglingLock, setTogglingLock] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const locked = status?.locked ?? false;
  const results = status?.results;
  const lastUpdated = status?.lastUpdated;

  async function handleToggleLock() {
    setTogglingLock(true);
    try {
      const res = await toggleKnockoutLock();
      onStatusChange();
      Notification.info({
        title: res.locked ? 'Predictions Locked' : 'Predictions Unlocked',
        content: res.locked
          ? 'Participants can no longer edit their picks.'
          : 'Participants can now edit their picks.',
      });
    } catch (err) {
      Notification.error({ title: 'Error', content: err instanceof Error ? err.message : 'Failed to toggle lock' });
    } finally {
      setTogglingLock(false);
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await refreshKnockoutResults();
      onStatusChange();
      Notification.success({ title: 'Refreshed', content: 'Knockout results fetched from live API' });
    } catch (err) {
      Notification.error({ title: 'Refresh failed', content: err instanceof Error ? err.message : 'API error' });
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <Card title="⚙️ Admin — Knockout Stage" style={{ marginBottom: 20 }}>
      {/* Live data status */}
      <div style={{ marginBottom: 20, display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'center' }}>
        <div>
          <Text strong style={{ marginRight: 8 }}>Live Data:</Text>
          <Tag color="cyan">{status?.teams.length ?? 0} R32 teams loaded</Tag>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Tag color={results?.r32Winners.length ? 'green' : 'grey'}>
            R32: {results?.r32Winners.length ?? 0}/16 done
          </Tag>
          <Tag color={results?.qfTeams.length ? 'green' : 'grey'}>
            QF: {results?.qfTeams.length ?? 0}/8
          </Tag>
          <Tag color={results?.sfTeams.length ? 'green' : 'grey'}>
            SF: {results?.sfTeams.length ?? 0}/4
          </Tag>
          <Tag color={results?.finalTeams.length ? 'green' : 'grey'}>
            Final: {results?.finalTeams.length ?? 0}/2
          </Tag>
          <Tag color={results?.champion ? 'orange' : 'grey'}>
            Champion: {results?.champion || 'TBD'}
          </Tag>
        </div>
        {lastUpdated && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            Last fetched: {formatTime(lastUpdated)}
          </Text>
        )}
        <Button loading={refreshing} onClick={handleRefresh} size="small">
          🔄 Refresh from API
        </Button>
      </div>

      {/* Lock / Unlock */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Text strong>Predictions:</Text>
        {locked
          ? <Tag color="red" size="large">Locked 🔒</Tag>
          : <Tag color="green" size="large">Open 🔓</Tag>
        }
        <Button loading={togglingLock} onClick={handleToggleLock}>
          {locked ? 'Unlock Predictions' : 'Lock Predictions'}
        </Button>
      </div>
    </Card>
  );
}
