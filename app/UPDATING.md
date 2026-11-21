# Cập nhật khi có văn bản thuế mới

Đổi văn bản luật cũng giống đổi domain. Báo cáo của đồ án đã chỉ ra rằng một AI chấm đúng trên dữ liệu này chưa chắc đúng trên dữ liệu khác. Vì vậy sau mỗi lần cập nhật đều phải **đo lại**, không chỉ thay số.

## Hằng tháng (hoặc khi có tin về chính sách thuế hộ kinh doanh)

1. **Tìm văn bản mới.**
   - Nguồn: Công báo (`congbao.chinhphu.vn`), mục Luật, Nghị quyết, Nghị định, Thông tư, Văn bản hợp nhất.
   - Từ khoá: "hộ kinh doanh", "cá nhân kinh doanh", "thuế giá trị gia tăng", "thuế thu nhập cá nhân".
   - Bài báo chỉ dùng để biết là có văn bản mới. Số liệu luôn lấy từ văn bản gốc.
2. **Tải văn bản gốc vào `data/tax/sources/`.**
   - Ưu tiên DOCX trên trang Công báo, sau đó tới PDF có lớp chữ.
   - Bản scan thì đặt tên `*.scan.pdf`, chép tay ra `.txt` và đối chiếu bằng OCR.
3. **Thêm vào `sources.json`:**
   - số hiệu, ngày ban hành
   - **hiệu lực, trích nguyên câu**
   - văn bản mà nó sửa đổi, thay thế hoặc hợp nhất
   - URL, sha256, `text_file`, `trich_dan`, `aliases`

   Văn bản hợp nhất thay cho văn bản gốc: để `text_file` cho bản hợp nhất, còn luật gốc và luật sửa đổi để `text_file: null` (chỉ giữ làm bằng chứng nguồn).
4. **Sửa đổi kiểu "thay cụm từ" hoặc "thay khoản"** khi chưa có bản hợp nhất: thêm vào `amendments.json`. `preprocess.py` sẽ dừng nếu cụm từ cần thay không có trong văn bản.
5. **Chạy `python app/preprocess.py --check`.** So số Điều với mục lục văn bản, mở vài bản ghi đọc đối chiếu.
6. **Sửa `rates.json`** nếu ngưỡng, tỷ lệ hoặc khoản giảm thay đổi:
   - Con số cũ chuyển vào `outdated_thresholds`, để lớp đối chiếu bắt được câu trả lời còn dùng số cũ.
   - Ghi khẳng định mới vào `VERIFICATION.md`, kèm câu gốc, trạng thái `ai`.
7. **Đổi `cutoff`** trong `rates.json`.
8. **Đo lại:**
   - `python app/eval_retrieval.py`: recall phải ≥ 0,90. Thêm câu hỏi cho phần luật mới vào `retrieval_eval.jsonl`.
   - `python -m pytest app/test_arbiter.py`: các cặp tin bẫy vẫn đúng. Tin bẫy nào dựa trên số liệu đã đổi thì sửa lại đáp án.
   - `python app/bench.py … --nolaw`: so với lần đo trước trong `results/bench.md`.
9. **Người kiểm chứng** đọc các dòng mới trong `VERIFICATION.md` và đổi trạng thái thành `nguoi`.

## Đang chờ

Xem `rates.json` → `pending`: các thay đổi đã được thông qua nhưng chưa có văn bản gốc trên Công báo.
