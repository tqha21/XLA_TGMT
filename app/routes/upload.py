import os
from flask import Blueprint, request, jsonify, current_app
from app.utils.validators import validate_image_file
from app.utils.file_manager import create_experiment_id, save_uploaded_file
from app.services.image_metadata import get_image_metadata

upload_bp = Blueprint("upload_bp", __name__)

@upload_bp.route("/api/images/upload", methods=["POST"])
def upload_image():
    """
    API FR-01 & FR-02: Upload image, validate strictly, extract metadata.
    Supports either direct file upload (multipart/form-data)
    or selecting a pre-loaded sample image by sample_name.
    """
    sample_name = request.form.get("sample_name")
    
    # Check if user requested an internal sample image
    if sample_name:
        sample_path = os.path.join(current_app.config["SAMPLE_FOLDER"], sample_name)
        if not os.path.exists(sample_path):
            return jsonify({
                "status": "error",
                "message": f"Ảnh mẫu '{sample_name}' không tồn tại."
            }), 404
            
        experiment_id = create_experiment_id()
        exp_upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], experiment_id)
        os.makedirs(exp_upload_dir, exist_ok=True)
        dest_path = os.path.join(exp_upload_dir, sample_name)
        
        import shutil
        shutil.copyfile(sample_path, dest_path)
        
        try:
            metadata = get_image_metadata(dest_path)
            return jsonify({
                "status": "success",
                "experiment_id": experiment_id,
                "filename": sample_name,
                "preview_url": f"/media/uploads/{experiment_id}/{sample_name}",
                "metadata": metadata
            }), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Lỗi đọc metadata ảnh mẫu: {str(e)}"
            }), 500

    # Normal user upload
    if "image" not in request.files:
        return jsonify({
            "status": "error",
            "message": "Không tìm thấy tệp đính kèm trong yêu cầu (key 'image')."
        }), 400
        
    file = request.files["image"]
    max_bytes = current_app.config.get("MAX_CONTENT_LENGTH", 20 * 1024 * 1024)
    max_pixels = current_app.config.get("MAX_IMAGE_PIXELS", 100_000_000)
    
    is_valid, error_msg, quick_summary = validate_image_file(
        file,
        max_size_bytes=max_bytes,
        max_pixels=max_pixels
    )
    if not is_valid:
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 400
        
    experiment_id = create_experiment_id()
    try:
        saved_path, safe_name = save_uploaded_file(
            file=file,
            upload_dir=current_app.config["UPLOAD_FOLDER"],
            experiment_id=experiment_id
        )
        metadata = get_image_metadata(saved_path)
        
        return jsonify({
            "status": "success",
            "experiment_id": experiment_id,
            "filename": safe_name,
            "preview_url": f"/media/uploads/{experiment_id}/{safe_name}",
            "metadata": metadata
        }), 200
    except Exception as exc:
        return jsonify({
            "status": "error",
            "message": f"Lỗi lưu trữ tệp: {str(exc)}"
        }), 500

