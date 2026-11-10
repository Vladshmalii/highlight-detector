<div align="center">

<img src="https://capsule-render.vercel.app/api?type=rect&color=0:0d1117,100:161b22&height=180&section=header&text=Highlight%20Detector&fontSize=40&fontColor=e6edf3&fontAlignY=42&desc=Automatic%20highlight%20clips%20from%20CS2%20and%20Dota%202%20gameplay&descSize=15&descColor=8b949e&descAlignY=64" width="100%"/>

**Upload a match recording, get the best moments back as ready-to-share clips.**

![Python](https://img.shields.io/badge/Python-161b22?style=for-the-badge&logo=python&logoColor=58a6ff)
![FastAPI](https://img.shields.io/badge/FastAPI-161b22?style=for-the-badge&logo=fastapi&logoColor=58a6ff)
![Celery](https://img.shields.io/badge/Celery-161b22?style=for-the-badge&logo=celery&logoColor=58a6ff)
![OpenCV](https://img.shields.io/badge/OpenCV-161b22?style=for-the-badge&logo=opencv&logoColor=58a6ff)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-161b22?style=for-the-badge&logo=postgresql&logoColor=58a6ff)
![Redis](https://img.shields.io/badge/Redis-161b22?style=for-the-badge&logo=redis&logoColor=58a6ff)
![Docker](https://img.shields.io/badge/Docker-161b22?style=for-the-badge&logo=docker&logoColor=58a6ff)

</div>

---

Highlight Detector is an asynchronous video-processing service for esports footage. A recording is uploaded over a REST API, a Celery worker scans it with OCR on the on-screen UI and with audio-energy analysis, scores the detected events with game-specific rules, and cuts the top moments into short clips with FFmpeg.

It is a compact, working prototype of a full pipeline: API, queue, computer vision, signal processing, persistence and containerised deployment.

## Highlights

- **Two games, one pipeline.** CS2 (killfeed, top-right) and Dota 2 (event banner, top-center) share the detector and differ only in regions of interest and scoring rules.
- **OCR on the game UI.** Each region is cropped, converted to grayscale, upscaled 3x, Otsu-thresholded and morphologically closed before EasyOCR reads it.
- **Audio as a second signal.** Librosa loads the soundtrack; squared amplitude is smoothed over a 0.5 s window and peaks above mean + 2.5 sigma (at least 5 s apart) are flagged. Peaks with no OCR event within 3 s become `teamfight` events.
- **Context-aware scoring and selection.** Per-game score tables, special-kill multipliers, then top-5 selection with minimum spacing (30 s for CS2, 60 s for Dota 2) so clips do not overlap.
- **Async by design.** FastAPI accepts the upload and returns immediately; a Celery worker (Redis broker) processes it with up to 3 retries and writes status and results to PostgreSQL.
- **One-command stack.** Docker Compose brings up API, worker, PostgreSQL 16 and Redis 7.

## How it works

```mermaid
flowchart LR
    C[Client] -->|POST /api/v1/upload| A[FastAPI]
    A -->|save file, insert row| DB[(PostgreSQL)]
    A -->|process_video.delay| R[(Redis)]
    R --> W[Celery worker]
    W --> D[GameDetector]
    D --> O[OCR: killfeed or banner ROI]
    D --> U[Audio: energy peaks]
    O --> M[Merge events]
    U --> M
    M --> S[HighlightScorer]
    S --> K[Top-K with min spacing]
    K --> F[FFmpeg: 8 s clips]
    F --> DB
    C -->|GET /api/v1/status/id| A
```

| Component | File | Role |
|---|---|---|
| API | `app/api/endpoints.py`, `app/main.py` | `POST /api/v1/upload`, `GET /api/v1/status/{video_id}`; tables are created on startup |
| Task | `app/tasks/video_tasks.py` | `process_video`: status transitions, detection, scoring, FFmpeg cutting, retry (max 3, 60 s countdown) |
| Detector | `app/services/detector.py` | Reads every 5th frame with OpenCV, runs game-specific OCR, merges with audio peaks |
| OCR | `app/services/ocr_engine.py` | ROI preprocessing and EasyOCR (English) |
| Audio | `app/services/audio_analyzer.py` | Librosa load (22.05 kHz mono), intensity peak detection |
| Scoring | `app/services/scorers.py` | `CS2Scorer`, `Dota2Scorer`, top-K selection |
| Model | `app/models/video.py` | `Video` table: status, highlights (JSON), total events, processing time |

Scoring as implemented:

| Game | Rules |
|---|---|
| CS2 | kill 100, multi_kill 400, ace 1200, clutch 800; multipliers headshot 1.2, wallbang 1.5, noscope 1.8 |
| Dota 2 | kill 100, teamfight 600, objective 800; banner text "triple kill" 500, "ultra kill" 900, "rampage" 1500 |

Clips start 5 s before the event and last 8 s (H.264 / AAC, `-preset fast`).

## Tech stack

| Layer | Tools |
|---|---|
| API | FastAPI 0.109, Uvicorn, Pydantic Settings |
| Queue | Celery 5.3, Redis 7 |
| Storage | PostgreSQL 16, SQLAlchemy 2.0, psycopg2 |
| Computer vision | OpenCV, EasyOCR 1.7 |
| Audio | Librosa, SciPy, NumPy |
| Video | FFmpeg |
| Runtime | Python 3.11, Docker, Docker Compose |

## Quick start

Requires Docker and Docker Compose.

```bash
git clone https://github.com/Vladshmalii/highlight-detector.git
cd highlight-detector
docker-compose up --build
```

API on `http://localhost:8000`, interactive docs on `http://localhost:8000/docs`.

```bash
curl -X POST "http://localhost:8000/api/v1/upload" -F "file=@gameplay.mp4" -F "game_type=cs2"
# {"video_id": 1, "game_type": "cs2", "status": "pending"}

curl "http://localhost:8000/api/v1/status/1"
# status: pending | processing | completed | failed
# on completion: highlights[] (timestamp, score, type, filename, path), total_events, processing_time
```

`game_type` accepts `cs2` (default) or `dota2`. Clips are written to `videos/highlights_<video_id>/highlight_<n>.mp4` (mounted from `./videos`).

Without Docker: install FFmpeg and `requirements.txt`, run PostgreSQL and Redis, set `DATABASE_URL` and `REDIS_URL`, then start `uvicorn app.main:app` and `celery -A app.core.celery_app worker --loglevel=info`.

## Configuration

Read by `app/core/config.py` from the environment or a `.env` file.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql://user:pass@localhost:5432/highlights` | SQLAlchemy connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Celery broker and result backend |
| `VIDEO_UPLOAD_DIR` | `/app/videos` | Uploads and generated clips |
| `HOST`, `PORT`, `LOG_LEVEL` | `0.0.0.0`, `8000`, `info` | Read by `entrypoint.sh` for the API server |

The `user:pass` values are local development defaults from `docker-compose.yml`; change them for any real deployment.

## Project structure

```
app/
  api/endpoints.py        upload + status routes
  core/                   config, Celery app, enums
  models/video.py         SQLAlchemy model
  services/               detector, ocr_engine, audio_analyzer, scorers
  tasks/video_tasks.py    process_video Celery task
  main.py                 FastAPI app
alembic/env.py            Alembic environment (no ini or versions yet)
Dockerfile  docker-compose.yml  entrypoint.sh  requirements.txt
```

## Testing

There is no test suite in the repository yet.

## Status and roadmap

Working prototype. Known limits, stated plainly:

- Detection is keyword matching on OCR text. CS2 emits `kill` events with `headshot` / `wallbang` tags; `ace`, `clutch` and `noscope` have score entries but no detector produces them yet.
- OCR regions are fixed fractions of the frame, so results depend on resolution and HUD layout; English only.
- `frame_skip` (5) is a constant in `detector.py`, not a setting. EasyOCR is created with `gpu=True`; the Compose file does not configure GPU access.
- No accuracy or throughput benchmarks have been measured.
- Schema is created with `create_all`; Alembic migrations are not set up. No authentication or upload size limits.

Roadmap: richer event detection (multi-kill, clutch, ace), configurable frame sampling and ROIs, tests, migrations, web UI, cloud storage.

## Credits

Inspired by [Flowtter/crispy](https://github.com/Flowtter/crispy) and [colinsenner/csgo-ml-cv](https://github.com/colinsenner/csgo-ml-cv).
