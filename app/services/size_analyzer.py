from typing import Dict, Any
from app.utils.file_manager import format_bytes

def analyze_size_efficiency(
    original_size_bytes: int,
    compressed_size_bytes: int,
    width: int = 0,
    height: int = 0
) -> Dict[str, Any]:
    """
    Computes compression efficiency metrics:
    - Original & compressed formatted sizes
    - Difference in bytes
    - Space saving percentage: ((original - compressed) / original) * 100
    - Compression ratio: original / compressed
    - Bits Per Pixel (bpp): (compressed_bytes * 8) / (width * height)
    """
    if original_size_bytes <= 0:
        return {
            "original_size_bytes": 0,
            "compressed_size_bytes": compressed_size_bytes,
            "saving_bytes": 0,
            "saving_percent": 0.0,
            "compression_ratio": 1.0,
            "bpp": 0.0,
            "formatted_original": "0 B",
            "formatted_compressed": format_bytes(compressed_size_bytes)
        }
        
    saving_bytes = original_size_bytes - compressed_size_bytes
    saving_percent = round((saving_bytes / original_size_bytes) * 100, 2)
    
    if compressed_size_bytes > 0:
        compression_ratio = round(original_size_bytes / compressed_size_bytes, 2)
    else:
        compression_ratio = 1.0
        
    # Bits per pixel (bpp)
    bpp = 0.0
    if width > 0 and height > 0:
        total_pixels = width * height
        bpp = round((compressed_size_bytes * 8) / total_pixels, 4)
        
    return {
        "original_size_bytes": original_size_bytes,
        "compressed_size_bytes": compressed_size_bytes,
        "saving_bytes": saving_bytes,
        "saving_percent": saving_percent,
        "compression_ratio": compression_ratio,
        "bpp": bpp,
        "formatted_original": format_bytes(original_size_bytes),
        "formatted_compressed": format_bytes(compressed_size_bytes)
    }

