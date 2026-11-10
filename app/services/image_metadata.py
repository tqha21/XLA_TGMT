import os
from math import gcd
from pathlib import Path
from typing import Dict, Any
from PIL import Image
from app.utils.file_manager import format_bytes

def get_image_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extracts deep metadata from an image file on disk.
    
    Returns structured dictionary with:
    - filename, file_size_bytes, formatted_size
    - format, mode, width, height, megapixels, aspect_ratio
    - has_alpha, bit_depth, dpi
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy tệp ảnh tại: {file_path}")
        
    size_bytes = path.stat().st_size
    
    with Image.open(file_path) as img:
        width, height = img.size
        img_format = (img.format or path.suffix.replace(".", "").upper())
        mode = img.mode
        
        # Check alpha channel
        has_alpha = mode in ("RGBA", "LA", "PA") or (
            mode == "P" and "transparency" in img.info
        )
        
        # Aspect Ratio
        divisor = gcd(width, height) if width > 0 and height > 0 else 1
        aspect_w = width // divisor
        aspect_h = height // divisor
        # If numbers are large, approximate common ratios or use decimal
        if aspect_w > 100 or aspect_h > 100:
            aspect_ratio_str = f"{width / height:.2f}:1" if height else "N/A"
        else:
            aspect_ratio_str = f"{aspect_w}:{aspect_h}"
            
        # DPI
        dpi = img.info.get("dpi")
        if dpi and isinstance(dpi, (tuple, list)) and len(dpi) >= 2:
            dpi_str = f"{int(dpi[0])} x {int(dpi[1])} DPI"
        else:
            dpi_str = "Standard (72/96 DPI)"
            
        # Bit depth estimation
        mode_depth_map = {
            "1": "1-bit (B&W)",
            "L": "8-bit (Grayscale)",
            "P": "8-bit (Palette)",
            "RGB": "24-bit (8-bit per channel)",
            "RGBA": "32-bit (8-bit + Alpha)",
            "CMYK": "32-bit (4 channels)",
            "I": "32-bit (Signed integer)",
            "F": "32-bit (Floating point)"
        }
        bit_depth = mode_depth_map.get(mode, f"{mode} mode")
        
        total_pixels = width * height
        megapixels = round(total_pixels / 1_000_000, 2)
        
    return {
        "filename": path.name,
        "file_size_bytes": size_bytes,
        "formatted_size": format_bytes(size_bytes),
        "format": img_format,
        "mode": mode,
        "width": width,
        "height": height,
        "total_pixels": total_pixels,
        "megapixels": megapixels,
        "aspect_ratio": aspect_ratio_str,
        "has_alpha": has_alpha,
        "bit_depth": bit_depth,
        "dpi": dpi_str
    }

