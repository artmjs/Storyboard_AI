from celery_worker import celery
import asyncio, time
from app.services.openai_client import refine_sketch
from app.core.config import settings
import uuid
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@celery.task(name="tasks.refine_sketch", acks_later=True)
def refine_sketch_task(prompt: str, sketch_bytes: bytes) -> str: 
    task_id = refine_sketch_task.request.id
    logger.info(f"[{task_id}] Starting OpenAI refine")
    t0 = time.time()

    refined_bytes = asyncio.get_event_loop().run_until_complete(
        refine_sketch(prompt, sketch_bytes))
    logger.info(f"[{task_id}] OpenAI returned {len(refined_bytes)} bytes in {time.time()-t0:.3f}s")

    # save image to disk
    filename = f"{uuid.uuid4().hex}.png"
    out_path = settings.STATIC_DIR / filename
    with open(out_path, "wb") as f:
        f.write(refined_bytes)
    logger.info(f"[{task_id}] Saved to {out_path}")
    
    return f"/static/{filename}"