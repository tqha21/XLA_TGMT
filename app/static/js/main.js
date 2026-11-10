// ImageBench Core Frontend Engine

document.addEventListener("DOMContentLoaded", () => {
    // Determine which page we are on
    const resultsApp = document.getElementById("resultsApp");
    if (resultsApp) {
        initResultsPage(resultsApp.dataset.experimentId);
    } else {
        initUploadPage();
    }
});

/* ========================================================
   UPLOAD & SETUP WORKFLOW (index.html)
   ======================================================== */
function initUploadPage() {
    const dropzone = document.getElementById("dropzone");
    const imageInput = document.getElementById("imageInput");
    const uploadAlert = document.getElementById("uploadAlert");
    const uploadErrorText = document.getElementById("uploadErrorText");
    const previewContainer = document.getElementById("previewContainer");
    const previewPlaceholder = document.getElementById("previewPlaceholder");
    const previewImage = document.getElementById("previewImage");
    const startBenchmarkBtn = document.getElementById("startBenchmarkBtn");
    const processingBox = document.getElementById("processingBox");

    let currentExperimentId = null;

    function showAlert(msg) {
        uploadErrorText.textContent = msg;
        uploadAlert.classList.remove("d-none");
    }

    function hideAlert() {
        uploadAlert.classList.add("d-none");
    }

    function displayMetadata(data) {
        const meta = data.metadata;
        currentExperimentId = data.experiment_id;

        previewImage.src = data.preview_url;
        document.getElementById("metaFilename").textContent = meta.filename;
        document.getElementById("metaSize").textContent = meta.formatted_size;
        document.getElementById("metaDimensions").textContent = `${meta.width} x ${meta.height} px (${meta.megapixels} MP)`;
        document.getElementById("metaMode").textContent = `${meta.mode} (${meta.bit_depth})`;
        
        const alphaEl = document.getElementById("metaAlpha");
        if (meta.has_alpha) {
            alphaEl.innerHTML = '<span class="text-warning"><i class="fa-solid fa-triangle-exclamation me-1"></i>Có (Cần WebP/PNG)</span>';
        } else {
            alphaEl.innerHTML = '<span class="text-success"><i class="fa-solid fa-check me-1"></i>Không</span>';
        }
        document.getElementById("metaAspect").textContent = meta.aspect_ratio;

        previewPlaceholder.classList.add("d-none");
        previewContainer.classList.remove("d-none");
        previewContainer.classList.add("d-flex");
        startBenchmarkBtn.disabled = false;
        hideAlert();
    }

    // Direct Upload Handler
    async function uploadFile(file) {
        if (!file) return;
        hideAlert();
        
        const formData = new FormData();
        formData.append("image", file);

        startBenchmarkBtn.disabled = true;
        try {
            const resp = await fetch("/api/images/upload", {
                method: "POST",
                body: formData
            });
            const result = await resp.json();
            if (resp.ok && result.status === "success") {
                displayMetadata(result);
            } else {
                showAlert(result.message || "Tải ảnh thất bại.");
            }
        } catch (err) {
            showAlert("Lỗi mạng khi kết nối máy chủ: " + err.message);
        }
    }

    // Sample Image Select Handler
    document.querySelectorAll(".sample-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
            const sampleName = btn.dataset.sample;
            hideAlert();
            startBenchmarkBtn.disabled = true;
            
            const formData = new FormData();
            formData.append("sample_name", sampleName);
            
            try {
                const resp = await fetch("/api/images/upload", {
                    method: "POST",
                    body: formData
                });
                const result = await resp.json();
                if (resp.ok && result.status === "success") {
                    displayMetadata(result);
                } else {
                    showAlert(result.message || "Không thể tải ảnh mẫu.");
                }
            } catch (err) {
                showAlert("Lỗi tải ảnh mẫu: " + err.message);
            }
        });
    });

    // File Input & Drag/Drop
    if (imageInput) {
        imageInput.addEventListener("change", (e) => {
            if (e.target.files && e.target.files[0]) {
                uploadFile(e.target.files[0]);
            }
        });
    }

    if (dropzone) {
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropzone.classList.add("dragover");
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropzone.classList.remove("dragover");
            }, false);
        });

        dropzone.addEventListener("drop", (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files[0]) {
                uploadFile(files[0]);
            }
        });
    }

    // Launch Benchmark Execution
    if (startBenchmarkBtn) {
        startBenchmarkBtn.addEventListener("click", async () => {
            if (!currentExperimentId) return;

            const selectedFormats = Array.from(document.querySelectorAll(".format-checkbox:checked")).map(cb => cb.value);
            const selectedQualities = Array.from(document.querySelectorAll(".quality-checkbox:checked")).map(cb => parseInt(cb.value));

            if (selectedFormats.length === 0) {
                showAlert("Vui lòng chọn ít nhất 1 định dạng mục tiêu.");
                return;
            }
            if (selectedQualities.length === 0) {
                showAlert("Vui lòng chọn ít nhất 1 mức chất lượng nén.");
                return;
            }

            // Show processing status
            startBenchmarkBtn.disabled = true;
            processingBox.classList.remove("d-none");

            const taskProgressBar = document.getElementById("taskProgressBar");
            const taskPercentBadge = document.getElementById("taskPercentBadge");
            const processStatusText = document.getElementById("processStatusText");
            const taskDetailText = document.getElementById("taskDetailText");

            function updateProgressUI(percent, statusText, detailText) {
                if (taskProgressBar) taskProgressBar.style.width = `${percent}%`;
                if (taskPercentBadge) taskPercentBadge.textContent = `${percent}%`;
                if (processStatusText) processStatusText.textContent = statusText;
                if (taskDetailText && detailText) taskDetailText.textContent = detailText;
            }

            updateProgressUI(5, "Đang gửi yêu cầu vào hàng đợi Celery...", "Khởi tạo Task ID...");

            try {
                const resp = await fetch("/api/experiments", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        experiment_id: currentExperimentId,
                        formats: selectedFormats,
                        qualities: selectedQualities
                    })
                });
                const data = await resp.json();

                if (resp.status === 202 && data.task_id) {
                    // Start polling asynchronous Celery task status
                    const taskId = data.task_id;
                    const pollInterval = setInterval(async () => {
                        try {
                            const statusResp = await fetch(`/api/status/${taskId}`);
                            const statusData = await statusResp.json();

                            if (statusData.state === "PROCESSING") {
                                updateProgressUI(
                                    statusData.percent || 30,
                                    statusData.status || "Đang xử lý nén...",
                                    `Tiến trình: ${statusData.current || 0}/${statusData.total || 0}`
                                );
                            } else if (statusData.state === "SUCCESS") {
                                clearInterval(pollInterval);
                                updateProgressUI(100, "Hoàn tất thử nghiệm!", "Chuyển tiếp đến trang kết quả...");
                                setTimeout(() => {
                                    window.location.href = statusData.redirect_url || `/experiments/${currentExperimentId}`;
                                }, 500);
                            } else if (statusData.state === "FAILED") {
                                clearInterval(pollInterval);
                                processingBox.classList.add("d-none");
                                startBenchmarkBtn.disabled = false;
                                showAlert("Tác vụ xử lý ảnh thất bại: " + (statusData.error || "Lỗi không xác định"));
                            }
                        } catch (pollErr) {
                            // Transient network blip during polling, continue
                        }
                    }, 600);

                } else if (resp.ok && data.status === "success") {
                    // Synchronous fallback (if applicable)
                    window.location.href = `/experiments/${currentExperimentId}`;
                } else {
                    processingBox.classList.add("d-none");
                    startBenchmarkBtn.disabled = false;
                    showAlert(data.message || "Quá trình đánh giá thất bại.");
                }
            } catch (err) {
                processingBox.classList.add("d-none");
                startBenchmarkBtn.disabled = false;
                showAlert("Lỗi thực thi thử nghiệm: " + err.message);
            }
        });
    }
}

/* ========================================================
   RESULTS, COMPARISON & CHARTS WORKFLOW (results.html)
   ======================================================== */
async function initResultsPage(experimentId) {
    let experimentData = null;

    try {
        const resp = await fetch(`/api/experiments/${experimentId}/results`);
        const result = await resp.json();
        if (!resp.ok || result.status !== "success") {
            alert("Không tìm thấy kết quả thử nghiệm: " + (result.message || "Lỗi"));
            window.location.href = "/";
            return;
        }
        experimentData = result.data;
    } catch (err) {
        alert("Lỗi tải dữ liệu thử nghiệm: " + err.message);
        return;
    }

    // Set Header
    document.getElementById("headerImageName").textContent = `Kết Quả: ${experimentData.metadata.filename}`;

    // 1. Render Recommendations (FR-09)
    renderRecommendations(experimentData.recommendations);

    // 2. Render Image Comparison Setup (FR-07)
    setupImageComparison(experimentData);

    // 3. Render Chart Dashboard (FR-08)
    renderCharts(experimentData);

    // 4. Render Table
    renderResultsTable(experimentData);

    // 5. Delete handler
    const deleteBtn = document.getElementById("deleteExpBtn");
    if (deleteBtn) {
        deleteBtn.addEventListener("click", async () => {
            if (confirm("Bạn có chắc chắn muốn xóa toàn bộ ảnh và kết quả của phiên thử nghiệm này?")) {
                try {
                    await fetch(`/api/experiments/${experimentId}`, { method: "DELETE" });
                    window.location.href = "/";
                } catch (e) {
                    alert("Lỗi khi xóa: " + e.message);
                }
            }
        });
    }
}

/* Render Recommendations Cards */
function renderRecommendations(rec) {
    const container = document.getElementById("recommendationContainer");
    container.innerHTML = "";

    const cats = rec.categories || {};
    const items = [
        { key: "web", icon: "fa-globe", cls: "rec-web", titleColor: "text-success", ...cats.web },
        { key: "max_compression", icon: "fa-bolt-lightning", cls: "rec-saving", titleColor: "text-warning", ...cats.max_compression },
        { key: "archival", icon: "fa-gem", cls: "rec-archival", titleColor: "text-primary", ...cats.archival }
    ];

    items.forEach(item => {
        if (!item.title) return;
        const col = document.createElement("div");
        col.className = "col-md-4";
        col.innerHTML = `
            <div class="card rec-card ${item.cls} p-3 h-100 shadow-sm border border-slate-700">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="badge bg-dark-subtle text-white border border-slate-700 text-xxs px-2 py-1">
                        <i class="fa-solid ${item.icon} me-1 ${item.titleColor}"></i> ${item.badge}
                    </span>
                    <span class="fw-bold fs-6 text-white">${item.format} <span class="text-xs text-slate-400">Q${item.quality}</span></span>
                </div>
                <h6 class="fw-bold ${item.titleColor} text-xs uppercase mb-2">${item.title}</h6>
                <div class="d-flex justify-content-between text-xs text-slate-300 py-1 border-bottom border-slate-800">
                    <span>Dung lượng:</span> <b class="text-warning">${item.file_size} (-${item.saving_percent}%)</b>
                </div>
                <div class="d-flex justify-content-between text-xs text-slate-300 py-1 border-bottom border-slate-800">
                    <span>PSNR / SSIM:</span> <b>${item.psnr} / ${item.ssim}</b>
                </div>
                <p class="text-xxs text-slate-400 mt-2 mb-0">${item.reason}</p>
            </div>
        `;
        container.appendChild(col);
    });

    if (cats.transparency_note) {
        const noteCol = document.createElement("div");
        noteCol.className = "col-12 mt-2";
        noteCol.innerHTML = `
            <div class="alert alert-warning text-xs py-2 px-3 rounded-3 mb-0">
                <i class="fa-solid fa-triangle-exclamation me-1.5"></i> <b>${cats.transparency_note.title}:</b> ${cats.transparency_note.message}
            </div>
        `;
        container.appendChild(noteCol);
    }
}

/* Image Comparison UI (FR-07) */
function setupImageComparison(expData) {
    const originalUrl = expData.original_preview_url;
    const originalMeta = expData.metadata;
    const validResults = expData.results.filter(r => r.success);

    const compareSelect = document.getElementById("compareSelect");
    compareSelect.innerHTML = "";

    validResults.forEach((r, idx) => {
        const opt = document.createElement("option");
        opt.value = idx;
        opt.textContent = `${r.target_format} Q${r.quality} (${r.size_analysis.formatted_compressed} · SSIM: ${r.quality_metrics.ssim})`;
        compareSelect.appendChild(opt);
    });

    const compBeforeImg = document.getElementById("compBeforeImg");
    const compAfterImg = document.getElementById("compAfterImg");
    const sideOriginalImg = document.getElementById("sideOriginalImg");
    const sideTargetImg = document.getElementById("sideTargetImg");

    compBeforeImg.src = originalUrl;
    sideOriginalImg.src = originalUrl;
    document.getElementById("sideOriginalSize").textContent = originalMeta.formatted_size;

    function updateActiveTarget(index) {
        const target = validResults[index];
        if (!target) return;

        compAfterImg.src = target.url;
        sideTargetImg.src = target.url;

        // Metric Bar
        document.getElementById("activeTargetLabel").textContent = `${target.target_format} (Quality ${target.quality})`;
        document.getElementById("activeTargetSize").textContent = target.size_analysis.formatted_compressed;
        document.getElementById("activeTargetSaving").textContent = `${target.size_analysis.saving_percent}%`;
        document.getElementById("activeTargetPsnr").textContent = target.quality_metrics.psnr_display;
        document.getElementById("activeTargetSsim").textContent = target.quality_metrics.ssim;
        document.getElementById("activeTargetTime").textContent = `${target.encoding_time_ms} ms`;

        // Side by side indicators
        document.getElementById("sideTargetBadge").textContent = `${target.target_format} Q${target.quality}`;
        document.getElementById("sideTargetMetrics").textContent = `${target.size_analysis.formatted_compressed} (SSIM: ${target.quality_metrics.ssim})`;
    }

    if (validResults.length > 0) {
        updateActiveTarget(0);
    }

    compareSelect.addEventListener("change", (e) => {
        updateActiveTarget(parseInt(e.target.value));
    });

    // Slider Drag Logic
    const compContainer = document.getElementById("compContainer");
    const compOverlay = document.getElementById("compOverlay");
    const compSlider = document.getElementById("compSlider");

    let isSliding = false;
    function moveSlider(clientX) {
        const rect = compContainer.getBoundingClientRect();
        let x = clientX - rect.left;
        if (x < 0) x = 0;
        if (x > rect.width) x = rect.width;
        
        const percent = (x / rect.width) * 100;
        compOverlay.style.width = percent + "%";
        compSlider.style.left = percent + "%";
    }

    compContainer.addEventListener("mousedown", (e) => {
        isSliding = true;
        moveSlider(e.clientX);
    });
    window.addEventListener("mouseup", () => isSliding = false);
    window.addEventListener("mousemove", (e) => {
        if (!isSliding) return;
        moveSlider(e.clientX);
    });

    // Touch support for mobile/trackpad
    compContainer.addEventListener("touchstart", (e) => {
        isSliding = true;
        if (e.touches[0]) moveSlider(e.touches[0].clientX);
    });
    window.addEventListener("touchend", () => isSliding = false);
    window.addEventListener("touchmove", (e) => {
        if (!isSliding || !e.touches[0]) return;
        moveSlider(e.touches[0].clientX);
    });

    // Toggle Modes (Slider vs Side by side)
    const btnSlider = document.getElementById("btnModeSlider");
    const btnSide = document.getElementById("btnModeSide");
    const sliderContainer = document.getElementById("sliderModeContainer");
    const sideContainer = document.getElementById("sideModeContainer");

    btnSlider.addEventListener("click", () => {
        btnSlider.classList.add("active");
        btnSide.classList.remove("active");
        sliderContainer.classList.remove("d-none");
        sideContainer.classList.add("d-none");
    });

    btnSide.addEventListener("click", () => {
        btnSide.classList.add("active");
        btnSlider.classList.remove("active");
        sideContainer.classList.remove("d-none");
        sliderContainer.classList.add("d-none");
    });
}

/* Charts Dashboard (FR-08) */
function renderCharts(expData) {
    const validResults = expData.results.filter(r => r.success);
    const labels = validResults.map(r => `${r.target_format} Q${r.quality}`);

    const colors = {
        JPEG: 'rgba(239, 68, 68, 0.85)',
        PNG: 'rgba(59, 130, 246, 0.85)',
        WEBP: 'rgba(16, 185, 129, 0.85)',
        AVIF: 'rgba(168, 85, 247, 0.85)'
    };

    const getBgColor = (r) => colors[r.target_format] || 'rgba(148, 163, 184, 0.85)';

    // Chart 1: File Size
    const sizeCtx = document.getElementById('sizeChart').getContext('2d');
    new Chart(sizeCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Dung lượng (KB)',
                data: validResults.map(r => roundNum(r.file_size_bytes / 1024, 1)),
                backgroundColor: validResults.map(getBgColor),
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } }
            }
        }
    });

    // Chart 2: Rate-Distortion Curve (Size in KB vs PSNR)
    const rdCtx = document.getElementById('rdChart').getContext('2d');
    const rdData = validResults.map(r => ({
        x: roundNum(r.file_size_bytes / 1024, 1),
        y: r.quality_metrics.psnr > 100 ? 100 : r.quality_metrics.psnr,
        label: `${r.target_format} Q${r.quality}`
    }));

    new Chart(rdCtx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'PSNR (dB)',
                data: rdData,
                backgroundColor: validResults.map(getBgColor),
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.raw.label}: ${ctx.raw.x} KB, PSNR: ${ctx.raw.y} dB`
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: 'Dung lượng (KB)', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                y: { title: { display: true, text: 'PSNR (dB)', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
            }
        }
    });

    // Chart 3: SSIM Comparison
    const ssimCtx = document.getElementById('ssimChart').getContext('2d');
    new Chart(ssimCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'SSIM Score',
                data: validResults.map(r => r.quality_metrics.ssim),
                backgroundColor: 'rgba(16, 185, 129, 0.85)',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { min: 0.8, max: 1.0, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } }
            }
        }
    });

    // Chart 4: Encoding Time
    const timeCtx = document.getElementById('timeChart').getContext('2d');
    new Chart(timeCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Thời gian mã hóa (ms)',
                data: validResults.map(r => r.encoding_time_ms),
                backgroundColor: 'rgba(245, 158, 11, 0.85)',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } }
            }
        }
    });
}

/* Results Data Table */
function renderResultsTable(expData) {
    const tbody = document.getElementById("tableBody");
    tbody.innerHTML = "";

    const results = expData.results;
    document.getElementById("tableRowCount").textContent = `Tổng cộng ${results.length} cấu hình`;

    results.forEach(r => {
        const tr = document.createElement("tr");

        if (!r.success) {
            tr.innerHTML = `
                <td class="fw-bold text-slate-400 py-2 px-3">${r.target_format}</td>
                <td class="text-slate-400 py-2 px-2">Q${r.quality}</td>
                <td colspan="9" class="text-danger py-2 px-3"><i class="fa-solid fa-circle-xmark me-1"></i> ${r.error_message || "Chuyển đổi thất bại"}</td>
                <td class="text-end py-2 px-3">-</td>
            `;
            tbody.appendChild(tr);
            return;
        }

        const s = r.size_analysis;
        const q = r.quality_metrics;

        const savingBadge = s.saving_percent >= 0 
            ? `<span class="badge bg-success-subtle text-success text-xxs">-${s.saving_percent}%</span>`
            : `<span class="badge bg-danger-subtle text-danger text-xxs">+${Math.abs(s.saving_percent)}%</span>`;

        tr.innerHTML = `
            <td class="fw-bold text-white py-2 px-3">
                <span class="badge bg-slate-800 border border-slate-700 text-xs">${r.target_format}</span>
            </td>
            <td class="text-slate-300 py-2 px-2">Q${r.quality}</td>
            <td class="fw-semibold text-warning py-2 px-3">${s.formatted_compressed}</td>
            <td class="py-2 px-2">${savingBadge}</td>
            <td class="text-slate-300 py-2 px-2">${s.compression_ratio}x</td>
            <td class="text-slate-400 py-2 px-2">${s.bpp}</td>
            <td class="text-slate-400 py-2 px-2">${q.mse}</td>
            <td class="fw-semibold text-info py-2 px-2">${q.psnr_display}</td>
            <td class="fw-bold text-primary py-2 px-2">${q.ssim}</td>
            <td class="text-slate-300 py-2 px-2">${r.encoding_time_ms} ms</td>
            <td class="py-2 px-3"><span class="badge bg-dark border border-slate-700 text-slate-300 text-xxs">${q.quality_rating}</span></td>
            <td class="text-end py-2 px-3">
                <a href="${r.url}" download="${r.filename}" class="btn btn-outline-slate btn-sm py-0.5 px-2 text-xxs" title="Tải tệp ảnh này">
                    <i class="fa-solid fa-download"></i>
                </a>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function roundNum(num, dec) {
    return Math.round(num * Math.pow(10, dec)) / Math.pow(10, dec);
}

