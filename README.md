# ClipCraft - AI Video Generation SaaS

A production-ready FastAPI SaaS platform for AI-powered video generation with async job processing, billing tiers, and real-time progress tracking.

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server (demo mode - no API key needed)
uvicorn app.main:app --reload --port 8000

# Open http://localhost:8000
```

### Docker

```bash
cp .env.example .env
# Edit .env with your API keys (optional - runs in demo mode without them)
docker-compose up --build
```

### Vercel Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

## Demo Mode

When `VIDEO_API_KEY` is empty (default), ClipCraft runs in demo mode:
- Generates animated SVG previews instead of real videos
- No external API calls required
- All features (job queue, progress tracking, billing) still work
- Uses the `demo` API key for authentication

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate` | Submit a video generation job |
| GET | `/api/jobs/{id}` | Poll job status and progress |
| GET | `/api/jobs` | List all jobs for the user |
| DELETE | `/api/jobs/{id}` | Cancel a pending job |
| GET | `/api/queue/stats` | Queue statistics |
| GET | `/api/health` | Health check |
| GET | `/docs` | Interactive API documentation |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VIDEO_PROVIDER` | `runway` | Video API provider (runway/replicate) |
| `VIDEO_API_KEY` | `""` | API key (empty = demo mode) |
| `MAX_CONCURRENT_JOBS` | `3` | Max parallel generation jobs |
| `MAX_VIDEO_DURATION` | `15` | Maximum video length in seconds |

## Billing Tiers

| Tier | Videos/Month | Max Resolution | Max Duration | Price |
|------|-------------|----------------|-------------|-------|
| Free | 3 | 720p | 5s | $0 |
| Starter | 30 | 1080p | 10s | $19.99 |
| Pro | 200 | 4K | 15s | $49.99 |
| Enterprise | Unlimited | 4K | 30s | $149.99 |

## Architecture

- **FastAPI** backend with async job processing
- **SQLite** for job persistence and billing
- **Background tasks** for non-blocking video generation
- **Progress tracking** with polling endpoint
- **Tiered billing** with usage limits
- **Demo mode** for development and testing
