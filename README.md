# Storyboard AI MVP

## Overview
Storyboard AI MVP is a minimal prototype that refines hand-drawn sketches into polished storyboard panels. A FastAPI application accepts uploads, Celery workers call OpenAI's image generation APIs, and Redis tracks task metadata. A small HTML frontend is included for quick testing.

## Features
- `POST /api/sketch/refine` – upload a PNG sketch and queue a refinement job.
- `POST /api/sketch/edit` – apply iterative edits to an existing image using a text prompt.
- `GET /api/sketch/status` – list jobs and their progress; `GET /api/sketch/status/{job_id}` checks a single job.
- `GET /health` – simple health check.

## Setup
1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Create a `.env` file** with at least:
   ```bash
   OPENAI_API_KEY=<your-key>
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```
3. Ensure a Redis server is running and reachable by the above URLs.

## Running
Start the Celery worker and API server in separate terminals:
```bash
celery -A celery_worker.celery worker --loglevel=info
uvicorn app.main:app --reload
```
The frontend is served at http://localhost:8000/frontend and static images appear under `./static`.

## Testing
Run the unit tests with:
```bash
pytest
```
