import os
import json
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from app.services.image_converter import convert_image
from app.services.size_analyzer import analyze_size_efficiency
from app.services.quality_analyzer import compute_quality_metrics
from app.services.recommendation import generate_recommendations
from app.services.image_metadata import get_image_metadata
from app.utils.file_manager import cleanup_experiment_folders

analysis_bp = Blueprint("analysis_bp", __name__)

def get_experiment_store_path(experiment_id: str) -> Path:
    """Returns path to cached experiment JSON file in instance folder."""
    instance_dir = Path(current_app.instance_path) / "experiments"
    instance_dir.mkdir(parents=True, exist_ok=True)
    return instance_dir / f"{experiment_id}.json"

@analysis_bp.route("/api/experiments", methods=["POST"])
def run_experiment():
    """
    POST /api/experiments
    Executes complete benchmark workflow across requested formats & quality settings.
    Payload (JSON):
    {
        "experiment_id": "<uuid>",
        "formats": ["JPEG", "PNG", "WEBP", "AVIF"],
        "qualities": [25, 50, 75, 90]
    }
    """
    data = request.get_json(silent=True) or {}
    experiment_id = data.get("experiment_id")
    if not experiment_id:
        return jsonify({"status": "error", "message": "Thiếu experiment_id."}), 400
        
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"]) / experiment_id
    if not upload_dir.exists() or not upload_dir.is_dir():
        return jsonify({"status": "error", "message": "Không tìm thấy phiên tải ảnh tương ứng."}), 404
        
    # Locate original image in upload directory
    uploaded_files = [f for f in upload_dir.iterdir() if f.is_file()]
    if not uploaded_files:
        return jsonify({"status": "error", "message": "Không tìm thấy tệp ảnh gốc trong phiên."}), 404
    source_file_path = str(uploaded_files[0])
    
    # Extract metadata
    try:
        metadata = get_image_metadata(source_file_path)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi đọc metadata: {str(e)}"}), 500
        
    requested_formats = data.get("formats", ["JPEG", "PNG", "WEBP"])
    requested_qualities = data.get("qualities", [25, 50, 75, 90])
    
    output_dir = Path(current_app.config["OUTPUT_FOLDER"]) / experiment_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    original_size = metadata["file_size_bytes"]
    width = metadata["width"]
    height = metadata["height"]
    has_alpha = metadata["has_alpha"]
    
    # Process conversions
    for fmt in requested_formats:
        fmt_upper = fmt.upper()
        # For PNG, quality presets map to compression optimization levels
        qualities_to_run = requested_qualities if fmt_upper != "PNG" else [50, 90]
        
        for q in qualities_to_run:
            conversion_res = convert_image(
                source_path=source_file_path,
                output_dir=str(output_dir),
                target_format=fmt_upper,
                quality=int(q)
            )
            
            if conversion_res["success"]:
                comp_path = conversion_res["output_path"]
                compressed_size = conversion_res["file_size_bytes"]
                
                # Size analysis (FR-05)
                size_res = analyze_size_efficiency(
                    original_size_bytes=original_size,
                    compressed_size_bytes=compressed_size,
                    width=width,
                    height=height
                )
                
                # Quality metrics (FR-06)
                quality_res = compute_quality_metrics(
                    reference_path=source_file_path,
                    compressed_path=comp_path
                )
                
                relative_url = f"/media/outputs/{experiment_id}/{conversion_res['filename']}"
                
                results.append({
                    "target_format": fmt_upper,
                    "quality": int(q),
                    "filename": conversion_res["filename"],
                    "url": relative_url,
                    "file_size_bytes": compressed_size,
                    "encoding_time_ms": conversion_res["encoding_time_ms"],
                    "size_analysis": size_res,
                    "quality_metrics": quality_res,
                    "success": True
                })
            else:
                results.append({
                    "target_format": fmt_upper,
                    "quality": int(q),
                    "success": False,
                    "error_message": conversion_res.get("error_message", "Chuyển đổi thất bại"),
                    "file_size_bytes": 0,
                    "encoding_time_ms": 0.0,
                    "size_analysis": {},
                    "quality_metrics": {}
                })
                
    # Generate intelligent recommendations (FR-09)
    recommendations = generate_recommendations(results, has_alpha=has_alpha)
    
    experiment_data = {
        "experiment_id": experiment_id,
        "metadata": metadata,
        "results": results,
        "recommendations": recommendations,
        "original_preview_url": f"/media/uploads/{experiment_id}/{Path(source_file_path).name}"
    }
    
    # Cache to disk for persistence & reports
    store_file = get_experiment_store_path(experiment_id)
    with open(store_file, "w", encoding="utf-8") as f:
        json.dump(experiment_data, f, ensure_ascii=False, indent=2)
        
    return jsonify({
        "status": "success",
        "data": experiment_data
    }), 200

@analysis_bp.route("/api/experiments/<experiment_id>", methods=["GET"])
def get_experiment_status(experiment_id: str):
    """GET /api/experiments/<id>: Check experiment status."""
    store_file = get_experiment_store_path(experiment_id)
    if not store_file.exists():
        return jsonify({"status": "error", "message": "Phiên thử nghiệm không tồn tại."}), 404
        
    return jsonify({
        "status": "success",
        "experiment_id": experiment_id,
        "state": "completed"
    }), 200

@analysis_bp.route("/api/experiments/<experiment_id>/results", methods=["GET"])
def get_experiment_results(experiment_id: str):
    """GET /api/experiments/<id>/results: Retrieve full comparison data."""
    store_file = get_experiment_store_path(experiment_id)
    if not store_file.exists():
        return jsonify({"status": "error", "message": "Phiên thử nghiệm không tồn tại hoặc đã bị xóa."}), 404
        
    with open(store_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    return jsonify({
        "status": "success",
        "data": data
    }), 200

@analysis_bp.route("/api/experiments/<experiment_id>", methods=["DELETE"])
def delete_experiment(experiment_id: str):
    """DELETE /api/experiments/<id>: Safely cleans up temporary assets and logs."""
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    output_dir = current_app.config["OUTPUT_FOLDER"]
    cleanup_experiment_folders(experiment_id, upload_dir, output_dir)
    
    store_file = get_experiment_store_path(experiment_id)
    if store_file.exists():
        try:
            store_file.unlink()
        except Exception:
            pass
            
    return jsonify({
        "status": "success",
        "message": f"Đã xóa toàn bộ dữ liệu phiên {experiment_id} thành công."
    }), 200

