import io
import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage
from app.utils.validators import allowed_file, validate_image_file

def test_allowed_extensions():
    assert allowed_file("photo.jpg") is True
    assert allowed_file("photo.JPEG") is True
    assert allowed_file("graphic.png") is True
    assert allowed_file("banner.webp") is True
    assert allowed_file("script.py") is False
    assert allowed_file("malicious.exe") is False
    assert allowed_file("no_extension") is False

def test_valid_image_upload():
    # Create an in-memory valid PNG image
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

def test_reject_empty_file():
    empty_io = io.BytesIO(b"")
    file_storage = FileStorage(stream=empty_io, filename="empty.png")
    is_valid, msg, _ = validate_image_file(file_storage)
    assert is_valid is False
    assert "rỗng" in msg or "0 byte" in msg

def test_reject_oversized_file():
    # Simulate a file larger than max size (using 100 bytes limit for test)
    fake_io = io.BytesIO(b"a" * 500)
    file_storage = FileStorage(stream=fake_io, filename="large.png")
    is_valid, msg, _ = validate_image_file(file_storage, max_size_bytes=200)
    assert is_valid is False
    assert "vượt quá" in msg

def test_reject_corrupted_or_fake_file():
    # Text file disguised as PNG
    fake_img = io.BytesIO(b"This is just plain text, not a valid image stream.")
    file_storage = FileStorage(stream=fake_img, filename="fake.png")
    is_valid, msg, _ = validate_image_file(file_storage)
    assert is_valid is False
    assert "không phải là định dạng ảnh hợp lệ" in msg

