import io
import os
import time
import base64
import asyncio
from pathlib import Path

from PIL import Image
from celery.utils.log import get_task_logger

from celery_worker import celery
from app.core.config import settings
from app.core.redis_client import redis_client
from app.services.image_utils import pad_to_aspect, crop_back
from app.services.openai_client import client, encode_image_bytes


logger = get_task_logger(__name__)

@celery.task(name="tasks.refine_sketch", acks_later=True)
def refine_sketch_task(image_id: str, prompt: str, sketch_bytes: bytes) -> str: 

    img = Image.open(io.BytesIO(sketch_bytes)).convert("RGBA")
    padded_img, mask_rgba, offset = pad_to_aspect(img)

    buf_img = io.BytesIO()
    buf_mask = io.BytesIO()
    padded_img.save(buf_img, format="PNG"); buf_img.seek(0)
    mask_rgba.save(buf_mask, format="PNG"); buf_mask.seek(0)




    task_id = refine_sketch_task.request.id
    # b64 = encode_image_bytes(sketch_bytes)
    # data_uri = f"data:image/png;base64,{b64}"

    logger.info(f"[{task_id}] Starting OpenAI refine")
    t0 = time.time()


    response = asyncio.get_event_loop().run_until_complete(
        client.responses.create(
        model="gpt-4.1-mini",
        input= [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "file_id": buf_img}
                ]
            }
        ],
        tools=[{
            "type":"image_generation",
            "quality": "high",
            "input_image_mask": {"file_id": buf_mask}
            }]
        ))

    call = next(o for o in response.output if o.type=="image_generation_call")
    img_bytes = base64.b64decode(call.result)
    resp_id   = call.id

    logger.info(f"[{task_id}] OpenAI returned {len(img_bytes)} bytes in {time.time()-t0:.3f}s")

    # decode, crop to original size

    edited = Image.open(io.BytesIO(base64.b64decode(img_bytes))).convert("RGBA")
    final = crop_back(edited, offset, img.size)

    out_dir = Path(settings.STATIC_DIR) / image_id
    out_dir.mkdir(exist_ok=True, parents=True)
    out_path = out_dir / "v1.png"
    with open(out_path, "wb") as f:
        final.save(f, format="PNG")

    # ########### DEBUG FOR THE UTILS

    # output_dir = "image_util_debug"
    # os.makedirs(output_dir, exist_ok=True)

    # images = {
    #     "mask": mask_rgba,
    #     "padded_image": padded_img,
    #     "final": final
    # }

    # for fname, img in images.items():

    #     temp_out = os.path.join(output_dir, f"{fname}".png)
    #     img.save(temp_out)
    #     print(f"saved {fname!r} to {temp_out}")



    # ################
    logger.info(f"[{task_id}] Saved initial panel to {out_path}")

    # persist metadata into Redis:
    #    - the OpenAI response id for chaining
    #    - the latest version so edits know which file to load
    redis_client.hset(f"image:{image_id}", mapping={
        "response_id": resp_id,
        "latest_version": 1
    })

    # return the public URL for v1
    return f"/static/{image_id}/v1.png"

@celery.task(name="tasks.refine_with_context", acks_late=True)
def refine_with_context_task(image_id: str, prompt: str) -> str:

    # prior metadata 
    key = f"image:{image_id}"
    data = redis_client.hgetall(key)
    if not data:
        raise RuntimeError(f"Unknown image_id {image_id}")
    prev_resp = data["response_id"]
    version   = int(data["latest_version"])

    # call multiturn openai 
    resp = client.responses.create(
        model="gpt-4.1",
        input=[
            {"role":"user", "content":[{"type":"input_text","text": prompt}]},
            {"type":"image_generation_call","id": prev_resp},
        ],
        tools=[{"type":"image_generation"}],
    )

    # check async, run until complete
    if hasattr(resp, "__await__"):
        resp = asyncio.get_event_loop().run_until_complete(resp)

    call = next(o for o in resp.output if o.type=="image_generation_call")
    img_bytes = base64.b64decode(call.result)
    new_resp  = call.id

    # Save v{N+1}.png
    new_v = version + 1
    out_dir = Path(settings.STATIC_DIR) / image_id
    out_path = out_dir / f"v{new_v}.png"
    out_dir.mkdir(exist_ok=True, parents=True)
    with open(out_path, "wb") as f:
        f.write(img_bytes)

    # Update Redis
    redis_client.hset(key, mapping={
        "response_id": new_resp,
        "latest_version": new_v
    })

    # 5) Return the new URL
    return f"/static/{image_id}/v{new_v}.png"