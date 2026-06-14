import React, { useState, useEffect, useCallback } from 'react';
import {
  Layout,
  Typography,
  Tabs,
  TabPane,
  Notification,
  Spin,
} from '@douyinfe/semi-ui';
import { GroupStanding, Participant, ScoreBreakdown, Prediction } from './types';
import { GroupStandingsViewer } from './components/GroupStandingsEditor';
import { Leaderboard, ScoreDetailCard } from './components/Leaderboard';
import { ParticipantManager } from './components/ParticipantManager';
import { AllScoresView } from './components/AllScores';
import { StatusIndicator } from './components/StatusIndicator';
import { calculateLeaderboard } from './utils/scoring';
import {
  detectMode,
  getMode,
  AppMode,
  fetchStandings as apiFetchStandings,
  refreshStandings as apiRefreshStandings,
  fetchParticipants as apiFetchParticipants,
  addParticipant as apiAddParticipant,
  updateParticipant as apiUpdateParticipant,
  deleteParticipant as apiDeleteParticipant,
  fetchStatus as apiFetchStatus,
  PollStatus,
} from './api/client';

const { Header, Content, Footer } = Layout;
const { Title, Text } = Typography;

const AUTO_REFRESH_MS = 30_000; // 30 seconds

function App() {
  const [mode, setMode] = useState<AppMode | 'detecting'>('detecting');
  const [standings, setStandings] = useState<GroupStanding[]>([]);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [pollStatus, setPollStatus] = useState<PollStatus | null>(null);
  const [expandedParticipant, setExpandedParticipant] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Detect mode and load initial data
  useEffect(() => {
    async function init() {
      const detected = await detectMode();
      setMode(detected);
      console.log(`App mode: ${detected}`);

      try {
        const [standingsData, participantsData, statusData] = await Promise.all([
          apiFetchStandings(),
          apiFetchParticipants(),
          apiFetchStatus(),
        ]);
        setStandings(standingsData.standings);
        setParticipants(participantsData);
        setPollStatus(statusData);
      } catch (err) {
        // Fall back to defaults if API is unreachable
        console.warn('Failed to load from API, using defaults:', err);
        const { getDefaultStandings } = await import('./utils/scoring');
        const { INITIAL_PARTICIPANTS } = await import('./data/participants');
        setStandings(getDefaultStandings());
        setParticipants(INITIAL_PARTICIPANTS);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  // Auto-refresh standings every 30 seconds
  useEffect(() => {
    if (mode === 'detecting') return;
    const interval = setInterval(async () => {
      try {
        const [standingsData, statusData] = await Promise.all([
          apiFetchStandings(),
          apiFetchStatus(),
        ]);
        setStandings(standingsData.standings);
        setPollStatus(statusData);
      } catch {
        // Silently fail on background refresh
      }
    }, AUTO_REFRESH_MS);
    return () => clearInterval(interval);
  }, [mode]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      const [standingsData, statusData] = await Promise.all([
        apiRefreshStandings(),
        apiFetchStatus(),
      ]);
      setStandings(standingsData.standings);
      setPollStatus(statusData);
      if (standingsData.success) {
        Notification.success({ title: 'Scores updated', content: 'Latest standings fetched from live API' });
      } else {
        Notification.warning({ title: 'Refresh issue', content: standingsData.error || 'Could not fetch live data' });
      }
    } catch (err) {
      Notification.error({ title: 'Refresh failed', content: 'Could not reach the live scores API' });
    } finally {
      setRefreshing(false);
    }
  }, []);

  const handleAddParticipant = useCallback(async (participant: Omit<Participant, 'id'>) => {
    const result = await apiAddParticipant(participant);
    setParticipants((prev) => [...prev, result]);
    return result;
  }, []);

  const handleUpdateParticipant = useCallback(async (id: string, data: Partial<Participant>) => {
    await apiUpdateParticipant(id, data);
    const updated = await apiFetchParticipants();
    setParticipants(updated);
  }, []);

  const handleDeleteParticipant = useCallback(async (id: string) => {
    await apiDeleteParticipant(id);
    setParticipants((prev) => prev.filter((p) => p.id !== id));
  }, []);

  const leaderboard = calculateLeaderboard(participants, standings);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        color: '#fff',
        gap: 24,
      }}>
        <div style={{ fontSize: 64, animation: 'pulse 1.5s ease-in-out infinite' }}>⚽</div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
            <span style={{ fontSize: 22, fontWeight: 700 }}>Seah Family World Cup 2026</span>
            <span style={{
              background: 'linear-gradient(135deg, #e94560, #ff6b81)',
              padding: '2px 10px',
              borderRadius: 12,
              fontSize: 14,
              fontWeight: 700,
              letterSpacing: '0.5px',
            }}>
              HUAT AH 🧧
            </span>
          </div>
          <div style={{ fontSize: 15, opacity: 0.75, fontStyle: 'italic' }}>Wishing everyone the best of luck! 祝大家好运！🍀</div>
          <div style={{ marginTop: 16 }}><Spin size="large" /></div>
        </div>
        <style>{`
          @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.15); }
          }
        `}</style>
      </div>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        padding: '16px 20px',
        borderBottom: '3px solid #e94560',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
          maxWidth: 1400,
          margin: '0 auto',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 36, filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))' }}>⚽</span>
            <div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
                <Title heading={3} style={{
                  color: '#fff',
                  margin: 0,
                  fontSize: 20,
                  fontWeight: 700,
                  textShadow: '0 1px 3px rgba(0,0,0,0.3)',
                }}>
                  Seah Family World Cup 2026
                </Title>
                <span style={{
                  background: 'linear-gradient(135deg, #e94560, #ff6b81)',
                  color: '#fff',
                  padding: '2px 10px',
                  borderRadius: 12,
                  fontSize: 13,
                  fontWeight: 700,
                  letterSpacing: '0.5px',
                  boxShadow: '0 2px 6px rgba(233,69,96,0.4)',
                }}>
                  HUAT AH 🧧
                </span>
              </div>
              <Text style={{
                color: 'rgba(255,255,255,0.65)',
                fontSize: 12,
                marginTop: 2,
                display: 'block',
                fontStyle: 'italic',
              }}>
                Wishing everyone the best of luck! 祝大家好运！🍀
              </Text>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <StatusIndicator
              status={pollStatus}
              loading={refreshing}
              onRefresh={handleRefresh}
              mode={mode === 'detecting' ? 'direct' : mode}
            />
          </div>
        </div>
      </Header>

      <Content style={{ padding: '16px', maxWidth: 1400, margin: '0 auto', width: '100%' }}>
        <Tabs type="button" size="large" style={{ marginBottom: 20 }}>
          <TabPane tab="🏆 Leaderboard 排行榜" itemKey="leaderboard">
            <Leaderboard leaderboard={leaderboard} />

            {expandedParticipant && leaderboard.find(p => p.id === expandedParticipant) && (
              <ScoreDetailCard participant={leaderboard.find(p => p.id === expandedParticipant)!} />
            )}

            {leaderboard.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
                  Click a participant row to see their detailed score breakdown
                </Text>
              </div>
            )}
          </TabPane>

          <TabPane tab="⚽ Group Standings 小组积分榜" itemKey="standings">
            <GroupStandingsViewer
              standings={standings}
              onRefresh={handleRefresh}
              refreshing={refreshing}
              updatedAt={pollStatus?.lastPollAt || ''}
            />
          </TabPane>

          <TabPane tab={`👥 Participants 参与者 (${participants.length})`} itemKey="participants">
            <ParticipantManager
              participants={participants}
              onAdd={handleAddParticipant}
              onUpdate={handleUpdateParticipant}
              onDelete={handleDeleteParticipant}
            />
          </TabPane>

          <TabPane tab="📊 Detailed Breakdown 详细积分" itemKey="breakdown">
            <AllScoresView
              participants={participants}
              standings={standings}
              expandedParticipant={expandedParticipant}
              onExpand={setExpandedParticipant}
            />
          </TabPane>
        </Tabs>
      </Content>

      <Footer style={{
        textAlign: 'center',
        background: '#1a1a2e',
        color: 'rgba(255,255,255,0.5)',
        padding: '12px 24px',
      }}>
        <Text style={{ color: 'rgba(255,255,255,0.5)' }}>
          FIFA World Cup 2026 Betting Scoreboard — Scoring: Champion +5 | Runner-up +3 | Advancement Bonus +1
        </Text>
      </Footer>
    </Layout>
  );
}

export default App;
