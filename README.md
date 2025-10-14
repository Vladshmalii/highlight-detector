# Highlight Detector

Automated highlight detection system for CS2 and Dota 2 gameplay videos using computer vision, OCR, and audio analysis.

## Features

- **Multi-game support**: CS2 and Dota 2
- **Intelligent detection**: OCR killfeed parsing, audio intensity analysis, visual pattern recognition
- **Smart scoring**: Context-aware scoring system (multi-kills, clutches, rampages, objectives)
- **Top-K selection**: Automatically selects top 5 highlights with temporal spacing
- **Async processing**: FastAPI + Celery for scalable video processing
- **GPU acceleration**: EasyOCR with CUDA support for faster processing

## Architecture

```
FastAPI (REST API)
    ↓
Celery Worker (Async processing)
    ↓
GameDetector → OCR + Audio + Visual
    ↓
HighlightScorer → Context-aware scoring
    ↓
Top-K Selection → Temporal NMS
    ↓
FFmpeg → Clip extraction
```

## Tech Stack

- **Backend**: FastAPI, Celery, Redis
- **Database**: PostgreSQL
- **Computer Vision**: OpenCV, EasyOCR
- **Audio**: Librosa
- **Video**: FFmpeg
- **Container**: Docker, Docker Compose

## Installation

### Prerequisites

- Docker & Docker Compose
- NVIDIA GPU (optional, but recommended)
- NVIDIA Container Toolkit (for GPU support)

### Quick Start

```bash
# Clone repository
git clone <repo-url>
cd highlight-detector

# Start services
docker-compose up --build

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Manual Setup

```bash
# Install system dependencies
apt-get update && apt-get install -y \
    ffmpeg \
    tesseract-ocr \
    libtesseract-dev \
    libsm6 libxext6 libxrender-dev libgomp1

# Install Python dependencies
pip install -r requirements.txt

# Start Redis
redis-server

# Start PostgreSQL
# Configure DATABASE_URL in .env

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start worker
celery -A app.core.celery_app worker --loglevel=info
```

## Usage

### Upload Video

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@gameplay.mp4" \
  -F "game_type=cs2"
```

Response:
```json
{
  "video_id": 1,
  "game_type": "cs2",
  "status": "pending"
}
```

### Check Status

```bash
curl "http://localhost:8000/api/v1/status/1"
```

Response:
```json
{
  "video_id": 1,
  "game_type": "cs2",
  "status": "completed",
  "highlights": [
    {
      "timestamp": 145.2,
      "score": 1200,
      "type": "ace",
      "filename": "highlight_1.mp4"
    }
  ],
  "total_events": 47,
  "processing_time": 892.3
}
```

## Game-Specific Detection

### Counter-Strike 2

**Detection Methods:**
- OCR killfeed parsing (top-right corner)
- Template matching for UI icons
- Special kill detection (headshot, wallbang, noscope)

**Scoring:**
- Kill: 100 points
- Multi-kill: 400 points
- Ace: 1200 points
- Clutch: 800 points
- Multipliers: headshot (1.2x), wallbang (1.5x), noscope (1.8x)

**Highlight Selection:**
- Minimum 30s spacing between clips
- 5s pre-event buffer, 3s post-event buffer

### Dota 2

**Detection Methods:**
- Event banner OCR (top-center)
- Audio intensity peak detection
- Killfeed parsing

**Scoring:**
- Kill: 100 points
- Triple Kill: 500 points
- Ultra Kill: 900 points
- Rampage: 1500 points
- Teamfight: 600 points

**Highlight Selection:**
- Minimum 60s spacing between clips
- 5s pre-event buffer, 3s post-event buffer

## Performance

### Processing Time

| Hardware | 30 min video | 60 min video |
|----------|-------------|--------------|
| CPU only | 60-90 min | 120-180 min |
| GPU (NVIDIA) | 15-30 min | 30-60 min |

### Optimization

**Frame Sampling:**
- Default: Every 5th frame (~6 FPS processing)
- Adjustable via `frame_skip` parameter

**GPU Acceleration:**
- EasyOCR with CUDA
- Automatic CPU fallback if GPU unavailable

## Configuration

### Environment Variables

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/highlights
REDIS_URL=redis://localhost:6379/0
VIDEO_UPLOAD_DIR=/app/videos
```

### Game Type

Supported values:
- `cs2` - Counter-Strike 2
- `dota2` - Dota 2

## API Reference

### Endpoints

#### POST /api/v1/upload
Upload video for processing

**Parameters:**
- `file` (multipart/form-data): Video file
- `game_type` (string): Game type (cs2, dota2)

**Response:**
```json
{
  "video_id": 1,
  "game_type": "cs2",
  "status": "pending"
}
```

#### GET /api/v1/status/{video_id}
Get processing status and results

**Response:**
```json
{
  "video_id": 1,
  "game_type": "cs2",
  "status": "completed",
  "highlights": [...],
  "total_events": 47,
  "processing_time": 892.3,
  "created_at": "2025-10-14T12:00:00",
  "processed_at": "2025-10-14T12:15:00"
}
```

## Project Structure

```
.
├── app/
│   ├── api/
│   │   └── endpoints.py          # FastAPI routes
│   ├── core/
│   │   ├── celery_app.py         # Celery configuration
│   │   ├── config.py             # Settings
│   │   └── enum.py               # Enums (VideoStatus, GameType)
│   ├── models/
│   │   └── video.py              # SQLAlchemy models
│   ├── services/
│   │   ├── detector.py           # Main detection logic
│   │   ├── ocr_engine.py         # OCR processing
│   │   ├── audio_analyzer.py    # Audio analysis
│   │   └── scorers.py            # Scoring system
│   ├── tasks/
│   │   └── video_tasks.py        # Celery tasks
│   └── main.py                   # FastAPI application
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
└── README.md
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format
black app/

# Lint
flake8 app/

# Type check
mypy app/
```

## Troubleshooting

### GPU not detected

```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Install NVIDIA Container Toolkit
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

### Slow processing

- Increase `frame_skip` in `detector.py` (trade accuracy for speed)
- Use GPU acceleration
- Reduce video resolution before upload

### OCR accuracy issues

- Check video quality (minimum 720p recommended)
- Adjust preprocessing parameters in `ocr_engine.py`
- Verify game UI language matches OCR language setting

## Roadmap

- [ ] Multi-language support
- [ ] Real-time streaming detection
- [ ] Custom scoring profiles
- [ ] Web UI for video management
- [ ] Batch processing
- [ ] Cloud storage integration (S3, GCS)

## License

MIT

## Credits

Built with inspiration from:
- [Flowtter/crispy](https://github.com/Flowtter/crispy)
- [colinsenner/csgo-ml-cv](https://github.com/colinsenner/csgo-ml-cv)


## Contributing

Pull requests welcome. For major changes, open an issue first.

## Support

For issues and questions, open a GitHub issue.