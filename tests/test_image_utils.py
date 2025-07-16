import pytest
from PIL import Image
from app.services.image_utils import pad_to_aspect, crop_back

def test_pad_and_crop_visual(tmp_path):
    # 1) Load your existing sample image
    img_path = "./test_images/test_sketch_1.png"
    orig = Image.open(img_path).convert("RGBA")

    # 2) Pad to best ratio + create mask
    padded, mask, offset = pad_to_aspect(orig)

    # 3) Crop back to original
    final = crop_back(padded, offset, orig.size)

    # 4) Save intermediates
    paths = {
        "orig": tmp_path / "orig.png",
        "padded": tmp_path / "padded.png",
        "mask": tmp_path / "mask.png",
        "final": tmp_path / "final.png",
    }
    orig.save(paths["orig"])
    padded.save(paths["padded"])
    mask.save(paths["mask"])
    final.save(paths["final"])

    # 5) Print for visual checking
    for name, path in paths.items():
        print(f"{name} image saved to: {path}")

    # 6) Verify sizes match
    assert final.size == orig.size

    for filename in ("orig.png","padded.png","mask.png","final.png"):
        img = Image.open(tmp_path / filename)
        img.show()