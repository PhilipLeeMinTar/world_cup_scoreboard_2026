# ⚽ World Cup 2026 Scoreboard

A live prediction scoreboard for the 2026 FIFA World Cup. Participants predict which teams will top each group, and the app scores them in real-time as group-stage results come in.

**Live site:** [PhilipLeeMinTar.github.io/world_cup_scoreboard_2026](https://philipleemintar.github.io/world_cup_scoreboard_2026/)

---

## Features

- **12 groups (A–L)** matching the 2026 World Cup format
- **17 participants** with predictions for champion & runner-up of each group
- **Live standings** fetched from [worldcup26.ir](https://worldcup26.ir) and auto-scored
- **Leaderboard** ranking participants by points in real time
- **All Scores** view showing every participant's picks vs actual standings side by side
- **Participant manager** — add, edit, or remove participants (in dev mode)
- **Dual mode:** full backend (local dev) or static GitHub Pages (no server needed)

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | React 18 + TypeScript + [Semi Design](https://semi.design) |
| Backend | [Hono](https://hono.dev) on Node.js |
| Database | SQLite via `better-sqlite3` |
| Build | Vite 6 |
| Deploy | GitHub Pages (static) via GitHub Actions |

## Getting Started

```bash
# Install dependencies
npm install

# Seed the database (idempotent — only runs if tables are empty)
npm run seed

# Start dev server (client on :5173, API on :3001)
npm run dev
```

The app opens at `http://localhost:5173`. The Vite dev server proxies `/api` requests to the Hono backend automatically.

## Scripts

| Script | Description |
|---|---|
| `npm run dev` | Start client + server concurrently with hot reload |
| `npm run build` | Type-check and build for production |
| `npm run start` | Run the production server (serves API + static files) |
| `npm run seed` | Seed the SQLite database with groups, participants, and default standings |
| `npm run preview` | Preview the production build locally |
| `./sync-participants.sh` | Export participants from the DB → `src/data/participants.ts` |
| `./sync-participants.sh --commit` | Same as above, then git add + commit + push |

## Syncing Predictions to the Live Site

The GitHub Pages site is **purely static** — there's no server. In production, participant data comes from the hardcoded `src/data/participants.ts` file (with a localStorage cache that auto-invalidates when the file changes).

When you edit predictions locally via `npm run dev`, changes go into the SQLite database. To push those changes to the live site:

```bash
# Option 1: Update the file, then commit manually
./sync-participants.sh

# Option 2: Update, commit, and push in one step
./sync-participants.sh --commit
```

This triggers a GitHub Actions deployment automatically.

## How It Works

### Scoring

Points are awarded based on how accurately each participant predicts the group standings:

- **1st place correctly guessed**: **5 points**
- **2nd place correctly guessed**: **3 points**
- **Right team, wrong position** (e.g. predicted champion but they finished 2nd): **1 point**
- **Wrong team**: **0 points**

### Data Flow

**Local dev (backend mode):**
```
Browser → Vite proxy → Hono API → SQLite DB
                                 ↕
                           worldcup26.ir (polls every 2h)
```

**GitHub Pages (direct mode):**
```
Browser → worldcup26.ir (standings)
        → localStorage / participants.ts (predictions)
```

## Project Structure

```
├── src/
│   ├── api/client.ts          # Unified API (backend / direct mode)
│   ├── components/            # React UI components
│   │   ├── AllScores.tsx      # Everyone's picks vs actual results
│   │   ├── Leaderboard.tsx    # Ranked scoreboard
│   │   ├── ParticipantManager.tsx
│   │   ├── GroupStandingsEditor.tsx
│   │   └── StatusIndicator.tsx
│   ├── data/
│   │   ├── groups.ts          # 12 groups with teams & flags
│   │   └── participants.ts    # All predictions (auto-generated)
│   ├── utils/
│   │   ├── scoring.ts         # Point calculation logic
│   │   └── name-mapping.ts    # API name → display name mapping
│   └── App.tsx                # Main app shell
├── server/
│   ├── index.ts               # Hono server entry point
│   ├── db/
│   │   ├── schema.ts          # SQLite table definitions
│   │   ├── seed.ts            # Database seeder
│   │   └── data/scoreboard.db # SQLite database (gitignored)
│   ├── routes/                # API route handlers
│   └── services/poll.ts       # Background standings poller
├── .github/workflows/deploy.yml  # GitHub Pages deployment
└── sync-participants.sh       # DB → participants.ts sync script
```

## License

Private project — not currently licensed for redistribution.
