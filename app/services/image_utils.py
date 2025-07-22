import math
from PIL import Image
import io

def _padding_overhead(orig_w: int, orig_h: int, A: int, B: int) -> int:
    
    scale = max(orig_w/A, orig_h/B)
    new_w = math.ceil(A*scale)
    new_h = math.ceil(B*scale)

    return (new_w * new_h) - (orig_w * orig_h)

def pick_best_ratio(orig_w: int, orig_h: int) -> tuple[int, int]:
    """
    From the tree supported aspect ratios in the OpenAI api, 
    pick the closest one to the original image
    """

    candidates = {(1,1), (2,3), (3,2)}

    best = min(candidates, key=lambda ab: _padding_overhead(orig_w, orig_h, *ab))

    return best

def pad_to_aspect(img: Image.Image) -> tuple[Image.Image, Image.Image, tuple[int,int]]:
    """
    Pads img up to the closest of the three supported aspect ratios.

    :return: (padded_img, mask, (pad_x, pad_y)).
    :rtype: tuple[Image.Image, Image.Image, tuple[int,int]]
    """
    orig_w, orig_h = img.size
    A, B = pick_best_ratio(orig_w, orig_h)

    scale = max(orig_w/A, orig_h/B)
    new_w, new_h = math.ceil(A * scale), math.ceil(B * scale)
    pad_x, pad_y = (new_w - orig_w) // 2, (new_h - orig_h) // 2

    padded = Image.new("RGBA", (new_w, new_h), (0,0,0,0))
    padded.paste(img, (pad_x, pad_y))

    mask_l = Image.new("L", (new_w, new_h), 0)
    mask_l.paste(255, (pad_x, pad_y, pad_x + orig_w, pad_y + orig_h))

    mask_rgba = mask_l.convert("RGBA")  
    mask_rgba.putalpha(mask_l)      

    return padded, mask_rgba, (pad_x, pad_y)

def crop_back(img: Image.Image, pad_xy: tuple[int,int], orig_size: tuple[int,int]) -> Image.Image:
    pad_x, pad_y = pad_xy
    orig_w, orig_h = orig_size
    return img.crop((pad_x, pad_y, pad_x + orig_w, pad_y + orig_h))

def pil_to_buffer(img: Image.Image, name: str) -> io.BytesIO:
    buf = io.BytesIO()
    buf.name = name
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
