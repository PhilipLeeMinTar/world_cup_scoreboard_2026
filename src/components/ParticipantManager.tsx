import React, { useState } from 'react';
import {
  Select,
  Typography,
  Card,
  Button,
  Space,
  Modal,
  Input,
  Table,
  Tag,
  Notification,
} from '@douyinfe/semi-ui';
import { IconPlus, IconDelete, IconEdit } from '@douyinfe/semi-icons';
import { Participant, Prediction } from '../types';
import { WORLD_CUP_2026_GROUPS } from '../data/groups';
import { getDefaultPredictions } from '../utils/scoring';

const { Title, Text } = Typography;

interface ParticipantManagerProps {
  participants: Participant[];
  onAdd: (participant: Omit<Participant, 'id'>) => Promise<Participant>;
  onUpdate: (id: string, data: Partial<Participant>) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export function ParticipantManager({ participants, onAdd, onUpdate, onDelete }: ParticipantManagerProps) {
  const [modalVisible, setModalVisible] = useState(false);
  const [editingParticipant, setEditingParticipant] = useState<Participant | null>(null);
  const [formName, setFormName] = useState('');
  const [formPredictions, setFormPredictions] = useState<Prediction[]>(getDefaultPredictions());
  const [saving, setSaving] = useState(false);

  const openAddModal = () => {
    setEditingParticipant(null);
    setFormName('');
    setFormPredictions(getDefaultPredictions());
    setModalVisible(true);
  };

  const openEditModal = (participant: Participant) => {
    setEditingParticipant(participant);
    setFormName(participant.name);
    setFormPredictions([...participant.predictions]);
    setModalVisible(true);
  };

  const handleSave = async () => {
    if (!formName.trim()) {
      Notification.warning({ title: 'Name required', content: 'Please enter a participant name' });
      return;
    }

    const incomplete = formPredictions.filter((p) => !p.champion || !p.runnerUp);
    if (incomplete.length > 0) {
      Notification.warning({
        title: 'Incomplete predictions',
        content: `Please fill in predictions for Group ${incomplete.map((p) => p.groupName).join(', ')}`,
      });
      return;
    }

    const duplicates = formPredictions.filter((p) => p.champion === p.runnerUp);
    if (duplicates.length > 0) {
      Notification.warning({
        title: 'Duplicate selections',
        content: `Champion and runner-up must be different in Group ${duplicates.map((p) => p.groupName).join(', ')}`,
      });
      return;
    }

    setSaving(true);
    try {
      if (editingParticipant) {
        await onUpdate(editingParticipant.id, {
          name: formName.trim(),
          predictions: formPredictions,
        });
        Notification.success({ title: 'Updated', content: `${formName}'s predictions updated` });
      } else {
        await onAdd({
          name: formName.trim(),
          predictions: formPredictions,
        });
        Notification.success({ title: 'Added', content: `${formName} added to the competition` });
      }
      setModalVisible(false);
    } catch (err) {
      Notification.error({ title: 'Save failed', content: 'Could not save to server' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = (id: string) => {
    const participant = participants.find((p) => p.id === id);
    Modal.confirm({
      title: 'Delete Participant',
      content: `Are you sure you want to remove ${participant?.name}?`,
      onOk: async () => {
        try {
          await onDelete(id);
          Notification.info({ title: 'Removed', content: `${participant?.name} has been removed` });
        } catch {
          Notification.error({ title: 'Delete failed', content: 'Could not delete from server' });
        }
      },
    });
  };

  const handlePredictionChange = (
    groupName: string,
    field: 'champion' | 'runnerUp',
    value: string
  ) => {
    setFormPredictions((prev) =>
      prev.map((p) => {
        if (p.groupName !== groupName) return p;
        return { ...p, [field]: value };
      })
    );
  };

  const predictionColumns = [
    {
      title: 'Group',
      dataIndex: 'groupName',
      width: 70,
      render: (name: string) => <Text strong>Group {name}</Text>,
    },
    {
      title: '🥇 Champion (1st)',
      dataIndex: 'champion',
      width: 200,
      render: (champion: string, record: Prediction) => {
        const group = WORLD_CUP_2026_GROUPS.find((g) => g.name === record.groupName);
        return (
          <Select
            value={champion || undefined}
            onChange={(val) => handlePredictionChange(record.groupName, 'champion', String(val))}
            placeholder="Select champion"
            style={{ width: '100%' }}
            optionList={group?.teams.map((t) => ({
              value: t.name,
              label: `${t.flag} ${t.name}`,
            }))}
            filter
          />
        );
      },
    },
    {
      title: '🥈 Runner-up (2nd)',
      dataIndex: 'runnerUp',
      width: 200,
      render: (runnerUp: string, record: Prediction) => {
        const group = WORLD_CUP_2026_GROUPS.find((g) => g.name === record.groupName);
        const availableTeams = group?.teams.filter((t) => t.name !== record.champion);
        return (
          <Select
            value={runnerUp || undefined}
            onChange={(val) => handlePredictionChange(record.groupName, 'runnerUp', String(val))}
            placeholder="Select runner-up"
            style={{ width: '100%' }}
            optionList={availableTeams?.map((t) => ({
              value: t.name,
              label: `${t.flag} ${t.name}`,
            }))}
            filter
          />
        );
      },
    },
  ];

  const participantColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      render: (name: string) => <Text strong>{name}</Text>,
    },
    {
      title: 'Predictions',
      render: (_: unknown, record: Participant) => (
        <Text type="secondary">{record.predictions.length} groups predicted</Text>
      ),
    },
    {
      title: 'Actions',
      width: 150,
      render: (_: unknown, record: Participant) => (
        <Space>
          <Button
            icon={<IconEdit />}
            size="small"
            onClick={() => openEditModal(record)}
          >
            Edit
          </Button>
          <Button
            icon={<IconDelete />}
            size="small"
            type="danger"
            onClick={() => handleDelete(record.id)}
          />
        </Space>
      ),
    },
  ];

  return (
    <Card
      title="👥 Participants & Predictions 参与者与预测"
      style={{ marginBottom: 20 }}
      headerExtraContent={
        <Button icon={<IconPlus />} theme="solid" onClick={openAddModal}>
          Add Participant
        </Button>
      }
    >
      <div style={{ overflowX: 'auto' }}>
      <Table
        columns={participantColumns}
        dataSource={participants}
        rowKey="id"
        pagination={false}
        size="small"
        empty={<Text type="secondary">No participants yet. Add someone to get started!</Text>}
      />
      </div>

      <Modal
        title={editingParticipant ? `Edit ${editingParticipant.name}'s Predictions` : 'Add New Participant'}
        visible={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        okText={editingParticipant ? 'Save Changes' : 'Add Participant'}
        confirmLoading={saving}
        width={700}
        style={{ maxHeight: '80vh' }}
        bodyStyle={{ overflowY: 'auto', maxHeight: '60vh' }}
      >
        <div style={{ marginBottom: 16 }}>
          <Text strong style={{ display: 'block', marginBottom: 6 }}>Participant Name</Text>
          <Input
            value={formName}
            onChange={setFormName}
            placeholder="Enter name"
          />
        </div>

        <Title heading={5} style={{ marginBottom: 8 }}>
          Predictions
        </Title>
        <Text type="secondary" style={{ marginBottom: 12, display: 'block' }}>
          Select the champion (1st) and runner-up (2nd) for each group.
        </Text>

        <div style={{ overflowX: 'auto' }}>
        <Table
          columns={predictionColumns}
          dataSource={formPredictions}
          rowKey="groupName"
          pagination={false}
          size="small"
        />
        </div>
      </Modal>
    </Card>
  );
}
