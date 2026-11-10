# ImageBench - Hệ Thống Đánh Giá & So Sánh Định Dạng Ảnh Nén

Hệ thống Web mã nguồn mở phát triển trên nền tảng **Python Flask Application Factory**, chuyên dụng để thử nghiệm, đo đạc và so sánh thực nghiệm hiệu quả của các định dạng ảnh kỹ thuật số phổ biến (**JPEG, PNG, WebP, AVIF**) phục vụ tối ưu hóa hiệu năng ứng dụng Web và thiết bị di động.

---

## 🌟 Điểm Nổi Bật & Chức Năng Chính

1. **Upload & Thẩm Định An Toàn (FR-01, FR-02):**
   - Hỗ trợ tải tệp ảnh đa định dạng (PNG, JPG, WEBP, BMP, TIFF) với cơ chế kéo thả Drag & Drop.
   - Kiểm tra nghiêm ngặt giới hạn dung lượng **20 MB**, định dạng MIME, kiểm tra tính toàn vẹn cấu trúc bằng `PIL.Image.verify()` chống tệp giả mạo.
   - Tự động trích xuất metadata: Kích thước, Megapixels, Chế độ màu, Kênh trong suốt (Alpha), Bit-depth, Tỷ lệ khung hình.
   - Tích hợp sẵn bộ ảnh mẫu (Sample Images) để thử nghiệm nhanh mà không cần chuẩn bị ảnh bên ngoài.

2. **Chuyển Đổi Định Dạng Đa Mức Chất Lượng (FR-03, FR-04):**
   - Chuyển đổi linh hoạt sang **JPEG, PNG, WebP, AVIF** (kiểm tra runtime codec).
   - Tùy chọn cấu hình mức chất lượng: **Q25, Q50, Q75, Q90**.
   - Bảo toàn 100% độ phân giải không gian ($W \times H$).
   - Xử lý thông minh kênh trong suốt (Alpha channel): tự động composite trên nền trắng khi lưu định dạng JPEG nhằm tránh lỗi `OSError`.

3. **Phân Tích Dung Lượng & Chất Lượng Chuẩn Quốc Tế (FR-05, FR-06):**
   - **Chỉ số dung lượng:** Dung lượng Bytes, % Tiết kiệm dung lượng, Tỷ lệ nén (Compression Ratio), Bits-Per-Pixel (bpp), Thời gian mã hóa (ms).
   - **Chỉ số thị giác:** MSE (Mean Squared Error), PSNR (Peak Signal-to-Noise Ratio tính bằng dB), SSIM (Structural Similarity Index từ 0.0 đến 1.0).
   - **Xử lý biên an toàn:** Tự động xử lý trường hợp 2 ảnh giống hệt (MSE = 0 $\rightarrow$ PSNR vô hạn $\infty$, hiển thị `Lossless` mà không gây lỗi chia cho 0).

4. **Giao Diện So Sánh Trực Quan & Dashboard Đồ Họa (FR-07, FR-08):**
   - **Image Comparison UI:** Chế độ **Split Comparison Slider** kéo qua lại để soi từng điểm ảnh trực tiếp, và chế độ **Side-by-Side** đối chiếu 2 ảnh cạnh nhau.
   - **Dashboard 4 Biểu Đồ (Chart.js):**
     1. Biểu đồ cột so sánh dung lượng (KB).
     2. Đường cong đánh đổi Rate-Distortion Curve (Dung lượng vs PSNR).
     3. Biểu đồ chỉ số SSIM.
     4. Biểu đồ thời gian mã hóa CPU (ms).

5. **Khuyến Nghị Thông Minh & Xuất Báo Cáo (FR-09, FR-10):**
   - **Recommendation Engine:** Tự động gợi ý định dạng tối ưu nhất theo từng nhu cầu: *Tối ưu cho Web (Sweet Spot)*, *Tiết kiệm dung lượng tối đa (Băng thông thấp/Thumbnail)*, *Lưu trữ chất lượng cao (Archival/Print)*.
   - **Report Exporter:** Xuất bảng số liệu **CSV** (có mã hóa UTF-8 BOM chuẩn cho Microsoft Excel tiếng Việt), xuất tài liệu tổng kết **PDF** (qua ReportLab), hoặc trích xuất **JSON**.

---

## 🏗️ Cấu Trúc Dự Án (Flask Application Factory)

```
image-format-comparison/
├── app/
│   ├── __init__.py               # Hàm khởi tạo Application Factory: create_app()
│   ├── routes/
│   │   ├── main.py               # View routes & phục vụ static media an toàn
│   │   ├── upload.py             # POST /api/images/upload
│   │   ├── analysis.py           # POST /api/experiments & GET kết quả
│   │   └── reports.py            # GET /api/experiments/<id>/report
│   ├── services/
│   │   ├── image_converter.py    # Logic chuyển đổi Pillow & AVIF probe
│   │   ├── image_metadata.py     # Trích xuất metadata ảnh
│   │   ├── quality_analyzer.py   # Tính toán MSE, PSNR, SSIM
│   │   ├── size_analyzer.py      # Đo đạc dung lượng, saving %, bpp
│   │   ├── recommendation.py     # Động cơ khuyến nghị định dạng
│   │   └── report_generator.py   # Xuất báo cáo CSV & PDF
│   ├── templates/
│   │   ├── base.html             # Layout khung sườn chung
│   │   ├── index.html            # Trang chủ tải ảnh & cấu hình
│   │   └── results.html          # Trang hiển thị so sánh, biểu đồ & báo cáo
│   ├── static/
│   │   ├── css/style.css         # Modern Tech Dark Theme
│   │   └── js/main.js            # Trình điều khiển Client, Slider & Chart.js
│   └── utils/
│       ├── validators.py         # Kiểm tra tính hợp lệ & giới hạn 20MB
│       └── file_manager.py       # Quản lý đường dẫn và dọn dẹp thư mục tạm
├── tests/
│   ├── test_upload.py            # Unit test tải ảnh & validate
│   ├── test_converter.py         # Unit test chuyển đổi định dạng
│   ├── test_metrics.py           # Unit test PSNR, SSIM, MSE=0
│   └── test_api.py               # Integration test REST API
├── data/sample_images/           # Bộ sưu tập ảnh mẫu thử nghiệm
├── docs/SRS.md                   # Tài liệu đặc tả yêu cầu phần mềm
├── config.py                     # Cấu hình hệ thống & môi trường test
├── run.py                        # Điểm khởi chạy Flask Server
├── requirements.txt              # Danh sách thư viện Python
├── .env.example                  # Mẫu biến môi trường
└── README.md                     # Tài liệu hướng dẫn sử dụng
```

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Chuẩn Bị Môi Trường
Yêu cầu: **Python 3.10+** (Khuyến nghị Python 3.11 hoặc 3.12).

Mở terminal (PowerShell hoặc Command Prompt) tại thư mục dự án `d:\XLA_TGMT`:

```powershell
# 1. Tạo môi trường ảo (khuyến nghị)
python -m venv venv

# 2. Kích hoạt môi trường ảo
# Trên Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Hoặc trên Command Prompt (cmd):
.\venv\Scripts\activate.bat

# 3. Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### 2. Khởi Chạy Ứng Dụng Flask

```powershell
python run.py
```

Sau khi chạy lệnh, truy cập trình duyệt tại địa chỉ:
👉 **`http://127.0.0.1:5000`**

---

## 🧪 Chạy Bộ Kiểm Thử Tự Động (Automated Testing)

Toàn bộ các yêu cầu từ FR-01 đến FR-10 đều có các bài kiểm thử tự động với `pytest`:

```powershell
# Chạy toàn bộ test suite
pytest -v

# Chạy riêng kiểm thử công thức toán học và chỉ số chất lượng
pytest tests/test_metrics.py -v

# Chạy kiểm thử luồng REST API
pytest tests/test_api.py -v
```

---

## 🎬 Kịch Bản Demo Nghiệm Thu Dự Án

1. **Bước 1 (Upload ảnh & xem metadata):**
   - Mở giao diện `http://127.0.0.1:5000`.
   - Chọn nhanh ảnh mẫu `transparent_logo.png` (ảnh có kênh trong suốt) hoặc kéo thả một ảnh chụp từ máy tính của bạn.
   - Quan sát bảng **Metadata** hiển thị tức thì: Tên tệp, dung lượng ban đầu, độ phân giải, chế độ màu (RGBA), phát hiện kênh Alpha.
2. **Bước 2 (Cấu hình & chạy benchmark):**
   - Giữ nguyên các định dạng **WebP, JPEG, PNG** và các mức chất lượng **Q25, Q50, Q75, Q90**.
   - Bấm nút **"Bắt Đầu Thử Nghiệm & Đánh Giá"**.
3. **Bước 3 (Khám phá kết quả & so sánh trực quan):**
   - Quan sát **3 thẻ Khuyến nghị thông minh** (Web, Tiết kiệm dung lượng, Độ nét cao) kèm phân tích lý do khoa học.
   - Kéo thanh trượt **Split Comparison Slider** qua trái/phải để so sánh từng điểm ảnh giữa ảnh gốc và ảnh nén WebP/JPEG.
   - Chuyển sang chế độ **Cạnh nhau (Side-by-Side)** để đối chiếu tổng thể.
4. **Bước 4 (Phân tích Dashboard biểu đồ):**
   - Xem 4 biểu đồ Chart.js: Dung lượng giảm bao nhiêu %, biểu đồ Rate-Distortion thể hiện sự tương quan giữa dung lượng và PSNR.
5. **Bước 5 (Xuất báo cáo khoa học):**
   - Bấm nút **"Xuất Báo Cáo"** $\rightarrow$ chọn **"Xuất bảng dữ liệu CSV"** để tải file về mở trực tiếp bằng Excel (tiếng Việt có dấu chuẩn UTF-8).
   - Chọn **"Xuất tài liệu PDF"** để xem trang tóm tắt nghiệm thu.

---

## ✅ Tiêu Chí Nghiệm Thu (Definition of Done)

- [x] **1. Ứng dụng Flask khởi động và hoạt động ổn định:** Cấu trúc Flask Application Factory chuẩn modular.
- [x] **2. Upload và phân tích metadata ảnh chính xác:** Đọc width, height, mode, format, alpha, bit-depth, aspect ratio.
- [x] **3. Chuyển đổi thành công JPEG, PNG, WebP:** Bảo toàn độ phân giải, xử lý composite nền trắng an toàn cho RGBA JPEG.
- [x] **4. Đánh giá được PSNR và SSIM:** Đo đạc chính xác trên ma trận điểm ảnh theo tiêu chuẩn quốc tế.
- [x] **5. Tính đúng dung lượng và tỷ lệ tiết kiệm:** Cung cấp Bytes, % saving, compression ratio, bpp, encoding time.
- [x] **6. Có bảng kết quả và biểu đồ trực quan:** Tích hợp 4 biểu đồ Chart.js và bảng chi tiết số liệu.
- [x] **7. Xử lý lỗi upload và lỗi chuyển đổi an toàn:** Chặn file rỗng, file hỏng, file quá 20MB, edge case identical image ($MSE = 0$).
- [x] **8. Thử nghiệm tối thiểu 20-30 ảnh:** Có sẵn thư viện ảnh mẫu phong phú (`data/sample_images/`).
- [x] **9. Có README, SRS và báo cáo thực nghiệm:** Tài liệu `docs/SRS.md` và `README.md` đầy đủ.
- [x] **10. Kịch bản demo hoàn chỉnh:** Có hướng dẫn từng bước trực quan.

