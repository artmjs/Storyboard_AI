# app/services/openai_client.py
import os
import base64
from typing import List, Optional
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize the OpenAI client
client = AsyncOpenAI()

def encode_image_bytes(image_bytes: bytes) -> str:
    """
    Convert raw image bytes into a base64-encoded string.
    """
    return base64.b64encode(image_bytes).decode("utf-8")

def encode_image_file(path: str) -> str:
    """
    Read an image file from disk and return its base64 encoding.
    """
    with open(path, "rb") as f:
        return encode_image_bytes(f.read())

async def create_openai_file(path: str) -> str:
    """
    Uploads a local file to OpenAI (e.g., for reference-image workflows)
    and returns the assigned file ID.
    """
    resp = await client.files.create(
        file=open(path, "rb"),
        purpose="image_generation"
    )
    return resp.id

async def refine_sketch(
    prompt: str,
    sketch_bytes: bytes,
    additional_images: Optional[List[bytes]] = None
) -> bytes:
    """
    Sends a multimodal request to GPT-4.1 for image refinement.
    Returns the raw image bytes of the generated panel.

    - prompt: The text instructions for refinement.
    - sketch_bytes: Raw bytes of the primary sketch.
    - additional_images: Optional list of other reference images as raw bytes.
    """
    # Build the 'input' list mixing text + encoded images
    inputs: List[dict] = [
        {"type": "input_text", "text": prompt},
        {
            "type": "input_image",
            "image_url": f"data:image/png;base64,{encode_image_bytes(sketch_bytes)}"
        }
    ]

    # Add any extra images by base64-encoding them
    if additional_images:
        for img_bytes in additional_images:
            inputs.append({
                "type": "input_image",
                "image_url": f"data:image/png;base64,{encode_image_bytes(img_bytes)}"
            })

    # Call the multimodal responses endpoint
    response = await client.responses.create(
        model="gpt-4.1",
        input=[{"role": "user", "content": inputs}],
        tools=[{"type": "image_generation"}],
    )

    # Extract the image-generation call result
    image_calls = [
        out for out in response.output
        if out.type == "image_generation_call"
    ]
    if not image_calls:
        raise RuntimeError(f"No image generated: {response.output}")

    # Decode the base64 result into raw bytes
    image_base64: str = image_calls[0].result
    return base64.b64decode(image_base64)
