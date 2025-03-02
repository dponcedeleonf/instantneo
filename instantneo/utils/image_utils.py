import base64
from typing import List, Dict, Any, Union
from urllib.parse import urlparse

def is_url(path: str) -> bool:
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_media_type_from_extension(img_path: str) -> str:
    extension = img_path.split('.')[-1].lower()
    if extension in ["jpg", "jpeg"]:
        return "image/jpeg"
    elif extension == "png":
        return "image/png"
    elif extension == "gif":
        return "image/gif"
    elif extension == "webp":
        return "image/webp"
    else:
        raise ValueError("Unsupported image format.")

def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_images(images: Union[str, List[str]], image_detail: str) -> List[Dict[str, Any]]:
    if isinstance(images, str):
        images = [images]

    processed_images = []
    for img_path in images:
        if is_url(img_path):
            processed_images.append({
                "type": "image_url",
                "image_url": {
                    "url": img_path
                }
            })
        else:
            media_type = get_media_type_from_extension(img_path)
            img_data = encode_image_to_base64(img_path)
            processed_images.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{media_type};base64,{img_data}"
                }
            })

    return processed_images