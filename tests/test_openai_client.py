import base64
import pytest
from app.services.openai_client import encode_image_bytes, refine_sketch

class DummyOut:
    def __init__(self, b64):
        self.type = "image_generation_call"
        self.result = b64


class DummyResp:
    output = [DummyOut(base64.b64encode(b"XYZ").decode())]


@pytest.mark.asyncio
async def test_refine_sketch_success(monkeypatch):

    async def fake_create(model, input, tools):
        return DummyResp()
    
    monkeypatch.setattr(
        "app.services.openai_client.client.responses.create",
        fake_create
    )

    out = await refine_sketch("prompt", b"\x01\x02\x03")
    assert out == b"XYZ"