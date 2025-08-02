# Standard library
import logging
import time
import uuid

# Third-party
import redis
from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Local
from celery_worker import celery
from app.core.config import settings, EditRequest
from app.core.redis_client import redis_client
from app.tasks.image_tasks import refine_sketch_task, refine_with_context_task

# logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#app
app = FastAPI(title="Storyboard AI MVP")

# redis client instantiation 
redis_client = redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)

class TimerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        elapsed = time.time() - start
        response.headers["X-Process-Time"] = f"{elapsed:.3f}s"
        logger.debug(f"{request.method} {request.url.path} completed in {elapsed:.3f}s")
        return response
    

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # TIGHTEN LATER
    allow_methods=["*"],        # TIGHTEN LATER
    allow_headers=["*"],        # TIGHTEN LATER
)


app.mount("/frontend", StaticFiles(directory=settings.FRONTEND_DIR, html=True), name="frontend")

app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

@app.post("/api/sketch/refine")
async def refine_endpoint(file: UploadFile):

    start = time.time()


    # read sketch bytes or raise exception
    sketch_bytes = await file.read()
    logger.debug(f"Recieved upload: {len(sketch_bytes)} bytes")
    if not sketch_bytes:
        logger.warning("Upload contained no data")
        raise HTTPException(status_code=422, detail="No file uploaded")


    # enqueue celery task, record time
    image_id = uuid.uuid4().hex
    
    job = refine_sketch_task.delay(
        image_id, 
        settings.FIRST_REFINE_PROMPT, 
        sketch_bytes
        )
    enqueue_time = time.time() - start
    logger.debug(f"Enqueued job {job.id} in {enqueue_time:.3f}s")

    # store job id in a redis set
    redis_client.hset(f"job:{job.id}", "image_id", image_id)

    # return immediately
    resp = JSONResponse({
        "job_id": job.id, 
        "status": "PENDING", 
        "image_id": image_id
        })
    resp.headers["X-Enqueue-Time"] = f"{enqueue_time:.3f}s"
    return resp

# multi turn edit endpoint. 
@app.post("/api/sketch/edit")
async def edit_endpoint(req: EditRequest):
    
    if not redis_client.exists(f"image:{req.image_id}"):
        raise HTTPException(404, "Unknown image_id")

    # enqueue the multi-turn refine
    job = refine_with_context_task.delay(req.image_id, req.prompt)

    # add to the redis set
    redis_client.sadd("jobs", job.id)
    # return the job id
    return JSONResponse(
      {"job_id": job.id, "status": "PENDING", "image_id": req.image_id}
    )


# get all jobs 
@app.get("/api/sketch/status")
def list_all_jobs():
    jobs = []
    for job_id in redis_client.smembers("jobs"):
        res = AsyncResult(job_id, app=celery)
        entry = {"job_id": job_id, "status": res.state}
        if res.state == "SUCCESS":
            entry["url"] = res.result
        elif res.state == "FAILURE":
            entry["error"] = str(res.result)
        jobs.append(entry)
    return jobs

# get one
@app.get("/api/sketch/status/{job_id}")
async def get_sketch_status(job_id: str):
    # Grab the AsyncResult
    result = AsyncResult(job_id, app=celery)

    # Always return the current Celery status
    status = result.status  # "PENDING", "STARTED", "SUCCESS", "FAILURE", etc.

    # On success, also return the URL your task returned
    if status == "SUCCESS":
        try:
            url = result.get(timeout=1, propagate=False)
        except Exception as e:
            # Something went wrong pulling the result
            raise HTTPException(500, detail="Error fetching result")

        return {"status": "SUCCESS", "url": url}

    # Failure
    if status == "FAILURE":
        return {"status": "FAILURE"}

    # 5) return the in‐flight status otherwise
    return {"status": status}

@app.get("/health")
def health():
    return {"status": "ok"}