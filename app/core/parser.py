import base64
import json
import re
from io import BytesIO
from PIL import Image
import ollama
from app.core.config import config

def resize_image(image_path: str, max_size: int = 1024) -> str:
    """Resize image and return as base64 string."""
    img = Image.open(image_path)
    img.thumbnail((max_size, max_size))
    buffer = BytesIO()
    img.save(buffer, format=img.format or "JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def clean_json_output(raw: str) -> dict:
    """Strip markdown fences, remove thousands separators, and parse JSON."""
    cleaned = re.sub(r"```json|```", "", raw).strip()
    cleaned = re.sub(r'(\d),(\d{3})', r'\1\2', cleaned)
    return json.loads(cleaned)

def parse_receipt(image_path: str) -> dict:
    """Send receipt image to VLM and return parsed JSON."""
    try:
        max_size = config.get("max_image_size", 1024)
        image_b64 = resize_image(image_path, max_size)
        
        response = ollama.chat(
            model=config.get("model_name", "qwen2.5vl:3b"),
            messages=[
                {
                    "role": "system",
                    "content": config.get("system_prompt", "")
                },
                {
                    "role": "user",
                    "content": "Here is the receipt.",
                    "images": [image_b64]
                }
            ]
        )
        raw = response["message"]["content"]
        return clean_json_output(raw)

    except json.JSONDecodeError:
        return {"error": "Model returned invalid JSON", "raw": raw}
    except Exception as e:
        return {"error": str(e)}
