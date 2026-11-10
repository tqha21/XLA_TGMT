import os
from pathlib import Path
from flask import Blueprint, render_template, send_from_directory, current_app, abort, jsonify

main_bp = Blueprint("main_bp", __name__)

@main_bp.route("/")
def index():
    """Renders the upload and benchmark launch dashboard."""
    # List available sample images
    sample_dir = Path(current_app.config["SAMPLE_FOLDER"])
    samples = []
    if sample_dir.exists():
        for file in sample_dir.iterdir():
            if file.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}:
                samples.append({
                    "name": file.name,
                    "size_kb": round(file.stat().st_size / 1024, 1)
                })
                
    return render_template("index.html", samples=samples)

@main_bp.route("/experiments/<experiment_id>")
def view_results(experiment_id: str):
    """Renders the comprehensive visual results page for an experiment."""
    return render_template("results.html", experiment_id=experiment_id)

@main_bp.route("/media/uploads/<experiment_id>/<path:filename>")
def serve_upload(experiment_id: str, filename: str):
    """Safely serves uploaded source images."""
    folder = Path(current_app.config["UPLOAD_FOLDER"]) / experiment_id
    if not folder.exists():
        abort(404)
    return send_from_directory(folder, filename)

@main_bp.route("/media/outputs/<experiment_id>/<path:filename>")
def serve_output(experiment_id: str, filename: str):
    """Safely serves converted output images."""
    folder = Path(current_app.config["OUTPUT_FOLDER"]) / experiment_id
    if not folder.exists():
        abort(404)
    return send_from_directory(folder, filename)

@main_bp.route("/api/samples", methods=["GET"])
def list_samples():
    """Lists available test sample images."""
    sample_dir = Path(current_app.config["SAMPLE_FOLDER"])
    samples = []
    if sample_dir.exists():
        for file in sample_dir.iterdir():
            if file.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}:
                samples.append({
                    "name": file.name,
                    "size_bytes": file.stat().st_size
                })
    return jsonify({"status": "success", "samples": samples})

@main_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Docker & container orchestrator probes."""
    return jsonify({"status": "healthy", "service": "XLA_TGMT"}), 200

