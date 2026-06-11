import { Hono } from 'hono';
import { getDb } from '../db/index.js';
import type { Prediction, Participant } from '../../src/types.js';

const participants = new Hono();

// GET /api/participants — return all participants
participants.get('/', (c) => {
  const db = getDb();
  const rows = db.prepare('SELECT id, name, predictions_json FROM participants ORDER BY name').all() as Array<{
    id: string;
    name: string;
    predictions_json: string;
  }>;

  const result: Participant[] = rows.map((r) => ({
    id: r.id,
    name: r.name,
    predictions: JSON.parse(r.predictions_json),
  }));

  return c.json(result);
});

// POST /api/participants — add a new participant
participants.post('/', async (c) => {
  const body = await c.req.json() as Omit<Participant, 'id'>;
  const db = getDb();

  const id = `p_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  db.prepare('INSERT INTO participants (id, name, predictions_json) VALUES (?, ?, ?)').run(
    id,
    body.name,
    JSON.stringify(body.predictions)
  );

  return c.json({ id, ...body }, 201);
});

// PUT /api/participants/:id — update a participant
participants.put('/:id', async (c) => {
  const id = c.req.param('id');
  const body = await c.req.json() as Partial<Participant>;
  const db = getDb();

  const existing = db.prepare('SELECT id FROM participants WHERE id = ?').get(id);
  if (!existing) {
    return c.json({ error: 'Participant not found' }, 404);
  }

  if (body.name || body.predictions) {
    const current = db.prepare('SELECT name, predictions_json FROM participants WHERE id = ?').get(id) as {
      name: string;
      predictions_json: string;
    };

    const newName = body.name || current.name;
    const newPredictions = body.predictions || JSON.parse(current.predictions_json);

    db.prepare('UPDATE participants SET name = ?, predictions_json = ? WHERE id = ?').run(
      newName,
      JSON.stringify(newPredictions),
      id
    );
  }

  return c.json({ success: true });
});

// DELETE /api/participants/:id — delete a participant
participants.delete('/:id', (c) => {
  const id = c.req.param('id');
  const db = getDb();

  const existing = db.prepare('SELECT id FROM participants WHERE id = ?').get(id);
  if (!existing) {
    return c.json({ error: 'Participant not found' }, 404);
  }

  db.prepare('DELETE FROM participants WHERE id = ?').run(id);

  return c.json({ success: true });
});

export default participants;
