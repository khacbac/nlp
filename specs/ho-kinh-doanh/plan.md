# Plan: Hộp thư tư vấn thuế hộ kinh doanh

Ngày lập: 2026-11-21.

## Tiến độ (cập nhật 21/11/2026)

| Bước | Trạng thái |
|---|---|
| 0. Xoá shop cờ | Xong |
| 1. Kho văn bản | Xong. 17 văn bản chính thức trong `sources.json`. 28 khẳng định trong `VERIFICATION.md` ở trạng thái `ai`, **chờ người kiểm** |
| 2. `preprocess.py` | Xong: 402 khoản luật, tự áp NĐ 141 lên NĐ 68, đã đối chiếu với OCR của VBHN 25 |
| 3. Tìm kiếm | Xong: recall 0,97 trên 30 câu (gồm câu gõ không dấu); chặn câu lạc đề bằng ngưỡng "ít nhất 2 cụm từ luật" |
| 4. Soạn trả lời, lọc phạm vi | Xong |
| 5. Lớp đối chiếu thuế | Xong: 6 kiểm tra |
| 6. Tin bẫy, test, bench | 13 tin bẫy, 26 test qua; bench thật đang chạy (Groq free tier: 8.000 token/phút, phải chờ) |
| 7. Giao diện | Xong (agent viết, đã kiểm bằng curl và Chrome headless). Đã sửa 4 vấn đề backend agent phát hiện |
| 8. Tài liệu | README, UPDATING xong; DEMO chờ bench |
| B. Dùng thật | Đã có: phiên riêng theo trình duyệt, che MST/CCCD, giới hạn 30 câu/giờ, nút phản hồi. Còn lại: nơi triển khai, key trả phí, tách `llm.py` khỏi `experiment/` |

Việc tồn: câu "Bán online không có cửa hàng thì nộp thuế ở cơ quan thuế nào?" vẫn chưa tìm ra khoản 4 Điều 8 NĐ 68.

## Platform

Backend + web frontend nhỏ: Python chỉ dùng thư viện chuẩn (`app/server.py`) và một trang HTML (`app/index.html`). Không có mobile.

## Overview

Thay demo shop cờ trong `app/` bằng một hộp thư hỏi đáp về **thuế của hộ và cá nhân kinh doanh** ở Việt Nam. Hệ thống trả lời theo văn bản có hiệu lực đến một ngày cắt cố định. Có hai mục đích:

1. **Demo cho đồ án.** Mạch của demo: judge không có văn bản tham chiếu sẽ chọn câu trả lời dùng số liệu cũ; chấm hai thứ tự chỉ bắt được lỗi do vị trí; đối chiếu với văn bản và con số mới bắt được lỗi nhất quán nhưng sai.
2. **Sản phẩm dùng thật** cho chính nhóm và cho người dùng khác. Văn bản thuế thì nhiều, khó đọc, khó tìm. Hệ thống tìm đúng Điều, trả lời có trích dẫn, và từ chối khi không đủ căn cứ.

Lõi hiện tại được giữ nguyên: hai model soạn trả lời, judge chấm hai thứ tự (`arbiter.py`), lớp đối chiếu bằng luật (`factcheck.py`). Phần thêm mới:
- kho văn bản đã kiểm chứng: `sources.json`, `articles.jsonl`, `rates.json`
- tìm kiếm BM25
- lớp đối chiếu riêng cho thuế
- những phần cần có khi dùng thật: trích dẫn, ngày cắt, tuyên bố miễn trừ, tách dữ liệu theo người dùng, quy trình cập nhật văn bản

## Assumptions

- **Đối tượng: chỉ hộ và cá nhân kinh doanh, chỉ phương pháp doanh thu × tỷ lệ.** Không làm doanh nghiệp, không tính theo phương pháp thu nhập − chi phí. Gặp các trường hợp này thì từ chối và giải thích lý do. *Lý do: các con số kiểm chứng được và tính được bằng code; phạm vi càng rộng càng dễ sai.*
- **Nhóm ngành: giữ đủ bảng tỷ lệ.** *Lý do: bảng chỉ có khoảng 5 dòng; chỗ khó là xếp hộ vào nhóm nào, việc này để cho model và tin bẫy.*
- **Ngày cắt mặc định: 30/11/2026.** Hiện trên giao diện và trong mọi câu trả lời. *Lý do: quy định năm 2026 đổi nhiều lần (NQ 198/2025, NĐ 68/2026, NĐ 141/2026, có thể còn NĐ 398/2026).*
- **Chỉ dùng văn bản gốc** từ Cổng Pháp luật quốc gia (`phapluat.gov.vn` / `vbpl.vn`), Công báo hoặc `chinhphu.vn`. Không lấy số liệu từ blog. *Lý do: khi tìm kiếm, các bài tổng hợp ghi mâu thuẫn nhau (ngưỡng 500 triệu hay 1 tỷ).*
- **Được commit văn bản gốc vào repo public.** Văn bản quy phạm pháp luật không thuộc đối tượng bảo hộ quyền tác giả (Luật SHTT, Điều 15). *Cần xác nhận lại trước khi commit.*
- **Thay hẳn shop cờ ngay trong `app/`, xoá sạch mọi dấu vết** (dữ liệu, ảnh, kịch bản demo, kết quả bench, test, chữ trên giao diện). Không gắn tag; bản cũ vẫn còn trong lịch sử git (commit `5b5ce89`). *Lý do (quyết định ngày 21/11/2026): tránh nhầm lẫn về sau; dùng lại được `arbiter.py`, `llm.py`, `bench.py` và khung giao diện hộp thư.*
- **Đây là sản phẩm dùng thật, không chỉ là demo.** Không có hạn chót; Giai đoạn B nằm trong phạm vi. Ưu tiên đúng và bền hơn nhanh.
- **AI kiểm chứng trước, người kiểm chứng sau.** Khi làm, AI đối chiếu từng con số với văn bản gốc (trích nguyên câu), ghi vào nhật ký kiểm chứng với trạng thái `ai`. Người kiểm chứng thủ công sau, đổi trạng thái thành `nguoi`. Giao diện hiện rõ con số nào mới chỉ được AI kiểm.
- **Không dùng embedding hay vector DB.** BM25 + các Điều cốt lõi + bảng đồng nghĩa. *Lý do: không phụ thuộc thư viện ngoài, không tốn lượt gọi API, giải thích được vì sao chọn Điều nào.* Chỉ đổi nếu bộ câu hỏi đánh giá tìm kiếm (Bước 3.4) cho thấy BM25 trượt nhiều.
- **Câu trả lời bị giữ lại** (judge đổi ý, hoặc lớp đối chiếu phát hiện sai): người dùng thật **không thấy bản nháp**. Họ thấy các Điều liên quan (văn bản luật luôn đúng), lý do hệ thống chưa chắc chắn, và gợi ý hỏi cơ quan thuế. Bản nháp chỉ hiện ở chế độ người duyệt và chế độ trình bày. *Lý do: một bản nháp sai về thuế mà gửi cho người dùng thật thì có thể khiến họ nộp sai.*
- **Phần lưu kho và phần cam kết đúng là hai phạm vi khác nhau.** `articles.jsonl` chứa toàn bộ văn bản đã tải. `rates.json`, `factcheck` và tin bẫy chỉ cam kết cho phạm vi ở trên.

## Affected Areas

| File | Thay đổi |
|---|---|
| `app/data/policy.md`, `products.json`, `tickets.json` (bản shop), `state.json`, `static/products/`, trang `/nguon-anh`, `results/bench.*` | Xoá hết |
| `app/data/tax/VERIFICATION.md` | **Mới.** Nhật ký kiểm chứng: mỗi con số → câu gốc trong văn bản, người/AI kiểm, ngày kiểm, trạng thái `ai` / `nguoi` |
| `app/data/tax/sources/` | **Mới.** File gốc PDF/DOCX, không sửa |
| `app/data/tax/sources.json` | **Mới.** Thông tin từng văn bản và quan hệ sửa đổi giữa các văn bản |
| `app/data/tax/articles.jsonl` | **Mới,** do script sinh ra. Mỗi dòng là một Điều hoặc Khoản |
| `app/data/tax/amendments.json` | **Mới,** chép tay. Điều nào bị Điều nào sửa hoặc thay thế (khi không có văn bản hợp nhất) |
| `app/data/tax/rates.json` | **Mới,** chép tay. Ngưỡng, tỷ lệ theo nhóm ngành, điều kiện áp dụng phương pháp, các con số đã hết hiệu lực. Mỗi số có trích dẫn |
| `app/data/tax/synonyms.json` | **Mới.** Từ người dùng hay nói → thuật ngữ trong luật |
| `app/data/tax/core.json` | **Mới.** Danh sách id các Điều luôn đưa vào prompt |
| `app/preprocess.py` | **Mới.** Văn bản gốc → `articles.jsonl` (lấy text, chuẩn hoá NFC, tách Điều/Khoản/Điểm, gắn thời gian hiệu lực) |
| `app/retrieve.py` | **Mới.** BM25 (âm tiết + bigram), mở rộng câu hỏi bằng bảng đồng nghĩa, ghép thêm Điều cốt lõi, ngưỡng điểm "không đủ căn cứ" |
| `app/factcheck.py` | **Viết lại cho thuế.** Bỏ phần tồn kho và giá. Giữ `gate()` và cách viết theo luật, không dùng LLM |
| `app/server.py` | Prompt mới (bắt buộc trích dẫn, từ chối khi ngoài phạm vi); gọi `retrieve` trước khi soạn; lưu các Điều đã tìm được vào ticket; tách hộp thư theo người dùng (Giai đoạn B) |
| `app/arbiter.py` | Không đổi |
| `app/llm.py` | Không đổi ở Giai đoạn A. Giai đoạn B tách phụ thuộc vào `experiment/` (đang import `generate_answers`, `judge`) |
| `app/index.html` | Đổi giao diện sang thuế; hiện các Điều đã dùng kèm trích dẫn; banner ngày cắt và tuyên bố miễn trừ; màn "chưa chắc chắn" cho người dùng; bỏ thẻ sản phẩm |
| `app/data/tickets.json` | Viết lại: tin bẫy thuế (có `canned`, `answer`, `reserve`) và tin thường |
| `app/bench.py` | Đổi nguồn dữ liệu sang thuế, giữ 5 chế độ chấm; thêm một chế độ judge **không có văn bản** để đo Màn 1 |
| `app/test_arbiter.py` | Cập nhật test factcheck theo tin bẫy thuế; thêm test cho phép tính thuế |
| `app/eval_retrieval.py` + `app/data/tax/retrieval_eval.jsonl` | **Mới.** Khoảng 30 câu hỏi, mỗi câu có danh sách Điều đúng; đo recall@k |
| `app/README.md`, `app/DEMO.md` | Viết lại |

## Implementation Steps

### Giai đoạn A: dùng được và demo được

#### Bước 0: chuẩn bị

- [ ] Xoá toàn bộ dữ liệu và chữ liên quan tới shop trong `app/` (xem Affected Areas). Đã rà: ngoài `app/` chỉ có tên nhóm "ABNQ" trong báo cáo, giữ nguyên.
- [ ] Ngày cắt: 30/11/2026; khi có văn bản mới thì cập nhật theo quy trình ở Giai đoạn B.

#### Bước 1: kho văn bản. Phần quan trọng nhất, làm tay và kiểm chứng

- [ ] Lập danh sách văn bản cần tải, xác nhận từng văn bản trên cổng chính thức (không lấy theo bài tổng hợp):
  - NQ 198/2025/QH15 (bỏ thuế khoán, bỏ lệ phí môn bài từ 01/01/2026)
  - Luật Thuế TNCN 109/2025/QH15, Luật 09/2026/QH16 sửa đổi, VBHN 112/VBHN-VPQH (nếu có)
  - Luật Thuế GTGT hiện hành, phần áp dụng cho hộ kinh doanh
  - NĐ 68/2026/NĐ-CP, NĐ 141/2026/NĐ-CP (ngưỡng 500 triệu → 1 tỷ)
  - Kiểm tra có NĐ 398/2026/NĐ-CP không (giảm 30% thuế TNCN; mới thấy ở một nguồn)
  - Thông tư hướng dẫn kê khai cho hộ kinh doanh năm 2026; phụ lục danh mục ngành nghề và tỷ lệ
  - Văn bản về hoá đơn điện tử, máy tính tiền cho hộ kinh doanh (nếu có trong phạm vi)
  - Văn bản cũ để đánh dấu hết hiệu lực và làm nguồn cho tin bẫy: TT 40/2021/TT-BTC, quy định ngưỡng 100 triệu, quy định thuế khoán
- [ ] Tải file gốc vào `app/data/tax/sources/`. Ưu tiên DOCX hoặc HTML, PDF có lớp chữ; bản scan thì OCR và soát tay.
- [ ] Viết `sources.json`, mỗi văn bản gồm: `id`, `so_hieu`, `ten`, `co_quan`, `ngay_ban_hanh`, `hieu_luc_tu`, `hieu_luc_den`, `sua_doi`, `thay_the`, `url_goc`, `file`, `sha256`, `ngay_tai`, `nguoi_kiem`, `ngay_kiem`.
- [ ] **Dựng dòng thời gian hiệu lực** (văn bản nào sửa văn bản nào, từ ngày nào). Đặc biệt kiểm điều khoản chuyển tiếp: ngưỡng 1 tỷ có áp dụng hồi tố từ 01/01/2026 không, và hộ đã nộp theo ngưỡng 500 triệu thì xử lý ra sao.
- [ ] Đọc văn bản gốc và chép tay `rates.json`:
  - `cutoff`
  - `threshold`: ngưỡng doanh thu không phải nộp thuế
  - `groups`: mỗi nhóm ngành có `gtgt`, `tncn`, ví dụ ngành
  - `methods`: các mốc doanh thu bắt buộc hoặc được chọn phương pháp tính theo thu nhập
  - `abolished`: thuế khoán, lệ phí môn bài
  - `outdated`: các con số từng đúng (100 triệu, 500 triệu, tỷ lệ cũ nếu có thay đổi), kèm ngày hết hiệu lực

  Mọi con số có trường `cite` (văn bản, Điều, Khoản).
- [ ] **AI kiểm chứng:** với mỗi con số trong `rates.json` và mỗi đáp án tin bẫy, trích nguyên câu trong văn bản gốc vào `VERIFICATION.md`, kiểm cả điều khoản hiệu lực và chuyển tiếp, kiểm xem có văn bản nào sau đó sửa Điều đó không. Trạng thái `ai`.
- [ ] **Người kiểm chứng (làm sau):** đọc `VERIFICATION.md`, đối chiếu từng dòng, đổi trạng thái thành `nguoi`. Trước khi xong bước này, giao diện ghi "số liệu đang chờ người kiểm chứng".

#### Bước 2: tiền xử lý thành `articles.jsonl`

- [ ] `app/preprocess.py`:
  - lấy text: DOCX dùng `zipfile` + XML; HTML dùng `html.parser`; PDF thì chuyển sang text trước, chấp nhận dùng công cụ ngoài một lần, chỉ trong bước tiền xử lý
  - chuẩn hoá `unicodedata.normalize("NFC")`
  - tách theo regex `^Điều \d+\.`, `^\d+\.`, `^[a-zđ]\)`
  - gắn `hieu_luc_tu` và `hieu_luc_den` từ `sources.json`
- [ ] Mỗi bản ghi gồm: `id` (ví dụ `nd-141-2026:d1:k2`), `doc`, `dieu`, `khoan`, `diem`, `tieu_de`, `text`, `hieu_luc_tu`, `hieu_luc_den`, `superseded_by`, `core`.
- [ ] Áp `amendments.json`: Điều nào đã bị sửa thì gắn `superseded_by`, và lúc tìm kiếm không đưa bản cũ vào prompt. Nếu có văn bản hợp nhất thì dùng văn bản hợp nhất.
- [ ] Phụ lục danh mục ngành nghề tách thành từng dòng ngành để BM25 tìm theo tên ngành được.
- [ ] Soát tay: đếm số Điều mỗi văn bản so với mục lục, mở ngẫu nhiên 10 bản ghi đọc đối chiếu.

#### Bước 3: tìm kiếm

- [ ] `app/retrieve.py`:
  - tokenize theo âm tiết (lowercase, NFC) cộng bigram âm tiết
  - BM25 (`k1=1.5`, `b=0.75`) trên các bản ghi còn hiệu lực
  - mở rộng câu hỏi bằng `synonyms.json`
  - trả về top-k (k≈8) cộng các Điều trong `core.json`, kèm điểm và các từ đã khớp (để hiện trên giao diện)
- [ ] `synonyms.json`, khoảng 20–40 dòng, ví dụ:
  - "bán online", "bán hàng qua mạng" → "kinh doanh trên nền tảng thương mại điện tử"
  - "quán ăn", "quán cà phê" → "dịch vụ ăn uống"
  - "khoán" → "phương pháp khoán"
  - "không phải đóng thuế" → "không phải nộp thuế"
- [ ] Ngưỡng **"không đủ căn cứ"**: nếu điểm của kết quả tốt nhất thấp hơn ngưỡng thì không soạn trả lời, chuyển thẳng sang câu "không tìm thấy căn cứ".
- [ ] `retrieval_eval.jsonl`: khoảng 30 câu hỏi do người viết (kiểu người dùng hỏi thật, có tiếng lóng và viết thiếu dấu), mỗi câu có danh sách Điều đúng. `eval_retrieval.py` in recall@8. **Mục tiêu ≥ 90%** trước khi sang Bước 4. Không đạt thì bổ sung đồng nghĩa hoặc Điều cốt lõi; vẫn không đạt thì xem xét embedding.

#### Bước 4: soạn trả lời và kiểm tra phạm vi

- [ ] Lọc phạm vi trước khi soạn, bằng luật đơn giản: câu hỏi có "công ty", "doanh nghiệp", "TNHH", "cổ phần", "quyết toán TNDN", ... thì trả lời ngoài phạm vi ngay, không gọi model.
- [ ] Viết lại `WRITER_SYSTEM`: chỉ dựa trên các Điều được cung cấp; **bắt buộc dòng cuối có dạng `Căn cứ: Điều X Khoản Y, <số hiệu>`**; nếu hộ thuộc diện tính theo thu nhập − chi phí, hoặc không đủ căn cứ, thì nói rõ và khuyên hỏi cơ quan thuế; nêu ngày cắt; tối đa khoảng 150 từ; văn bản thuần.
- [ ] Viết lại `JUDGE_QUESTION`: đưa cùng các Điều đã tìm được vào prompt của judge. Giữ nguyên prompt MT-Bench, giống thí nghiệm.
- [ ] Ticket lưu thêm `retrieved` (id Điều + điểm) để giao diện và bench dùng lại.

#### Bước 5: lớp đối chiếu cho thuế (`factcheck.py`)

Mỗi kiểm tra trả về một ghi chú tiếng Việt ngắn, giữ cách viết theo luật như hiện tại:

- [ ] **Số đã hết hiệu lực:** câu trả lời nêu một giá trị trong `rates.outdated` (ví dụ ngưỡng 100 hoặc 500 triệu) như quy định hiện hành → gắn cờ.
- [ ] **Chế độ đã bãi bỏ:** nói thuế khoán hoặc lệ phí môn bài vẫn áp dụng (không có phủ định trong cùng câu) → gắn cờ.
- [ ] **Tỷ lệ hợp lệ:** % trong câu trả lời không thuộc bảng tỷ lệ → gắn cờ. Câu trả lời tự nêu một nhóm ngành nhưng áp tỷ lệ của nhóm khác → gắn cờ.
- [ ] **Tự tính số thuế:** khi biết doanh thu (đọc từ câu hỏi bằng regex "X triệu", "X tỷ") và biết nhóm ngành (từ ticket bẫy, hoặc nhóm mà câu trả lời tự nêu) → tính số thuế đúng theo `rates.json`, so với số tiền trong câu trả lời, cho sai số làm tròn.
- [ ] **Áp sai phương pháp:** doanh thu thuộc mốc phải tính theo thu nhập mà câu trả lời lại tính doanh thu × tỷ lệ → gắn cờ.
- [ ] **Trích dẫn:** thiếu dòng `Căn cứ:`, hoặc trích một Điều không có trong `retrieved` hay đã hết hiệu lực → gắn cờ. Đây là kiểm tra quan trọng nhất khi dùng thật.
- [ ] Giữ nguyên `gate()`.

#### Bước 6: tin bẫy và đo lường

- [ ] Viết lại `tickets.json`: khoảng 12 tin bẫy (cặp câu soạn sẵn, dài bằng nhau, chỉ khác một chi tiết) và khoảng 6 tin thường. Các loại bẫy:
  - ngưỡng cũ (100 triệu, 500 triệu) và ngưỡng mới 1 tỷ
  - "vẫn nộp thuế khoán" hoặc "vẫn nộp môn bài"
  - xếp sai nhóm ngành (ví dụ quán cà phê áp 1% thay vì tỷ lệ đúng)
  - áp doanh thu × tỷ lệ cho hộ thuộc diện tính theo thu nhập
  - trường hợp chuyển tiếp: đã nộp theo ngưỡng 500 triệu thì được bù trừ hoặc hoàn
  - câu sai dài hơn và hào phóng hơn (để đo thiên vị độ dài)
  - câu hỏi của doanh nghiệp (đáp án đúng là từ chối)
  - tin có lệnh cài cho judge
  - tin rác
- [ ] Mỗi tin bẫy ghi `answer` và `cite` (Điều chứa đáp án), do người kiểm chứng duyệt.
- [ ] `bench.py`: thêm chế độ "judge không có văn bản" bên cạnh 5 chế độ hiện tại, để đo Màn 1 (judge dựa vào trí nhớ thì chọn số cũ). Chạy 3 judge × 3 lần, ghi kết quả vào `results/bench.md`.
- [ ] Cập nhật `test_arbiter.py`: test lớp đối chiếu bắt đúng câu sai của các tin bẫy có số liệu (dùng `it.each` / `parametrize` như hiện tại); test lớp đối chiếu không gắn cờ nhầm câu đúng; test phép tính thuế trên 3–4 trường hợp có trong văn bản (ví dụ minh hoạ của thông tư nếu có).

#### Bước 7: giao diện

- [ ] Đổi tên và màu sắc sang hộp thư thuế; bỏ thẻ sản phẩm, bảng tồn kho, trang `/nguon-anh`.
- [ ] Banner cố định: "Theo văn bản hiệu lực đến 30/11/2026. Thông tin tham khảo, không thay thế tư vấn của cơ quan thuế."
- [ ] Ở mỗi câu trả lời: danh sách Điều đã dùng (bấm để mở nguyên văn và link văn bản gốc); trích dẫn trong câu trả lời đánh dấu đã kiểm hay chưa.
- [ ] Màn "chưa chắc chắn" cho người dùng: lý do, các Điều liên quan, gợi ý liên hệ. Bản nháp chỉ hiện ở chế độ người duyệt.
- [ ] Chế độ trình bày: giữ phím `N`, công tắc "Tự gửi", và hàng "Đối chiếu" như hiện tại.

#### Bước 8: tài liệu

- [ ] Viết lại `app/README.md` (kiến trúc, cách chạy, cách cập nhật văn bản) và `app/DEMO.md` (mạch 3 phút: Màn 1, 2, 3, kèm đáp án tin bẫy và kết quả bench).

### Giai đoạn B: cho người khác dùng thật

- [ ] **Tách dữ liệu theo người dùng:** mỗi trình duyệt có một id phiên (cookie), câu hỏi lưu theo id. Hiện `state.json` là một hộp thư chung, nên người này sẽ thấy câu hỏi của người kia.
- [ ] **Quyền riêng tư:** thông báo rằng câu hỏi được gửi tới nhà cung cấp model (Groq, Google). Khuyên không nhập MST, CCCD hay số tài khoản. Lọc bằng regex các chuỗi giống MST/CCCD trước khi gửi.
- [ ] **Giới hạn lượt dùng:** giới hạn số câu mỗi phiên mỗi giờ; báo lỗi rõ khi nhà cung cấp hết hạn mức.
- [ ] **Nút phản hồi** "Đúng / Sai / Báo lỗi" ở mỗi câu trả lời, lưu lại để người duyệt xem. Theo thời gian, phần này thành **bộ nhãn người lấy từ chính dữ liệu thật**, dùng để kiểm chứng lại judge, đúng như khuyến nghị của báo cáo.
- [ ] **Quy trình cập nhật văn bản** (`app/UPDATING.md`):
  1. kiểm tra văn bản mới định kỳ hằng tháng
  2. thêm vào `sources.json`
  3. chạy `preprocess.py`
  4. sửa `rates.json` và `amendments.json`
  5. chạy `eval_retrieval.py`, `bench.py` và test
  6. đổi ngày cắt

  Đổi văn bản tức là đổi domain, nên phải đo lại judge.
- [ ] **Triển khai:** chọn nơi chạy (xem Open Questions), bật HTTPS, giữ `.env` ngoài repo, tách `llm.py` khỏi phụ thuộc vào `experiment/`.

## Out of Scope

- Doanh nghiệp, thuế TNDN, GTGT theo phương pháp khấu trừ.
- **Tính** thuế theo phương pháp thu nhập − chi phí. Hệ thống chỉ nhận biết trường hợp này và từ chối.
- Thuế TNCN từ tiền lương, chuyển nhượng bất động sản, chứng khoán, thừa kế, trúng thưởng; thuế đất; thuế tiêu thụ đặc biệt.
- Tài khoản và đăng nhập; app mobile.
- Embedding, vector DB, fine-tune.
- Tự động thu thập văn bản mới. Giai đoạn này cập nhật tay theo quy trình.
- Chạy lại thí nghiệm của báo cáo hoặc sửa `report.md`.

## Đã quyết (21/11/2026)

- Thay hẳn shop cờ, xoá sạch dấu vết.
- AI chủ động kiểm chứng kỹ khi làm; người kiểm chứng thủ công sau.
- Làm cho mình dùng thật, không chạy theo buổi trình bày; Giai đoạn B trong phạm vi.

## Open Questions

1. **Triển khai ở đâu, ai trả tiền API?** Groq và Gemini free tier giới hạn số lượt mỗi phút. Có nhiều người dùng thì cần key trả phí hoặc giới hạn chặt hơn.
2. **Câu trả lời bị giữ lại thì ai trả lời?** Plan đang chỉ hiện các Điều liên quan và gợi ý hỏi cơ quan thuế. Nếu muốn có người duyệt trả lời sau thì cần thêm thông báo cho người hỏi (email hoặc link quay lại xem).
3. **Hoá đơn điện tử và máy tính tiền** có nằm trong phạm vi không? Đây là câu hỏi hộ kinh doanh rất hay hỏi, nhưng là thêm một nhóm văn bản phải kiểm chứng.
