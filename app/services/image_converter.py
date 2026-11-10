import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image

def check_avif_support() -> bool:
    """Check if AVIF encoding is supported in current Python environment."""
    try:
        import pillow_heif  # type: ignore
        pillow_heif.register_avif_opener()
        return True
    except (ImportError, Exception):
        # Fallback check Pillow's internal extensions
        return "AVIF" in Image.registered_extensions().values()

def prepare_image_for_format(img: Image.Image, target_format: str) -> Image.Image:
    """
    Handles alpha channels, color modes and palettes correctly for the target format:
    - JPEG does not support Alpha -> Composite transparent pixels over clean white background.
    - WebP supports RGBA & RGB.
    - PNG supports RGBA, RGB, P, L.
    """
    target = target_format.upper()
    
    if target in ("JPEG", "JPG"):
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            # Create a solid white background and alpha composite
            converted_rgba = img.convert("RGBA")
            background = Image.new("RGBA", converted_rgba.size, (255, 255, 255, 255))
            alpha_composite = Image.alpha_composite(background, converted_rgba)
            return alpha_composite.convert("RGB")
        elif img.mode != "RGB":
            return img.convert("RGB")
    elif target == "WEBP":
        if img.mode not in ("RGB", "RGBA"):
            # If palette with transparency or grayscale, convert cleanly
            if "transparency" in img.info or img.mode == "P":
                return img.convert("RGBA")
            return img.convert("RGB")
    elif target == "PNG":
        if img.mode not in ("RGB", "RGBA", "L", "1"):
            return img.convert("RGBA" if "transparency" in img.info else "RGB")
            
    return img

def convert_image(
    source_path: str,
    output_dir: str,
    target_format: str,
    quality: int = 75,
    filename_prefix: str = ""
) -> Dict[str, Any]:
    """
    Converts source image to specified format & quality level.
    Measures file size and exact encoding time.
    
    Parameters:
    - source_path: Path to original image.
    - output_dir: Destination folder.
    - target_format: 'JPEG', 'PNG', 'WEBP', or 'AVIF'.
    - quality: Integer 1-100 (for lossy formats).
    - filename_prefix: Optional prefix for output filename.
    
    Returns:
        Structured result dict.
    """
    target_format = target_format.upper()
    if target_format == "JPG":
        target_format = "JPEG"
        
    out_dir_path = Path(output_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)
    
    ext_map = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp", "AVIF": "avif"}
    extension = ext_map.get(target_format, target_format.lower())
    
    prefix = f"{filename_prefix}_" if filename_prefix else ""
    out_filename = f"{prefix}{target_format.lower()}_q{quality}.{extension}"
    out_path = out_dir_path / out_filename
    
    # AVIF support check
    if target_format == "AVIF" and not check_avif_support():
        return {
            "target_format": target_format,
            "quality": quality,
            "success": False,
            "error_message": "Định dạng AVIF chưa được hỗ trợ trong môi trường này (cần thư viện pillow-heif hoặc libheif).",
            "file_size_bytes": 0,
            "encoding_time_ms": 0.0,
            "output_path": ""
        }
        
    start_time = time.perf_counter()
    try:
        with Image.open(source_path) as src_img:
            # Preserve resolution
            original_dimensions = src_img.size
            prepared_img = prepare_image_for_format(src_img, target_format)
            
            save_params: Dict[str, Any] = {}
            if target_format == "JPEG":
                save_params = {
                    "format": "JPEG",
                    "quality": max(1, min(quality, 100)),
                    "optimize": True,
                    "progressive": True
                }
            elif target_format == "WEBP":
                save_params = {
                    "format": "WEBP",
                    "quality": max(1, min(quality, 100)),
                    "method": 6  # Best compression speed/effort tradeoff
                }
            elif target_format == "PNG":
                # For PNG, map quality 1-100 to compress_level (1..9)
                compress_level = max(1, min(int(round((100 - quality) / 10)), 9)) if quality < 100 else 6
                save_params = {
                    "format": "PNG",
                    "optimize": True,
                    "compress_level": compress_level
                }
            elif target_format == "AVIF":
                save_params = {
                    "format": "AVIF",
                    "quality": max(1, min(quality, 100))
                }
                
            prepared_img.save(str(out_path), **save_params)
            
        elapsed_sec = time.perf_counter() - start_time
        encoding_time_ms = round(elapsed_sec * 1000, 2)
        
        file_size_bytes = out_path.stat().st_size
        
        # Verify resolution preserved
        with Image.open(str(out_path)) as verified_img:
            new_dimensions = verified_img.size
            
        return {
            "target_format": target_format,
            "quality": quality,
            "success": True,
            "output_path": str(out_path),
            "filename": out_filename,
            "file_size_bytes": file_size_bytes,
            "encoding_time_ms": encoding_time_ms,
            "dimensions": new_dimensions,
            "resolution_preserved": (original_dimensions == new_dimensions),
            "error_message": None
        }
    except Exception as exc:
        elapsed_sec = time.perf_counter() - start_time
        return {
            "target_format": target_format,
            "quality": quality,
            "success": False,
            "error_message": f"Lỗi chuyển đổi: {str(exc)}",
            "file_size_bytes": 0,
            "encoding_time_ms": round(elapsed_sec * 1000, 2),
            "output_path": ""
        }

