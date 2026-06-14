import { getDb } from './server/db/index.js';
import { closeDb } from './server/db/index.js';
import fs from 'fs';

const db = getDb();
const rows = db.prepare('SELECT id, name, predictions_json FROM participants ORDER BY name').all() as Array<{
  id: string;
  name: string;
  predictions_json: string;
}>;

const result = rows.map(r => ({
  id: r.id,
  name: r.name,
  predictions: JSON.parse(r.predictions_json)
}));

const output = JSON.stringify(result, null, 2);
console.log(output);

// Also write to a file for easy reading
fs.writeFileSync('/tmp/wc2026_participants_export.json', output);
console.error(`\nExported ${result.length} participants to /tmp/wc2026_participants_export.json`);

closeDb();
