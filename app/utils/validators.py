import os
from typing import Tuple, Dict, Any, Optional
from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}
ALLOWED_MIME_PREFIXES = ("image/",)

def allowed_file(filename: str) -> bool:
    """Check if filename extension is in the allowed whitelist."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def validate_image_file(file: Optional[FileStorage], max_size_bytes: int = 20 * 1024 * 1024) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Strict validation of uploaded image file:
    1. Checks presence of file and filename.
    2. Checks file extension against whitelist.
    3. Checks binary size (<= max_size_bytes).
    4. Performs deep header/content verification using Pillow.
    
    Returns:
        (is_valid: bool, error_message: str, metadata_summary: dict)
    """
    if file is None or not file.filename:
        return False, "Không có tệp nào được chọn hoặc tên tệp trống.", {}

    filename = file.filename
    if not allowed_file(filename):
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "không có"
        return False, f"Định dạng tệp '{ext}' không được hỗ trợ. Vui lòng tải PNG, JPG, JPEG, WEBP, BMP hoặc TIFF.", {}

    # Check file size by seeking stream
    try:
        file.seek(0, os.SEEK_END)
        size_bytes = file.tell()
        file.seek(0)
    except Exception as e:
        return False, f"Lỗi đọc kích thước tệp: {str(e)}", {}

    if size_bytes == 0:
        return False, "Tệp được tải lên có dung lượng 0 byte (tệp rỗng).", {}

    if size_bytes > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        curr_mb = size_bytes / (1024 * 1024)
        return False, f"Dung lượng tệp ({curr_mb:.2f} MB) vượt quá giới hạn tối đa cho phép ({max_mb:.1f} MB).", {}

    # Deep verification with Pillow
    try:
        # Protect against decompression bombs with a reasonable limit
        Image.MAX_IMAGE_PIXELS = 100_000_000
        with Image.open(file.stream) as img:
            format_name = img.format
            width, height = img.size
            mode = img.mode
            img.verify()  # Verifies file integrity and header
            
        # Reset stream position after verify() so subsequent reads work
        file.seek(0)
        
        return True, "", {
            "format": format_name,
            "width": width,
            "height": height,
            "mode": mode,
            "size_bytes": size_bytes
        }
    except UnidentifiedImageError:
        file.seek(0)
        return False, "Tệp tải lên không phải là định dạng ảnh hợp lệ hoặc dữ liệu tệp bị hỏng.", {}
    except Image.DecompressionBombError:
        file.seek(0)
        return False, "Ảnh có kích thước điểm ảnh quá lớn (nguy cơ Decompression Bomb).", {}
    except Exception as exc:
        file.seek(0)
        return False, f"Tệp ảnh bị lỗi cấu trúc: {str(exc)}", {}

