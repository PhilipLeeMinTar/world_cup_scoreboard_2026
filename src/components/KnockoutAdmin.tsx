import React, { useState } from 'react';
import { Card, Button, Tag, Typography, Notification, Popconfirm } from '@douyinfe/semi-ui';
import type { KnockoutStatus, KnockoutPrediction } from '../types';
import { toggleKnockoutLock, refreshKnockoutResults, deleteKnockoutPrediction } from '../api/client';

const { Text } = Typography;

interface Props {
  status: KnockoutStatus | null;
  predictions: KnockoutPrediction[];
  onStatusChange: () => void;
}

function formatTime(iso: string): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function KnockoutAdmin({ status, predictions, onStatusChange }: Props) {
  const [togglingLock, setTogglingLock] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

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

  async function handleDeletePrediction(participantId: string, participantName: string) {
    setDeleting(participantId);
    try {
      await deleteKnockoutPrediction(participantId);
      onStatusChange();
      Notification.success({ title: 'Deleted', content: `Removed knockout predictions for ${participantName}` });
    } catch (err) {
      Notification.error({ title: 'Delete failed', content: err instanceof Error ? err.message : 'API error' });
    } finally {
      setDeleting(null);
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
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: predictions.length > 0 ? 20 : 0 }}>
        <Text strong>Predictions:</Text>
        {locked
          ? <Tag color="red" size="large">Locked 🔒</Tag>
          : <Tag color="green" size="large">Open 🔓</Tag>
        }
        <Button loading={togglingLock} onClick={handleToggleLock}>
          {locked ? 'Unlock Predictions' : 'Lock Predictions'}
        </Button>
      </div>

      {/* Submitted predictions list with delete */}
      {predictions.length > 0 && (
        <div>
          <Text strong style={{ display: 'block', marginBottom: 10 }}>
            Submitted Predictions ({predictions.length})
          </Text>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {predictions.map((p) => (
              <div
                key={p.participantId}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '6px 10px',
                  background: 'rgba(0,0,0,0.04)',
                  border: '1px solid rgba(0,0,0,0.1)',
                  borderRadius: 6,
                }}
              >
                <Text style={{ fontSize: 13 }}>{p.participantName}</Text>
                <Text type="tertiary" style={{ fontSize: 11 }}>
                  {p.updatedAt ? formatTime(p.updatedAt) : ''}
                </Text>
                <Popconfirm
                  title="Delete predictions?"
                  content={`Remove all knockout picks for ${p.participantName}?`}
                  onConfirm={() => handleDeletePrediction(p.participantId, p.participantName)}
                  okType="danger"
                  okText="Delete"
                  cancelText="Cancel"
                >
                  <Button
                    size="small"
                    type="danger"
                    theme="light"
                    loading={deleting === p.participantId}
                    style={{ padding: '0 8px', height: 24, fontSize: 11 }}
                  >
                    Delete
                  </Button>
                </Popconfirm>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
