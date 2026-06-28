# ⚽ World Cup 2026 Scoreboard

A live prediction scoreboard for the 2026 FIFA World Cup — two separate competitions:

1. **Group Stage** — predict champion & runner-up for each of the 12 groups
2. **Knockout Stage** — predict which teams advance through R32 → QF → SF → Final → Champion

**Live site:** [PhilipLeeMinTar.github.io/world_cup_scoreboard_2026](https://philipleemintar.github.io/world_cup_scoreboard_2026/)

---

## Features

- **Group Stage Leaderboard** — scored from all 12 group predictions (competition over, scores frozen)
- **Knockout Stage Leaderboard** — live scoring as R32 → Final results come in automatically
- **Full group tables** — live stats: Pos, MP, W, D, L, GF, GA, GD, Pts
- **17 participants** with predictions for group stage + knockout rounds
- **Live standings** auto-fetched from openfootball every 2h (group) / 30min (knockout)
- **Participant manager** — add, edit, or remove participants
- **Dual mode:** full backend (local dev) or static GitHub Pages (no server needed)

---

## Getting Started

```bash
# Install dependencies
npm install

# Seed the database (idempotent — safe to run multiple times)
npm run seed

# Start dev server (frontend on :5173, API on :3001)
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api/*` to the Hono backend.

---

## Testing the Knockout Tab

### 1. Open the Knockout tab

Click **🏟️ Knockout 淘汰赛** in the tab bar. You'll see:
- **Knockout Leaderboard** — empty until predictions are saved
- **Knockout Predictions** — all participants with Edit Picks buttons
- **Admin** — live data status + Lock/Unlock

The 32 R32 teams are **automatically loaded from the live API** on startup — no manual configuration needed.

### 2. Enter predictions for a participant

Click **Edit Picks** next to any participant. The modal has 5 sections:

| Section | Pick | Required |
|---|---|---|
| Round of 32 | Teams you think will win their R32 match | exactly 16 |
| Quarter-Final | Teams you think will make the QF | exactly 8 |
| Semi-Final | Teams you think will make the SF | exactly 4 |
| Final | The 2 finalists | exactly 2 |
| Champion | The winner | exactly 1 |

Save Picks is disabled until all counts are exact. Once saved, the participant's status turns green.

### 3. Watch scores appear automatically

As R32 matches finish, the server polls openfootball every 30 minutes and updates results automatically. The leaderboard recalculates on the next page load. You can also hit **🔄 Refresh from API** in the admin panel to force an immediate update.

### 4. Lock predictions

Once all participants have submitted picks, click **Lock Predictions** in the admin panel. This disables all Edit Picks buttons so no one can change their picks mid-tournament.

### 5. Test scoring locally (without waiting for real matches)

You can inject mock results directly into the database:

```bash
sqlite3 server/db/data/scoreboard.db \
  "UPDATE knockout_results SET
     r32_winners_json = '[\"Germany\",\"Brazil\",\"France\",\"Morocco\"]',
     updated_at = datetime('now')
   WHERE id = 1;"
```

Then reload the page — the leaderboard scores update immediately.

---

## Knockout Scoring

| Round | Points per correct pick | Max picks | Max pts |
|---|---|---|---|
| R32 winner | 0.5 pt | 16 | 8 pts |
| QF team | 1 pt | 8 | 8 pts |
| SF team | 2 pts | 4 | 8 pts |
| Finalist | 4 pts | 2 | 8 pts |
| Champion | 8 pts | 1 | 8 pts |
| **Total** | | | **40 pts** |

Scoring is intersection-based: you get points for each team in your picks that appears in the actual results for that round, regardless of bracket position.

---

## Group Stage Scoring

Points are awarded based on how accurately each participant predicts the group standings:

| Result | Points |
|---|---|
| 1st place correctly guessed | 5 pts |
| 2nd place correctly guessed | 3 pts |
| Right team, wrong position (predicted champ but finished 2nd or vice versa) | 1 pt |
| Wrong team | 0 pts |

---

## Scripts

| Script | Description |
|---|---|
| `npm run dev` | Start client + server concurrently with hot reload |
| `npm run build` | Type-check and build for production |
| `npm run start` | Run the production server (serves API + static files) |
| `npm run seed` | Seed the SQLite database |
| `npm run preview` | Preview the production build locally |
| `./sync-participants.sh` | Export participants from DB → `src/data/participants.ts` |
| `./sync-participants.sh --commit` | Same, then git add + commit + push |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/knockout` | Status: lock state, 32 R32 teams, current results |
| GET | `/api/knockout/predictions` | All participants' knockout picks |
| PUT | `/api/knockout/predictions/:id` | Save a participant's picks (403 if locked) |
| POST | `/api/knockout/refresh` | Trigger an immediate live data poll |
| POST | `/api/knockout/lock` | Toggle predictions locked/unlocked |

---

## Data Flow

**Local dev (backend mode):**
```
Browser → Vite proxy → Hono API → SQLite DB
                                 ↕
              openfootball GitHub JSON (group standings: 2h, knockout: 30min)
```

**GitHub Pages (direct mode):**
```
Browser → openfootball (standings computed from match data)
        → localStorage / participants.ts (predictions)
        → knockout tab shows empty state (backend required for knockout)
```

---

## Project Structure

```
├── src/
│   ├── api/client.ts              # Unified API (backend / direct mode)
│   ├── components/
│   │   ├── Leaderboard.tsx        # Group stage leaderboard
│   │   ├── KnockoutLeaderboard.tsx  # Knockout stage leaderboard
│   │   ├── KnockoutPredictionManager.tsx  # Per-participant pick editor
│   │   ├── KnockoutAdmin.tsx      # Admin: lock/unlock + refresh
│   │   ├── ParticipantManager.tsx
│   │   ├── GroupStandingsEditor.tsx
│   │   └── StatusIndicator.tsx
│   ├── utils/
│   │   ├── scoring.ts             # Group stage scoring
│   │   └── knockoutScoring.ts     # Knockout scoring + leaderboard
│   ├── data/
│   │   ├── groups.ts              # 12 groups with teams & flags
│   │   └── participants.ts        # All predictions (auto-generated)
│   └── App.tsx
├── server/
│   ├── index.ts                   # Hono server entry point
│   ├── db/
│   │   ├── schema.ts              # SQLite table definitions (incl. knockout tables)
│   │   ├── seed.ts                # Database seeder
│   │   └── data/scoreboard.db
│   ├── routes/
│   │   ├── knockout.ts            # Knockout API routes
│   │   ├── standings.ts
│   │   ├── participants.ts
│   │   └── status.ts
│   └── services/
│       ├── poll.ts                # Group standings poller (2h)
│       ├── knockout-poll.ts       # Knockout results poller (30min)
│       ├── api-client.ts
│       └── name-mapping.ts
├── .github/workflows/deploy.yml
└── sync-participants.sh
```

---

## License

Private project — not licensed for redistribution.
