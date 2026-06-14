import React from 'react';
import { Typography, Spin } from '@douyinfe/semi-ui';
import type { PollStatus, AppMode } from '../api/client';

const { Text } = Typography;

interface StatusIndicatorProps {
  status: PollStatus | null;
  loading: boolean;
  onRefresh: () => void;
  mode: AppMode;
}

export function StatusIndicator({ status, loading, onRefresh, mode }: StatusIndicatorProps) {
  const lastPoll = status?.lastPollAt ? new Date(status.lastPollAt) : null;
  const isStale = lastPoll
    ? Date.now() - lastPoll.getTime() > 4 * 60 * 60 * 1000
    : !status?.lastPollAt;

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const nextPollTime = lastPoll
    ? new Date(lastPoll.getTime() + (status?.pollIntervalMinutes || 120) * 60 * 1000)
    : null;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        cursor: 'pointer',
        padding: '4px 12px',
        borderRadius: 6,
        background: 'rgba(255,255,255,0.1)',
      }}
      onClick={onRefresh}
    >
      {loading ? (
        <Spin size="small" />
      ) : (
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            backgroundColor: isStale ? '#faad14' : '#52c41a',
            display: 'inline-block',
          }}
        />
      )}
      <div style={{ textAlign: 'right' }}>
        <Text
          style={{
            color: 'rgba(255,255,255,0.5)',
            fontSize: 12,
            display: 'block',
          }}
        >
          {lastPoll
            ? `Updated ${formatTime(lastPoll)}${nextPollTime ? ` · Next ${formatTime(nextPollTime)}` : ''}`
            : loading ? 'Refreshing...' : isStale ? '⚠️ Data may be stale' : 'Not yet synced'}
        </Text>
      </div>
      <span
        style={{
          color: 'rgba(255,255,255,0.6)',
          fontSize: 14,
          display: 'inline-block',
          animation: loading ? 'spin 1s linear infinite' : 'none',
        }}
      >
        🔄
      </span>
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
