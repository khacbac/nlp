# Kế hoạch hoàn thiện đồ án

Ngày lập: 2026-11-19. Trạng thái hiện tại:

| Phần | Trạng thái |
|---|---|
| Proposal (`proposal.md`, `proposal.html` + slide trình chiếu 13 màn) | Xong |
| 500 câu hỏi UIT-ViQuAD (`experiment/data/questions.jsonl`) | Xong |
| 1500 câu trả lời từ Qwen, gpt-oss, Gemini | Xong (local, gitignore) |
| Grading sheets A–D + `key.csv` | Đã tạo; **người chấm chưa xong** (`ai_graded/` chỉ là bản AI chấm thử) |
| Judge chấm 2 chiều + logprob | **Chưa làm** |
| Phân tích 6 tiêu chí, kappa/alpha, baseline | **Chưa làm** |
| Demo flip (`demo.html`) | Có bản minh hoạ, chưa dùng dữ liệu thật |
| Báo cáo cuối kỳ + slide kết quả | **Chưa làm** |
| Đọc paper (`papers/`) | Bạn tự làm, mình không đụng vào |

## 1. Công cụ (MCP) dùng cho design và slide

### Đã có sẵn, dùng luôn (không cần cài)

| Công cụ | Dùng để | Vì sao chọn |
|---|---|---|
| **Artifact – Slides** | Deck kết quả cuối kỳ | Slide 16:9 chỉnh từng màn, tải về **.pptx / PDF**, có trang private để cả nhóm xem link |
| **Artifact – Design / Motion** | Hình minh hoạ, animation "đổi chỗ → flip" | Tự thiết kế trên canvas, xuất MP4 nhúng vào slide hoặc demo |
| **dataviz skill** | Mọi biểu đồ kết quả | Bảng màu kiểm định sẵn, sáng/tối đều đọc được |
| **argent (Chromium/CDP)** | Mở `demo.html`, `proposal.html`, deck trong Chrome, chụp màn hình để **tự kiểm tra** layout, màu, chữ tràn | Đã kết nối; giúp mình tự soát lỗi hiển thị thay vì đoán |
| **Google Slides / Drive** (đã kết nối) | Nếu nhóm muốn cùng sửa deck trên Google Slides | Thay thế khi thầy/nhóm yêu cầu Google Slides |

### Cần bạn đăng nhập (tuỳ chọn)

| Công cụ | Lợi ích | Nhược |
|---|---|---|
| **Canva MCP** | Kho template, ảnh stock, illustration có bản quyền | Cần auth; khó kiểm soát chi tiết, số liệu dễ sai khi chép tay |
| **Figma MCP** | Lấy design từ Figma ra code | Project không có file Figma, nên lợi ích thấp |

### Đã xem nhưng không đề xuất

- **Presentations.AI, Plus AI, SlideSpeak, 2slides**: tạo deck nhanh nhưng trả phí, template chung chung, và gửi nội dung đồ án ra dịch vụ ngoài.
- **Magic UI / shadcn MCP**: thư viện component React; project là HTML tĩnh nên không hợp.
- **MCP tạo ảnh AI**: chưa có server ổn định; hình ảnh khoa học nên là **SVG vẽ tay + biểu đồ thật**, chính xác và nhẹ hơn ảnh sinh.
- **Icon**: dùng Iconify/Lucide qua CDN hoặc nhúng SVG trực tiếp, không cần cài MCP riêng.

**Kết luận:** không cần cài thêm gì. Chỉ cần đăng nhập Canva nếu bạn muốn ảnh stock.

## 2. Các bước triển khai

### Bước 1. Judge chấm 2 chiều (`experiment/judge.py` + cell trong notebook Colab)

- Judge: **Qwen2.5-7B-Instruct** (vLLM, T4), **temperature 0**, prompt pairwise MT-Bench (giải thích trước, verdict ở cuối).
- 1500 cặp × 2 thứ tự = 3000 lần chấm. Lưu verdict + logprob của token verdict vào `judgments_vi.jsonl`; chạy lại được giữa chừng như `generate_answers.py`.
- Điều kiện tiếng Anh: dịch 500 câu (đoạn văn, câu hỏi, 3 câu trả lời) bằng Gemini/gpt-oss → `judgments_en.jsonl`.
- Kiểm tra nhanh trên 20 cặp ở local hoặc Colab trước khi chạy hết.
- **Bạn cần:** bấm chạy notebook trên Colab (khoảng 30–60 phút GPU).

### Bước 2. Phân tích (`experiment/analyze.py`)

- 6 tiêu chí: Flip Rate, First-Position Preference, Confidence Margin, Human Score Gap (flip rate theo bin), BPC so với người chấm, VI vs EN.
- Độ đồng thuận người chấm: Cohen's kappa từng cặp + Krippendorff's alpha.
- CI bằng bootstrap **theo câu hỏi** (vì 3 cặp cùng câu không độc lập); tách riêng các cặp có Qwen (self-enhancement).
- Baseline: word-overlap F1 và cosine sentence-embedding so với điểm người.
- Xuất `results/metrics.json` + biểu đồ SVG/PNG.
- Trong lúc chờ người chấm, chạy thử trên `ai_graded/` và **gắn nhãn rõ là dữ liệu thử**; khi điểm thật về chỉ cần chạy lại một lệnh.
- Chỉ giữ test cho phần tính toán dễ sai (map A/B về X/Y, đếm flip, BPC), theo quy tắc giữ test gọn.

### Bước 3. Demo với ví dụ thật (`demo.html`)

- Lấy 3–5 cặp flip thật (độ tự tin thấp, điểm người gần nhau) và 1 cặp không flip để đối chứng.
- Thêm animation hai thẻ đổi chỗ, thanh xác suất A/B của từng lần chấm.
- Kiểm tra bằng argent trên Chrome: màn hình máy chiếu, mobile, sáng/tối.

### Bước 4. Báo cáo cuối kỳ

- `report.md` theo cấu trúc: Introduction, Related Work (từ `papers/matrix.md`), Method, Results, Discussion, Limitations, References.
- Xuất PDF; có thể đưa lên Claude Docs nếu nhóm muốn cùng sửa và comment.
- Phần Related Work dùng các thẻ đọc bạn đang hoàn thiện; chỗ chưa kiểm chứng sẽ đánh dấu `TODO` để bạn soát.

### Bước 5. Slide kết quả (Artifact Slides)

- Khoảng 12–15 màn, giữ cùng hệ màu và font với `proposal.html` (Be Vietnam Pro, X xanh / Y vàng / flip hồng).
- Mạch kể: câu chuyện cô Hoa → câu hỏi → cách làm → **4 kết quả, mỗi RQ một màn có 1 biểu đồ chính** → khuyến nghị → hạn chế → demo.
- Ghi chú người nói cho từng màn (cập nhật `presentation-script.md`), tải về .pptx + PDF làm bản dự phòng.
- Soát bằng argent: chụp từng màn, kiểm tra chữ tràn, độ tương phản, số liệu khớp `metrics.json`.

### Bước 6. Hoàn tất

- Cập nhật `README`/`experiment/README.md`, commit theo từng bước (không push nếu bạn không yêu cầu).
- Không commit dữ liệu lộ model (answers, sheets, key, judgments có tên model).

## 3. Phụ thuộc vào bạn / nhóm

| Việc | Ai | Chặn bước nào |
|---|---|---|
| Chạy notebook judge trên Colab | Bạn | 2, 3, 5 (số liệu thật) |
| 4 người chấm xong sheet A–D | Nhóm | Kết quả RQ2, RQ4, kappa (trước đó dùng bản AI thử) |
| Đọc paper, sửa thẻ | Bạn | Chỉ phần Related Work của báo cáo |

## 4. Quyết định đã chốt (2026-11-19)

1. Prompt judge **giữ lựa chọn hoà `[[C]]`** như MT-Bench; độ tự tin tính từ xác suất A/B đã chuẩn hoá lại.
2. Điều kiện tiếng Anh **để sau**: làm phần tiếng Việt trước, code vẫn để sẵn tham số ngôn ngữ.
3. Slide kết quả dùng **Artifact Slides**.
4. Còn mở: định dạng/độ dài báo cáo, thời lượng thuyết trình, hạn nộp. Tạm theo cấu trúc ở Bước 4 và khoảng 10 phút.

## 5. Phát hiện khi chạy judge (2026-11-19)

- Judge chạy đủ 3000 lần chấm, 0 lỗi format. **86% lần chấm ghi verdict trước rồi mới giải thích**, nên giả định "prompt MT-Bench đã đáp ứng MEC" trong `papers/matrix.md` không đúng với Qwen2.5-7B. Cần ghi vào báo cáo.
- Judge thiên vị gpt-oss rõ (thắng 67% theo BPC) và thích câu dài hơn (69%). Judge thấy text gốc có `**in đậm**` của gpt-oss, còn người chấm thấy bản đã bỏ. **Thí nghiệm phụ nên chạy:** judge lại trên text đã bỏ in đậm (`strip_emphasis`) để tách hiệu ứng định dạng.
- RQ1 và RQ3 không cần điểm người nên đã là số cuối. RQ2 và RQ4 đang chạy trên điểm AI (TRIAL), chạy lại `python analyze.py` khi người chấm xong.

## 6. Trạng thái (2026-11-19, cuối ngày)

| Bước | Kết quả |
|---|---|
| 1–2 Judge + phân tích | Xong. `experiment/results/` (metrics, summary, 4 biểu đồ) |
| 3 Demo | Xong. `demo.html` dùng 3 cặp thật và số liệu toàn bộ 500 câu |
| 4 Báo cáo | Xong bản nháp đầy đủ: `report.md` (~4.400 từ, tiếng Anh) |
| 5 Slide | Xong 14 slide (Artifact Slides), có ghi chú người nói cho từng slide |

Lưu ý: điểm người chấm hiện lấy từ `data/ai_graded/`. Khi có sheet chấm của nhóm, chạy `python analyze.py` rồi cập nhật số trong báo cáo, demo và slide.
