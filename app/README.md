# Hộp thư thuế hộ kinh doanh

Trả lời câu hỏi về thuế của hộ kinh doanh, cá nhân kinh doanh tại Việt Nam, dựa trên văn bản pháp luật gốc có hiệu lực đến ngày cắt (`data/tax/rates.json` → `cutoff`). Mỗi câu trả lời ghi căn cứ (Điều, khoản, số hiệu văn bản) và đi qua ba lớp kiểm tra trước khi đến người hỏi.

```
câu hỏi ──► ngoài phạm vi (doanh nghiệp, tiền lương, bất động sản…) ──► từ chối, không gọi AI
   │
   ▼ tìm các khoản luật liên quan (BM25 trên articles.jsonl, + khoản cốt lõi)
   │   không khoản nào đủ khớp ──► "chưa đủ căn cứ", không gọi AI
   ▼
 2 mô hình soạn 2 bản nháp, chỉ dùng các khoản luật được đưa, bắt buộc dòng "Căn cứ:"
   ▼
 AI chấm so 2 bản nháp ở CẢ HAI thứ tự (arbiter.py) ── đổi ý khi đảo thứ tự ──► chưa chắc chắn
   ▼
 đối chiếu bằng luật (factcheck.py): ngưỡng cũ, thuế khoán/môn bài, tỷ lệ %, số tiền, phương pháp, trích dẫn
   │   mâu thuẫn ──► chưa chắc chắn
   ▼
 trả lời (người hỏi thấy câu trả lời + các khoản luật đã dùng, mở được văn bản gốc)
```

"Chưa chắc chắn": người hỏi **không thấy bản nháp chưa kiểm**, chỉ thấy các khoản luật liên quan và lý do. Bản nháp chỉ hiện ở chế độ người duyệt.

Đây là kết quả của đồ án (thiên vị vị trí của AI chấm) biến thành quy tắc định tuyến. Đồ án cho hai bài học:
- AI chấm đổi ý khi chỉ đổi thứ tự câu trả lời, nên phải chấm cả hai thứ tự.
- AI chấm nhất quán chưa chắc đã đúng: so với đáp án chuẩn thì tốt hơn. Ở đây, đáp án chuẩn chính là văn bản luật.

## Chạy

```
cp .env.example .env              # GROQ_API_KEY và/hoặc GEMINI_API_KEY
python app/server.py              # mở http://localhost:8010
python app/server.py --host 0.0.0.0 --port 8080 --max-wait 90
```

Yêu cầu Python 3.10+. Ứng dụng chỉ dùng thư viện chuẩn. Riêng `preprocess.py` cần `pdftotext` (poppler) khi văn bản nguồn là PDF.

Mỗi trình duyệt có một hộp thư riêng, nhận diện bằng cookie và lưu trong `data/state/` (không đưa lên git). Người này không thấy câu hỏi của người khác. Hệ thống tự che chuỗi giống mã số thuế hoặc số CCCD trước khi gửi cho nhà cung cấp AI. Mỗi phiên được hỏi tối đa 30 câu mỗi giờ.

**Hạn mức:** gói miễn phí của Groq cho 8.000 token mỗi phút, trong khi một lượt chấm có kèm khoản luật tốn khoảng 5.000 token. Vì vậy mỗi câu hỏi có thể phải chờ tới khoảng một phút (`--max-wait`). Khi có nhiều người dùng thật, cần dùng key trả phí.

## Dữ liệu (`data/tax/`)

| File | Vai trò | Ai sửa |
|---|---|---|
| `sources/` | Văn bản gốc tải từ Công báo hoặc cổng Chính phủ (DOCX, PDF, bản scan). Không sửa | Tải về |
| `sources.json` | Thông tin từng văn bản: số hiệu, hiệu lực (trích nguyên câu), văn bản sửa đổi hoặc hợp nhất, URL, sha256 | Tay |
| `amendments.json` | Văn bản sửa đổi được áp vào văn bản gốc (ví dụ NĐ 141 thay "500 triệu" bằng "01 tỷ" trong NĐ 68) | Tay |
| `articles.jsonl` | Mỗi dòng là một khoản luật đang có hiệu lực, kèm bản gốc nếu đã bị sửa | `preprocess.py` sinh ra |
| `rates.json` | Ngưỡng, tỷ lệ GTGT và TNCN theo nhóm ngành, khoản giảm thuế, chế độ đã bỏ, ngưỡng cũ. Mỗi số đều có trích dẫn | Tay |
| `VERIFICATION.md` | Nhật ký kiểm chứng: mỗi con số kèm câu gốc, trạng thái `ai` hoặc `nguoi` | Tay |
| `core.json` | Các khoản luôn đưa vào prompt (ngưỡng, phương pháp, tỷ lệ) | Tay |
| `synonyms.json` | Cách nói thường ngày → thuật ngữ trong luật ("bán online" → "thương mại điện tử") | Tay |
| `retrieval_eval.jsonl` | 30 câu hỏi kiểu người dùng, mỗi câu có khoản luật đúng, để đo tìm kiếm | Tay |
| `../tickets.json` | Câu hỏi bẫy cho chế độ trình bày: mỗi câu có một cặp bản nháp soạn sẵn, một bản sai đúng một chi tiết luật | Tay |

## Files

| File | Vai trò |
|---|---|
| `server.py` | Phiên theo trình duyệt, lọc phạm vi, gọi tìm kiếm, soạn, chấm, đối chiếu; API JSON |
| `retrieve.py` | BM25 theo âm tiết và cặp âm tiết, bảng đồng nghĩa, khoản cốt lõi; câu gõ không dấu tìm trên bản bỏ dấu |
| `arbiter.py` | Chấm hai thứ tự, gộp kết quả thành agree / tie / partial / flip / invalid |
| `factcheck.py` | Đối chiếu bản nháp với `rates.json` và các khoản đã đưa, bằng luật, không dùng AI |
| `preprocess.py` | Văn bản gốc → `articles.jsonl` |
| `eval_retrieval.py` | Đo recall của tìm kiếm trên `retrieval_eval.jsonl` |
| `bench.py` | Chạy tin bẫy qua các AI chấm: một lượt, đảo thứ tự, đảo thứ tự kèm đối chiếu; `--nolaw` đo AI chấm khi không có khoản luật |
| `test_arbiter.py` | Kiểm quy tắc định tuyến và lớp đối chiếu trên các cặp tin bẫy |
| `index.html` | Giao diện |
| `UPDATING.md` | Quy trình cập nhật khi có văn bản mới |

## Kiểm tra

```
python app/preprocess.py --check   # dựng lại articles.jsonl
python app/eval_retrieval.py       # mục tiêu recall >= 0,90
python -m pytest app/test_arbiter.py
python app/bench.py --judges groq-gpt-oss-20b,groq-gpt-oss-120b --repeats 3 --nolaw
```

## Giới hạn đã biết

- Mới có AI kiểm chứng số liệu (`VERIFICATION.md`, trạng thái `ai`). Cần người kiểm lại trước khi giới thiệu rộng.
- Chưa có văn bản của Bộ Tài chính xếp chi tiết ngành nghề vào nhóm tỷ lệ. Tỷ lệ GTGT cho nhóm "cho thuê tài sản, đại lý" và nhóm "nội dung số" đang để trống. Xếp một ngành cụ thể (quán ăn, cà phê…) vào nhóm nào là việc của AI soạn và AI chấm, lớp đối chiếu không quyết.
- Không tự tính thuế theo phương pháp thu nhập (doanh thu trừ chi phí): chỉ nhận ra trường hợp này và khuyên hỏi cơ quan thuế hoặc kế toán.
- Luật Quốc hội thông qua ngày 20/11/2026 (nâng mốc 03 tỷ lên 10 tỷ từ kỳ tính thuế 2027) chưa đăng Công báo, nên chưa đưa vào. Xem `rates.json` → `pending`.
