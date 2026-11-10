import io
import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage
from app.utils.validators import allowed_file, validate_image_file

def test_allowed_extensions():
    """Verify extension whitelist logic."""
    assert allowed_file("photo.jpg") is True
    assert allowed_file("photo.JPEG") is True
    assert allowed_file("graphic.png") is True
    assert allowed_file("banner.webp") is True
    assert allowed_file("script.py") is False
    assert allowed_file("malicious.exe") is False
    assert allowed_file("no_extension") is False

def test_valid_image_upload():
    """Verify legitimate PNG image passes all security checks."""
    img_io = io.BytesIO()
    img = Image.new("RGB", (120, 80), color=(100, 150, 200))
    img.save(img_io, format="PNG")
    img_io.seek(0)
    
    file_storage = FileStorage(stream=img_io, filename="test_sample.png", content_type="image/png")
    is_valid, msg, meta = validate_image_file(file_storage, max_size_bytes=20 * 1024 * 1024)
    
    assert is_valid is True
    assert msg == ""
    assert meta["format"] == "PNG"
    assert meta["width"] == 120
    assert meta["height"] == 80
    assert meta["detected_mime"] == "image/png"

def test_reject_empty_file():
    """Zero-byte files must be rejected immediately."""
    empty_io = io.BytesIO(b"")
    file_storage = FileStorage(stream=empty_io, filename="empty.png")
    is_valid, msg, _ = validate_image_file(file_storage)
    assert is_valid is False
    assert "rỗng" in msg or "0 byte" in msg

def test_reject_oversized_file():
    """Files exceeding byte limit must be rejected safely without reading whole stream."""
    fake_io = io.BytesIO(b"a" * 500)
    file_storage = FileStorage(stream=fake_io, filename="large.png")
    is_valid, msg, _ = validate_image_file(file_storage, max_size_bytes=200)
    assert is_valid is False
    assert "vượt quá" in msg

def test_reject_executable_spoofed_as_png():
    """
    Security Test: Windows Executable (.exe) disguised as .png.
    Magic Bytes: 'MZ' header (PE executable).
    Must detect file spoofing attack via puremagic.
    """
    fake_exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00" + b"\x00" * 200
    fake_io = io.BytesIO(fake_exe_bytes)
    file_storage = FileStorage(stream=fake_io, filename="malicious_payload.png", content_type="image/png")
    
    is_valid, msg, _ = validate_image_file(file_storage)
    assert is_valid is False
    assert "giả mạo định dạng" in msg or "File Spoofing" in msg

def test_reject_mismatched_image_format():
    """
    Security Test: Valid JPEG bytes disguised with .png extension.
    Must detect that byte header is image/jpeg while declared extension is .png.
    """
    img_io = io.BytesIO()
    img = Image.new("RGB", (64, 64), color=(200, 50, 50))
    img.save(img_io, format="JPEG")
    img_io.seek(0)
    
    file_storage = FileStorage(stream=img_io, filename="fake_jpeg_renamed_to.png", content_type="image/png")
    is_valid, msg, _ = validate_image_file(file_storage)
    assert is_valid is False
    assert "không khớp" in msg or "image/jpeg" in msg

def test_reject_decompression_bomb_attack():
    """
    Security Test: Decompression Bomb Attack (Image Bomb DoS).
    Upload image with pixel dimension exceeding configured MAX_IMAGE_PIXELS.
    System must catch exception safely and reject file without crashing server.
    """
    # Create image with 1500 x 1500 = 2,250,000 pixels
    # Test with max_pixels threshold = 1,000,000 pixels
    bomb_io = io.BytesIO()
    img = Image.new("RGB", (1500, 1500), color=(255, 255, 255))
    img.save(bomb_io, format="PNG")
    bomb_io.seek(0)
    
    file_storage = FileStorage(stream=bomb_io, filename="decompression_bomb.png", content_type="image/png")
    is_valid, msg, _ = validate_image_file(
        file_storage,
        max_size_bytes=20 * 1024 * 1024,
        max_pixels=1_000_000  # Threshold under 2.25M px
    )
    
    assert is_valid is False
    assert "Decompression Bomb" in msg or "ngưỡng an toàn" in msg

def test_reject_corrupted_or_garbage_bytes():
    """Non-image garbage data disguised as image must be rejected."""
    garbage_io = io.BytesIO(b"Hello world! This is just random plain text without image header.")
    file_storage = FileStorage(stream=garbage_io, filename="garbage.png")
    is_valid, msg, _ = validate_image_file(file_storage)
    assert is_valid is False
