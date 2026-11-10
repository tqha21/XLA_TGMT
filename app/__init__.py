import os
from pathlib import Path
from flask import Flask, jsonify, request
from PIL import Image, UnidentifiedImageError
from config import Config

def create_app(config_class=Config):
    """
    Application Factory for Image Format Comparison Web System.
    Includes Enterprise-Grade Security defenses against:
    - Path Traversal & Extension Spoofing
    - Decompression Bomb Attacks (Image Bomb DoS)
    - Corrupted / Malformed Image Exploits
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure Pillow Security Policy
    max_pixels = app.config.get("MAX_IMAGE_PIXELS", 100_000_000)
    Image.MAX_IMAGE_PIXELS = max_pixels
    
    # Ensure all working directories exist
    for dir_key in ["UPLOAD_FOLDER", "OUTPUT_FOLDER", "SAMPLE_FOLDER"]:
        folder_path = app.config.get(dir_key)
        if folder_path:
            Path(folder_path).mkdir(parents=True, exist_ok=True)
            
    # Instance cache directory
    (Path(app.instance_path) / "experiments").mkdir(parents=True, exist_ok=True)
    
    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.upload import upload_bp
    from app.routes.analysis import analysis_bp
    from app.routes.reports import reports_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(reports_bp)
    
    # Global Error Handlers
    @app.errorhandler(Image.DecompressionBombError)
    def handle_decompression_bomb(error):
        error_msg = (
            f"Tệp ảnh bị từ chối: Kích thước điểm ảnh vượt quá ngưỡng an toàn cho phép "
            f"({max_pixels:,} pixels). Nguy cơ tấn công Decompression Bomb."
        )
        if request.path.startswith("/api/"):
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 400
        return f"<h3>Lỗi 400: {error_msg}</h3>", 400

    @app.errorhandler(UnidentifiedImageError)
    def handle_unidentified_image(error):
        error_msg = "Tệp tải lên không phải là định dạng ảnh hợp lệ hoặc dữ liệu tệp đã bị hỏng."
        if request.path.startswith("/api/"):
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 400
        return f"<h3>Lỗi 400: {error_msg}</h3>", 400

    @app.errorhandler(413)
    def request_entity_too_large(error):
        max_mb = app.config.get("MAX_CONTENT_LENGTH", 20 * 1024 * 1024) / (1024 * 1024)
        if request.path.startswith("/api/"):
            return jsonify({
                "status": "error",
                "message": f"Dung lượng tệp vượt quá giới hạn tối đa cho phép ({max_mb:.0f} MB)."
            }), 413
        return f"<h3>Lỗi 413: Tệp quá lớn (Giới hạn tối đa {max_mb:.0f} MB).</h3>", 413

    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith("/api/"):
            return jsonify({
                "status": "error",
                "message": "Không tìm thấy tài nguyên yêu cầu (404 Not Found)."
            }), 404
        return "<h3>Lỗi 404: Không tìm thấy trang.</h3>", 404

    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith("/api/"):
            return jsonify({
                "status": "error",
                "message": "Đã xảy ra lỗi hệ thống máy chủ (500 Internal Server Error)."
            }), 500
        return "<h3>Lỗi 500: Lỗi máy chủ nội bộ.</h3>", 500

    return app
