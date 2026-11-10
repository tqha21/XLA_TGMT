import os
import warnings
from typing import Tuple, Dict, Any, Optional
from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage
import puremagic

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}

# Allowed MIME types recognized from Magic Bytes
ALLOWED_IMAGE_MIMES = {
    "image/jpeg": {"jpg", "jpeg"},
    "image/pjpeg": {"jpg", "jpeg"},
    "image/png": {"png"},
    "image/webp": {"webp"},
    "image/bmp": {"bmp"},
    "image/x-ms-bmp": {"bmp"},
    "image/tiff": {"tiff", "tif"},
    "image/x-tiff": {"tiff", "tif"}
}

# Dangerous executable signatures for targeted defense
DANGEROUS_SIGNATURES = {
    b"MZ": ("Windows Executable / DLL", ".exe"),
    b"\x7fELF": ("Linux ELF Executable", ".elf"),
    b"\xca\xfe\xba\xbe": ("Java Class / Mach-O Binary", ".class"),
    b"%!PS": ("PostScript File", ".ps"),
    b"<?php": ("PHP Script", ".php"),
    b"#!/bin": ("Shell Script", ".sh")
}

def allowed_file(filename: str) -> bool:
    """Check if filename extension is in the allowed whitelist."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def detect_magic_bytes(header_chunk: bytes) -> Tuple[Optional[str], Optional[str]]:
    """
    Analyzes the raw byte header using puremagic to determine true MIME and extension.
    Returns: (detected_mime, detected_ext)
    """
    if not header_chunk:
        return None, None

    # 1. Fast path: Check known dangerous execution headers
    for sig, (desc, ext) in DANGEROUS_SIGNATURES.items():
        if header_chunk.startswith(sig):
            return "application/x-executable", ext

    # 2. Deep signature analysis with puremagic
    try:
        detected_mime = puremagic.from_string(header_chunk, mime=True)
    except Exception:
        detected_mime = None

    try:
        detected_ext = puremagic.from_string(header_chunk)
        if detected_ext and detected_ext.startswith("."):
            detected_ext = detected_ext[1:].lower()
    except Exception:
        detected_ext = None

    # 3. Fallback: Standard image magic numbers
    if not detected_mime or detected_mime == "application/octet-stream":
        if header_chunk.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png", "png"
        elif header_chunk.startswith(b"\xff\xd8\xff"):
            return "image/jpeg", "jpg"
        elif header_chunk.startswith(b"RIFF") and len(header_chunk) >= 12 and header_chunk[8:12] == b"WEBP":
            return "image/webp", "webp"
        elif header_chunk.startswith(b"BM"):
            return "image/bmp", "bmp"
        elif header_chunk.startswith(b"II*\x00") or header_chunk.startswith(b"MM\x00*"):
            return "image/tiff", "tiff"

    return detected_mime, detected_ext

def validate_image_file(
    file: Optional[FileStorage],
    max_size_bytes: int = 20 * 1024 * 1024,
    max_pixels: int = 100_000_000
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Senior Defense-in-Depth Validation for Uploaded Images:
    1. Check presence of file and filename.
    2. Check declared extension against whitelist.
    3. Check binary file size against threshold.
    4. Magic Bytes (Byte Header) inspection via puremagic to stop extension spoofing.
    5. Pillow Content & Integrity verification.
    6. Decompression Bomb Attack defense (Image Bomb protection).
    
    Returns:
        (is_valid: bool, error_message: str, metadata_summary: dict)
    """
    if file is None or not file.filename:
        return False, "Không có tệp nào được chọn hoặc tên tệp trống.", {}

    filename = file.filename
    declared_ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    
    if not allowed_file(filename):
        return False, f"Định dạng tệp '{declared_ext}' không được hỗ trợ. Vui lòng tải PNG, JPG, JPEG, WEBP, BMP hoặc TIFF.", {}

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

    # 4. Magic Bytes Inspection (Byte Header Verification)
    try:
        header_chunk = file.read(2048)
        file.seek(0)
    except Exception as e:
        return False, f"Lỗi đọc dữ liệu header tệp: {str(e)}", {}

    detected_mime, detected_ext = detect_magic_bytes(header_chunk)

    if not detected_mime:
        return False, "Tệp bị từ chối: Không thể xác định cấu trúc định dạng thực tế (Magic Bytes không hợp lệ hoặc dữ liệu bị hỏng).", {}

    # Check if file is executable or non-image disguised as image
    if detected_mime not in ALLOWED_IMAGE_MIMES and not detected_mime.startswith("image/"):
        return (
            False,
            f"Phát hiện tệp bị giả mạo định dạng (File Spoofing Attack)! "
            f"Tên tệp khai báo đuôi '.{declared_ext}' nhưng nội dung thực tế là "
            f"'{detected_ext or 'Unknown'}' (MIME type: {detected_mime}).",
            {}
        )

    # Check compatibility between declared extension and detected MIME
    compatible_extensions = ALLOWED_IMAGE_MIMES.get(detected_mime, set())
    if compatible_extensions and declared_ext not in compatible_extensions:
        # Standardize jpg/jpeg
        if not (declared_ext in {"jpg", "jpeg"} and compatible_extensions.intersection({"jpg", "jpeg"})):
            return (
                False,
                f"Định dạng tệp không khớp với cấu trúc thực tế: "
                f"Tên tệp là '.{declared_ext}' nhưng dữ liệu ảnh thực tế là MIME '{detected_mime}'.",
                {}
            )

    # 5. Pillow Deep Integrity Check & Decompression Bomb Protection
    try:
        # Configure strictly to defense threshold
        Image.MAX_IMAGE_PIXELS = max_pixels
        
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always", Image.DecompressionBombWarning)
            with Image.open(file.stream) as img:
                format_name = img.format
                width, height = img.size
                mode = img.mode
                
                # Check for warnings raised during header reading
                for w in caught_warnings:
                    if issubclass(w.category, Image.DecompressionBombWarning):
                        file.seek(0)
                        return (
                            False,
                            f"Cảnh báo bảo mật: Kích thước ảnh ({width}x{height} = {width*height:,} px) "
                            f"vượt quá ngưỡng cho phép ({max_pixels:,} px). Nguy cơ tấn công Decompression Bomb.",
                            {}
                        )
                
                # Manual pixel verification against configured limit
                total_pixels = width * height
                if total_pixels > max_pixels:
                    file.seek(0)
                    return (
                        False,
                        f"Tệp bị từ chối: Kích thước ảnh ({width}x{height} = {total_pixels:,} px) "
                        f"vượt quá ngưỡng an toàn ({max_pixels:,} px). Nguy cơ tấn công Decompression Bomb.",
                        {}
                    )
                
                # Verify structural integrity
                img.verify()
                
        # Reset stream position after verify()
        file.seek(0)
        
        return True, "", {
            "format": format_name,
            "width": width,
            "height": height,
            "mode": mode,
            "size_bytes": size_bytes,
            "detected_mime": detected_mime
        }
    except Image.DecompressionBombError:
        file.seek(0)
        return False, f"Tệp ảnh bị từ chối: Kích thước điểm ảnh quá lớn (vượt quá {max_pixels:,} pixels). Nguy cơ tấn công Decompression Bomb.", {}
    except UnidentifiedImageError:
        file.seek(0)
        return False, "Tệp tải lên không phải là định dạng ảnh hợp lệ hoặc dữ liệu tệp bị hỏng.", {}
    except Exception as exc:
        file.seek(0)
        return False, f"Tệp ảnh bị lỗi cấu trúc: {str(exc)}", {}
