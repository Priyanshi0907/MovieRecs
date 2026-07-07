# MovieRecs — AI-Powered Movie Recommendation Platform

MovieRecs is a full-stack movie recommendation web app combining collaborative filtering, content-based similarity, semantic search, and an LLM-powered chatbot to help users discover movies they'll actually enjoy.

## Features

- **Hybrid recommendation engine** — blends collaborative filtering (custom SVD on user ratings), content-based similarity (TF-IDF + Gemini semantic embeddings), user preference matching, and global popularity/rating signals.
- **AI movie chatbot** — natural-language movie search ("romcoms that would make you cry," "movies like Interstellar but less emotional") powered by Gemini embeddings for semantic search, with a rules-based fallback when no Gemini key is configured.
- **TMDb integration** — pulls a diverse, multi-source catalog (popular, top-rated, genre/decade discovery, and international-language titles) rather than just trending Hollywood releases.
- **Personalization** — onboarding questionnaire (genres, actors, directors, mood, runtime, language preferences), cold-start recommendations for new users, and a full ratings/watchlist/review system.
- **Taste Analytics dashboard** — genre distribution, ratings history, release-year breakdown, and real watch-activity timeline, with manual + periodic auto-refresh.
- **Guest mode** — full functionality without requiring account creation.
- **Admin/maintenance tooling** — endpoints to sync new movies, backfill missing posters, repair broken poster links, and backfill semantic embeddings, all designed to run as non-blocking background jobs.

## Tech Stack

**Backend**
- FastAPI (Python) + SQLAlchemy ORM
- SQLite by default (swap to Postgres via `DATABASE_URL` for production)
- scikit-learn (TF-IDF + cosine similarity), NumPy/Pandas
- Custom SVD implementation for collaborative filtering
- Google Gemini API (`google-generativeai`) — chatbot reasoning + text embeddings
- TMDb API — movie metadata, posters, cast/crew, trailers

**Frontend**
- React (Vite)
- Tailwind CSS
- React Router
- Recharts (analytics visualizations)
- Lucide icons

## Project Structure

```
Movie-Recommendation/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, all API routes
│   │   ├── models.py        # SQLAlchemy models (User, Movie, Rating, Watchlist, History, Review)
│   │   ├── database.py      # DB engine/session + lightweight migrations
│   │   ├── auth.py          # JWT auth, password hashing, guest user
│   │   ├── recommender.py   # Hybrid recommender: SVD, TF-IDF, Gemini embeddings
│   │   ├── ai.py            # Chatbot: intent extraction, semantic search, reply generation
│   │   ├── tmdb.py          # TMDb API integration, sync, poster repair
│   │   └── seed.py          # Database seeding (hand-picked classics + live TMDb sync)
│   ├── requirements.txt
│   └── movies.db            # SQLite database (created on first run)
└── frontend/
    ├── src/
    │   ├── pages/            # HomeDashboard, MovieDetailPage, WatchlistPage, AnalyticsDashboard, etc.
    │   ├── components/        # NavBar, MovieCard, ChatbotWidget, etc.
    │   └── api.js             # Backend API client
    └── package.json
```

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- A [TMDb API key](https://www.themoviedb.org/settings/api) (free)
- A [Google Gemini API key](https://aistudio.google.com/apikey) (free tier available) — required for the chatbot's semantic search and AI reasoning; the app degrades gracefully to rules-based matching without it, but accuracy is significantly better with it configured

## Setup

### 1. Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:

```dotenv
TMDB_API_KEY=your_tmdb_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET_KEY=replace_with_a_long_random_string

# Optional (see "Environment Variables" below for defaults)
DATABASE_URL=
CORS_ALLOWED_ORIGINS=
```

Start the server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On first run with an empty database, the app automatically seeds itself: it syncs a broad movie catalog from TMDb, adds a curated set of classic and horror titles, creates a Guest account and 79 synthetic users with clustered ratings (for collaborative filtering to have something to learn from), and — if `GEMINI_API_KEY` is set — begins backfilling semantic embeddings in the background. This can take a few minutes on first boot.

The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173` by default.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `TMDB_API_KEY` | Yes | — | Required for seeding, search, poster resolution, and catalog sync. |
| `GEMINI_API_KEY` | Recommended | — | Powers chatbot reasoning and semantic embeddings. App falls back to a rules-based chatbot without it. |
| `JWT_SECRET_KEY` | Recommended | insecure dev default | Secret used to sign auth tokens. **Set a real value before deploying.** |
| `DATABASE_URL` | No | local SQLite file | Set to a Postgres connection string for production use — SQLite doesn't handle concurrent writes well under real traffic. |
| `CORS_ALLOWED_ORIGINS` | No | `*` (all origins) | Comma-separated list of allowed frontend origins in production, e.g. `https://yourapp.com`. |
| `VITE_API_BASE_URL` (frontend) | No | `http://localhost:8000/api` | Set to your deployed backend URL when building the frontend for production. |

## Admin / Maintenance Endpoints

These support ongoing catalog upkeep without requiring a full reseed:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/admin/sync-tmdb` | POST | Pull additional movies from TMDb (`{"count": 500}`). |
| `/api/admin/backfill-posters` | POST | Resolve posters for movies with a missing `poster_path`. |
| `/api/admin/repair-broken-posters` | POST | Validate and fix movies whose stored poster path is set but invalid/404ing. |
| `/api/admin/backfill-embeddings` | POST | Compute semantic embeddings for movies that don't have one yet. |
| `/health` | GET | Liveness check for deployment platforms. |

All of these are designed to run in bounded batches and as background tasks — safe to call repeatedly on a large catalog without blocking the server.

## How the Recommendation Engine Works

1. **Semantic search (primary, when Gemini is configured)** — the chatbot embeds the user's raw query and searches the catalog by meaning, not keywords, using cached Gemini embeddings (`models/embedding-001`).
2. **Content-based similarity (TF-IDF fallback)** — genre/overview/cast/director similarity via cosine similarity, used when embeddings aren't available or for the "Because you watched..." / "Similar movies" sections.
3. **Collaborative filtering** — a custom SVD model trained on the user-movie ratings matrix, predicting how a given user would likely rate an unseen movie.
4. **Hybrid scoring** — combines collaborative score, content score, explicit user preference overlap (genres/actors/directors/language), and global popularity/rating into a single ranked list for the "Recommended For You" section.
5. **Cold start** — new users with no ratings get recommendations based purely on their onboarding questionnaire until they've rated enough movies for collaborative filtering to kick in.

## Known Limitations

- **SQLite in production**: fine for demos/small deployments, but doesn't handle concurrent writes well at scale. Switch to Postgres via `DATABASE_URL` before real production traffic.
- **Embedding backfill cost**: computing embeddings makes one API call per movie; large catalogs should be backfilled incrementally via the admin endpoint rather than all at once.
- **TMDb data quality**: some lightweight-ingested (non-English or obscure) titles may have incomplete cast/director data until individually resolved via search or the detail page (which lazy-loads full details on view).
- **No production-grade rate limiting** on the chatbot or admin endpoints — add this before public deployment.

## Deployment Checklist

- [ ] Set a real, random `JWT_SECRET_KEY`
- [ ] Restrict `CORS_ALLOWED_ORIGINS` to your actual frontend domain
- [ ] Set `VITE_API_BASE_URL` to your deployed backend URL before building the frontend (`npm run build`)
- [ ] Consider migrating to Postgres via `DATABASE_URL` if expecting concurrent traffic
- [ ] Ensure `TMDB_API_KEY` and `GEMINI_API_KEY` are set as environment variables on your hosting platform, never committed to source control
- [ ] Run `/api/admin/backfill-embeddings` and `/api/admin/backfill-posters` after your initial production seed completes

## License

This project is for educational/personal use.
