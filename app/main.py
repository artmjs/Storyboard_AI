from fastapi import FastAPI, UploadFile, HTTPException
from celery_worker import celery
from celery.result import AsyncResult
from app.tasks.image_tasks import refine_sketch_task
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging 
import time
import redis
from app.core.config import settings
from starlette.middleware.base import BaseHTTPMiddleware

# logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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


app.mount("/static", StaticFiles(directory="static"), name="static")
@app.post("/api/sketch/refine")
async def refine_endpoint(file: UploadFile):

    start = time.time()

    # read sketch bytes or raise exception
    sketch_bytes = await file.read()
    logger.debug(f"Recieved upload: {len(sketch_bytes)} bytes")


    if not sketch_bytes:
        logger.warning("Upload contained no data")
        raise HTTPException(status_code=400, detail="No file uploaded")


    prompt = "Refine this storyboard sketch into a clean, professional pencil drawn panel." \
    " Keep the exact same composition, placement of objects, framing. Only change the " \
    "visual style of the sketch."

    # enqueue celery task, record time
    job = refine_sketch_task.delay(prompt, sketch_bytes)

    enqueue_time = time.time() - start
    logger.debug(f"Enqueued job {job.id} in {enqueue_time:.3f}s")

    # store job id in a redis set
    redis_client.sadd("jobs", job.id)





    # return immediately
    resp = JSONResponse({"job_id": job.id, "status": "PENDING"})
    resp.headers["X-Enqueue-Time"] = f"{enqueue_time:.3f}s"

    return resp


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

@app.get("/health")
def health():
    return {"status": "ok"}