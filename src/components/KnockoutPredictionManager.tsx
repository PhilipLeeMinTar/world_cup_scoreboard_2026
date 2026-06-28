import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Tag,
  Typography,
  Notification,
  Badge,
} from '@douyinfe/semi-ui';
import type { Participant, KnockoutStatus, KnockoutPrediction } from '../types';
import {
  getKnockoutPredictions,
  saveKnockoutPrediction,
} from '../api/client';
import {
  R16_FROM_R32,
  QF_FROM_R16,
  SF_FROM_QF,
  r32PairsFromTeams,
} from '../data/bracketStructure';

const { Text } = Typography;

interface Props {
  participants: Participant[];
  status: KnockoutStatus | null;
  onStatusChange: () => void;
}

interface Draft {
  r32: (string | null)[];   // length 16 — winner of each R32 match
  r16: (string | null)[];   // length 8 — winner of each R16 match
  qf: (string | null)[];    // length 4
  sf: (string | null)[];    // length 2
  champion: string | null;
}

function emptyDraft(): Draft {
  return { r32: Array(16).fill(null), r16: Array(8).fill(null), qf: Array(4).fill(null), sf: Array(2).fill(null), champion: null };
}

/** Reconstruct match-indexed picks from a flat picks array. */
function reconstructDraft(pred: KnockoutPrediction | undefined, r32Pairs: [string, string][]): Draft {
  if (!pred) return emptyDraft();

  const r32Set = new Set(pred.r32Picks);
  const qfSet = new Set(pred.qfPicks);
  const sfSet = new Set(pred.sfPicks);
  const finalSet = new Set(pred.finalPicks);

  const r32: (string | null)[] = r32Pairs.map(([t1, t2]) =>
    r32Set.has(t1) ? t1 : r32Set.has(t2) ? t2 : null
  );

  const r16: (string | null)[] = R16_FROM_R32.map(([a, b]) => {
    const t1 = r32[a];
    const t2 = r32[b];
    if (!t1 || !t2) return null;
    return qfSet.has(t1) ? t1 : qfSet.has(t2) ? t2 : null;
  });

  const qf: (string | null)[] = QF_FROM_R16.map(([a, b]) => {
    const t1 = r16[a];
    const t2 = r16[b];
    if (!t1 || !t2) return null;
    return sfSet.has(t1) ? t1 : sfSet.has(t2) ? t2 : null;
  });

  const sf: (string | null)[] = SF_FROM_QF.map(([a, b]) => {
    const t1 = qf[a];
    const t2 = qf[b];
    if (!t1 || !t2) return null;
    return finalSet.has(t1) ? t1 : finalSet.has(t2) ? t2 : null;
  });

  const champion = pred.championPick || null;
  return { r32, r16, qf, sf, champion };
}

/** Convert indexed draft back to flat API format. */
function draftToApiPicks(draft: Draft) {
  return {
    r32Picks: draft.r32.filter((p): p is string => p !== null),
    qfPicks: draft.r16.filter((p): p is string => p !== null),
    sfPicks: draft.qf.filter((p): p is string => p !== null),
    finalPicks: draft.sf.filter((p): p is string => p !== null),
    championPick: draft.champion ?? '',
  };
}

/** Update a pick and cascade-clear downstream picks that are no longer valid. */
function setPick(
  draft: Draft,
  round: 'r32' | 'r16' | 'qf' | 'sf',
  matchIdx: number,
  team: string | null,
): Draft {
  let r32 = [...draft.r32];
  let r16 = [...draft.r16];
  let qf = [...draft.qf];
  let sf = [...draft.sf];
  let champion = draft.champion;

  if (round === 'r32') {
    const old = r32[matchIdx];
    r32[matchIdx] = team;
    const r16Idx = R16_FROM_R32.findIndex(([a, b]) => a === matchIdx || b === matchIdx);
    if (r16Idx !== -1 && r16[r16Idx] === old) {
      r16[r16Idx] = null;
      const qfIdx = QF_FROM_R16.findIndex(([a, b]) => a === r16Idx || b === r16Idx);
      if (qfIdx !== -1 && qf[qfIdx] === old) {
        qf[qfIdx] = null;
        const sfIdx = SF_FROM_QF.findIndex(([a, b]) => a === qfIdx || b === qfIdx);
        if (sfIdx !== -1 && sf[sfIdx] === old) {
          sf[sfIdx] = null;
          if (champion === old) champion = null;
        }
      }
    }
  } else if (round === 'r16') {
    const old = r16[matchIdx];
    r16[matchIdx] = team;
    const qfIdx = QF_FROM_R16.findIndex(([a, b]) => a === matchIdx || b === matchIdx);
    if (qfIdx !== -1 && qf[qfIdx] === old) {
      qf[qfIdx] = null;
      const sfIdx = SF_FROM_QF.findIndex(([a, b]) => a === qfIdx || b === qfIdx);
      if (sfIdx !== -1 && sf[sfIdx] === old) {
        sf[sfIdx] = null;
        if (champion === old) champion = null;
      }
    }
  } else if (round === 'qf') {
    const old = qf[matchIdx];
    qf[matchIdx] = team;
    const sfIdx = SF_FROM_QF.findIndex(([a, b]) => a === matchIdx || b === matchIdx);
    if (sfIdx !== -1 && sf[sfIdx] === old) {
      sf[sfIdx] = null;
      if (champion === old) champion = null;
    }
  } else {
    const old = sf[matchIdx];
    sf[matchIdx] = team;
    if (champion === old) champion = null;
  }

  return { r32, r16, qf, sf, champion };
}

interface MatchRowProps {
  matchNum: number;
  team1: string;
  team2: string;
  picked: string | null;
  disabled: boolean;
  onPick: (team: string | null) => void;
}

function MatchRow({ matchNum, team1, team2, picked, disabled, onPick }: MatchRowProps) {
  const btnStyle = (team: string): React.CSSProperties => ({
    flex: 1,
    textAlign: 'left',
    borderRadius: 4,
    padding: '6px 10px',
    border: picked === team ? '2px solid var(--semi-color-primary)' : '1px solid var(--semi-color-border)',
    backgroundColor: picked === team ? 'var(--semi-color-primary-light-default)' : undefined,
    fontWeight: picked === team ? 600 : 400,
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.6 : 1,
    transition: 'all 0.15s',
    fontSize: 13,
  });

  const handleClick = (team: string) => {
    if (disabled) return;
    onPick(picked === team ? null : team);
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
      <Text type="tertiary" style={{ minWidth: 28, fontSize: 11, textAlign: 'right' }}>
        M{matchNum}
      </Text>
      <div style={{ flex: 1, display: 'flex', gap: 6 }}>
        <div style={btnStyle(team1)} role="button" onClick={() => handleClick(team1)}>
          {team1}
        </div>
        <Text type="tertiary" style={{ alignSelf: 'center', fontSize: 11 }}>vs</Text>
        <div style={btnStyle(team2)} role="button" onClick={() => handleClick(team2)}>
          {team2}
        </div>
      </div>
      {picked && (
        <Tag color="green" size="small" style={{ minWidth: 16 }}>✓</Tag>
      )}
    </div>
  );
}

interface SectionProps {
  title: string;
  subtitle: string;
  done: number;
  total: number;
  children: React.ReactNode;
}

function Section({ title, subtitle, done, total, children }: SectionProps) {
  const exact = done === total;
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <Text strong>{title}</Text>
        <Text type="tertiary" style={{ fontSize: 12 }}>{subtitle}</Text>
        <Badge
          count={`${done}/${total}`}
          style={{ backgroundColor: exact ? 'var(--semi-color-success)' : done > 0 ? 'var(--semi-color-warning)' : 'var(--semi-color-primary)' }}
        />
      </div>
      {children}
    </div>
  );
}

export function KnockoutPredictionManager({ participants, status, onStatusChange }: Props) {
  const [predictions, setPredictions] = useState<KnockoutPrediction[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<Draft>(emptyDraft());
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getKnockoutPredictions().then(setPredictions).catch(console.error);
  }, []);

  const teams = status?.teams ?? [];
  const locked = status?.locked ?? false;
  const r32Pairs = r32PairsFromTeams(teams);

  const valid =
    draft.r32.every(Boolean) &&
    draft.r16.every(Boolean) &&
    draft.qf.every(Boolean) &&
    draft.sf.every(Boolean) &&
    draft.champion !== null;

  function openEdit(p: Participant) {
    const existing = predictions.find((pr) => pr.participantId === p.id);
    setDraft(reconstructDraft(existing, r32Pairs));
    setEditingId(p.id);
  }

  function handlePickChange(round: 'r32' | 'r16' | 'qf' | 'sf', idx: number, team: string | null) {
    setDraft((prev) => setPick(prev, round, idx, team));
  }

  async function handleSave() {
    if (!editingId) return;
    setSaving(true);
    try {
      await saveKnockoutPrediction(editingId, draftToApiPicks(draft));
      const updated = await getKnockoutPredictions();
      setPredictions(updated);
      setEditingId(null);
      onStatusChange();
      Notification.success({ title: 'Saved', content: 'Knockout predictions saved' });
    } catch (err) {
      Notification.error({ title: 'Error', content: err instanceof Error ? err.message : 'Failed to save' });
    } finally {
      setSaving(false);
    }
  }

  const editingParticipant = participants.find((p) => p.id === editingId);

  const columns = [
    {
      title: 'Participant',
      dataIndex: 'name',
      render: (name: string) => <Text strong>{name}</Text>,
    },
    {
      title: 'Status',
      render: (_: unknown, record: Participant) => {
        const pred = predictions.find((pr) => pr.participantId === record.id);
        if (!pred) return <Tag color="grey">No picks</Tag>;
        const isComplete = pred.r32Picks.length === 16 && pred.qfPicks.length === 8 && pred.sfPicks.length === 4 && pred.finalPicks.length === 2 && pred.championPick !== '';
        return <Tag color={isComplete ? 'green' : 'amber'}>{isComplete ? 'Complete ✓' : 'Incomplete'}</Tag>;
      },
    },
    {
      title: 'Action',
      render: (_: unknown, record: Participant) => (
        <Button
          size="small"
          disabled={locked || r32Pairs.length === 0}
          onClick={() => openEdit(record)}
        >
          Edit Picks
        </Button>
      ),
    },
  ];

  // Build R16 match rows from draft r32 picks
  const r16Rows = R16_FROM_R32.map(([a, b], j) => ({
    matchNum: j + 1,
    team1: draft.r32[a] ?? `Winner M${a + 1}`,
    team2: draft.r32[b] ?? `Winner M${b + 1}`,
    locked: !draft.r32[a] || !draft.r32[b],
    picked: draft.r16[j],
  }));

  const qfRows = QF_FROM_R16.map(([a, b], k) => ({
    matchNum: k + 1,
    team1: draft.r16[a] ?? `Winner R16 M${a + 1}`,
    team2: draft.r16[b] ?? `Winner R16 M${b + 1}`,
    locked: !draft.r16[a] || !draft.r16[b],
    picked: draft.qf[k],
  }));

  const sfRows = SF_FROM_QF.map(([a, b], l) => ({
    matchNum: l + 1,
    team1: draft.qf[a] ?? `Winner QF${a + 1}`,
    team2: draft.qf[b] ?? `Winner QF${b + 1}`,
    locked: !draft.qf[a] || !draft.qf[b],
    picked: draft.sf[l],
  }));

  const finalTeam1 = draft.sf[0] ?? 'Winner SF1';
  const finalTeam2 = draft.sf[1] ?? 'Winner SF2';
  const finalLocked = !draft.sf[0] || !draft.sf[1];

  return (
    <Card
      title="🎯 Knockout Predictions 淘汰赛预测"
      style={{ marginBottom: 20 }}
      headerExtraContent={
        locked
          ? <Tag color="red" size="large">Predictions Locked 🔒</Tag>
          : <Tag color="green" size="large">Predictions Open 🔓</Tag>
      }
    >
      {r32Pairs.length === 0 && (
        <Text type="secondary" style={{ display: 'block', marginBottom: 12 }}>
          R32 fixtures not yet loaded. Check back once the knockout stage begins.
        </Text>
      )}
      <Table
        columns={columns}
        dataSource={participants}
        rowKey="id"
        pagination={false}
        size="small"
      />

      <Modal
        title={`Edit Knockout Picks — ${editingParticipant?.name ?? ''}`}
        visible={editingId !== null}
        onCancel={() => setEditingId(null)}
        width={620}
        footer={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Pick one winner per match. Later rounds unlock as you go.
            </Text>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button onClick={() => setEditingId(null)}>Cancel</Button>
              <Button type="primary" disabled={!valid || saving} loading={saving} onClick={handleSave}>
                Save All Picks
              </Button>
            </div>
          </div>
        }
      >
        <div style={{ maxHeight: '65vh', overflowY: 'auto', padding: '4px 0' }}>

          {/* R32 */}
          <Section
            title="Round of 32"
            subtitle="— pick 1 winner per match (16 total)"
            done={draft.r32.filter(Boolean).length}
            total={16}
          >
            {r32Pairs.length === 0 ? (
              <Text type="tertiary">Fixtures not yet available.</Text>
            ) : (
              r32Pairs.map(([t1, t2], i) => (
                <MatchRow
                  key={i}
                  matchNum={i + 1}
                  team1={t1}
                  team2={t2}
                  picked={draft.r32[i]}
                  disabled={false}
                  onPick={(team) => handlePickChange('r32', i, team)}
                />
              ))
            )}
          </Section>

          {/* R16 */}
          <Section
            title="Round of 16"
            subtitle="— your R32 winners face off (8 matches)"
            done={draft.r16.filter(Boolean).length}
            total={8}
          >
            {r16Rows.map((row, j) => (
              <MatchRow
                key={j}
                matchNum={row.matchNum}
                team1={row.team1}
                team2={row.team2}
                picked={row.picked}
                disabled={row.locked}
                onPick={(team) => handlePickChange('r16', j, team)}
              />
            ))}
          </Section>

          {/* QF */}
          <Section
            title="Quarter-Final"
            subtitle="— 4 matches"
            done={draft.qf.filter(Boolean).length}
            total={4}
          >
            {qfRows.map((row, k) => (
              <MatchRow
                key={k}
                matchNum={row.matchNum}
                team1={row.team1}
                team2={row.team2}
                picked={row.picked}
                disabled={row.locked}
                onPick={(team) => handlePickChange('qf', k, team)}
              />
            ))}
          </Section>

          {/* SF */}
          <Section
            title="Semi-Final"
            subtitle="— 2 matches"
            done={draft.sf.filter(Boolean).length}
            total={2}
          >
            {sfRows.map((row, l) => (
              <MatchRow
                key={l}
                matchNum={row.matchNum}
                team1={row.team1}
                team2={row.team2}
                picked={row.picked}
                disabled={row.locked}
                onPick={(team) => handlePickChange('sf', l, team)}
              />
            ))}
          </Section>

          {/* Final + Champion */}
          <Section
            title="Final + Champion"
            subtitle="— pick the winner (8 pts)"
            done={draft.champion ? 1 : 0}
            total={1}
          >
            <MatchRow
              matchNum={1}
              team1={finalTeam1}
              team2={finalTeam2}
              picked={draft.champion}
              disabled={finalLocked}
              onPick={(team) => setDraft((prev) => ({ ...prev, champion: team }))}
            />
          </Section>
        </div>
      </Modal>
    </Card>
  );
}
