import json
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from celery.result import AsyncResult
from app.tasks.image_tasks import run_image_benchmark_task, execute_image_benchmark, get_experiment_store_path
from app.utils.file_manager import cleanup_experiment_folders

analysis_bp = Blueprint("analysis_bp", __name__)

@analysis_bp.route("/api/experiments", methods=["POST"])
def run_experiment():
    """
    POST /api/experiments
    Triggers Asynchronous Celery Task for complete Image Benchmark.
    Returns HTTP 202 Accepted with task_id.
    
    Payload (JSON):
    {
        "experiment_id": "<uuid>",
        "formats": ["JPEG", "PNG", "WEBP"],
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

    uploaded_files = [f for f in upload_dir.iterdir() if f.is_file() and not f.name.endswith(".gitkeep")]
    if not uploaded_files:
        return jsonify({"status": "error", "message": "Không tìm thấy tệp ảnh gốc trong phiên."}), 404

    requested_formats = data.get("formats", ["JPEG", "PNG", "WEBP"])
    requested_qualities = data.get("qualities", [25, 50, 75, 90])

    try:
        # Enqueue Celery Task asynchronously
        task = run_image_benchmark_task.delay(
            experiment_id=experiment_id,
            requested_formats=requested_formats,
            requested_qualities=requested_qualities
        )
        task_id = task.id

        return jsonify({
            "status": "accepted",
            "task_id": task_id,
            "experiment_id": experiment_id,
            "message": "Phiên thử nghiệm đã được đưa vào hàng đợi xử lý bất đồng bộ."
        }), 202

    except Exception as exc:
        current_app.logger.warning(f"Celery queue error: {exc}. Falling back to direct in-process execution...")
        try:
            # Fallback to direct synchronous execution in case Celery broker / Redis is unavailable
            execute_image_benchmark(
                experiment_id=experiment_id,
                requested_formats=requested_formats,
                requested_qualities=requested_qualities
            )
            return jsonify({
                "status": "accepted",
                "task_id": experiment_id,
                "experiment_id": experiment_id,
                "message": "Hoàn tất phân tích ảnh trực tiếp."
            }), 202
        except Exception as inner_exc:
            return jsonify({
                "status": "error",
                "message": f"Lỗi thực thi tác vụ thử nghiệm: {str(inner_exc)}"
            }), 500

@analysis_bp.route("/api/status/<task_id>", methods=["GET"])
def get_task_status(task_id: str):
    """
    GET /api/status/<task_id>
    Polls real-time execution state of asynchronous Celery task.
    Also checks file store for instant fallback if Redis/broker is offline.
    """
    exp_id_query = request.args.get("exp_id")

    # 1. Fast check: If experiment JSON file exists on disk, task completed!
    for check_id in [exp_id_query, task_id]:
        if check_id:
            store_file = get_experiment_store_path(check_id)
            if store_file.exists():
                try:
                    with open(store_file, "r", encoding="utf-8") as f:
                        result_data = json.load(f)
                    actual_exp_id = result_data.get("experiment_id", check_id)
                    return jsonify({
                        "state": "SUCCESS",
                        "percent": 100,
                        "status": "Hoàn tất thử nghiệm và phân tích dữ liệu!",
                        "experiment_id": actual_exp_id,
                        "redirect_url": f"/experiments/{actual_exp_id}",
                        "data": result_data
                    }), 200
                except Exception:
                    pass

    # 2. Query Celery AsyncResult safely using the app's configured Celery instance
    celery_instance = current_app.extensions.get("celery")
    try:
        task = AsyncResult(task_id, app=celery_instance)
        task_state = task.state
        task_info = task.info
        task_result = task.result if task_state == "SUCCESS" else None
    except Exception as exc:
        current_app.logger.warning(f"Error checking AsyncResult({task_id}): {exc}")
        # If Celery backend/Redis is unreachable, check all cached experiments in instance folder
        instance_dir = Path(current_app.instance_path) / "experiments"
        if instance_dir.exists():
            for f in instance_dir.glob("*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as jf:
                        jdata = json.load(jf)
                        found_id = jdata.get("experiment_id")
                        if found_id and (found_id == exp_id_query or found_id == task_id):
                            return jsonify({
                                "state": "SUCCESS",
                                "percent": 100,
                                "status": "Hoàn tất thử nghiệm!",
                                "experiment_id": found_id,
                                "redirect_url": f"/experiments/{found_id}",
                                "data": jdata
                            }), 200
                except Exception:
                    continue

        return jsonify({
            "state": "PROCESSING",
            "percent": 50,
            "status": "Đang xử lý phân tích dữ liệu..."
        }), 200

    if task_state == "PENDING":
        response = {
            "state": "PENDING",
            "status": "Đang xếp hàng chờ Worker xử lý...",
            "percent": 0
        }
    elif task_state == "PROGRESS":
        info = task_info or {}
        response = {
            "state": "PROCESSING",
            "percent": info.get("percent", 10),
            "status": info.get("status", "Đang xử lý nén và phân tích chất lượng..."),
            "current": info.get("current", 0),
            "total": info.get("total", 0)
        }
    elif task_state == "SUCCESS":
        result_data = task_result or {}
        exp_id = result_data.get("experiment_id", "")
        response = {
            "state": "SUCCESS",
            "percent": 100,
            "status": "Hoàn tất thử nghiệm và phân tích dữ liệu!",
            "experiment_id": exp_id,
            "redirect_url": f"/experiments/{exp_id}",
            "data": result_data
        }
    elif task_state in ("FAILURE", "REVOKED"):
        response = {
            "state": "FAILED",
            "percent": 0,
            "status": "Tác vụ thất bại trong quá trình thực thi.",
            "error": str(task_info)
        }
    else:
        response = {
            "state": task_state,
            "percent": 50,
            "status": str(task_info)
        }

    return jsonify(response), 200

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
