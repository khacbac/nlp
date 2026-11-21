# Nhật ký kiểm chứng số liệu thuế

Mỗi dòng là một khẳng định mà hệ thống dựa vào (`rates.json`, `amendments.json`, đáp án tin bẫy), kèm câu gốc trong văn bản.

Trạng thái:
- `ai`: AI đã đối chiếu với văn bản gốc.
- `nguoi`: một người đã đối chiếu lại.

Chỉ dòng `nguoi` mới được coi là đã kiểm chứng đầy đủ.

Ngày cắt: 30/11/2026.

## Nghị định 68/2026/NĐ-CP và sửa đổi bởi Nghị định 141/2026/NĐ-CP

| # | Khẳng định | Câu gốc (trích nguyên văn) | Nguồn | Kiểm | Ngày |
|---|---|---|---|---|---|
| 1 | NĐ 68 có hiệu lực từ ngày ký, 05/3/2026 | "Nghị định này có hiệu lực thi hành kể từ ngày ký ban hành." · "Hà Nội, ngày 05 tháng 3 năm 2026" | NĐ 68 Điều 19 (DOCX Công báo số 152) | ai | 2026-11-21 |
| 2 | NĐ 141 có hiệu lực từ 01/01/2026, tức áp dụng hồi tố cho cả năm 2026 | "Nghị định này có hiệu lực thi hành từ ngày 01 tháng 01 năm 2026" | NĐ 141 Điều 3, trích trong chú thích của VBHN 25/2026/VBHN-NĐ-BTC (bản scan, đọc bằng OCR); khớp với trang vanban.chinhphu.vn ("Ngày có hiệu lực: 01-01-2026") | ai | 2026-11-21 |
| 3 | Ngưỡng hiện hành: doanh thu năm **từ 01 tỷ đồng trở xuống** thì không chịu thuế GTGT và không phải nộp thuế TNCN | NĐ 68 Điều 3 khoản 1 và Điều 4 khoản 1, gốc "500 triệu đồng", sửa thành "01 tỷ đồng" theo NĐ 141 Điều 1 khoản 1: "Cụm từ "500 triệu đồng" được thay thế bởi cụm từ "01 tỷ đồng" theo quy định tại khoản 1, Điều 1 của Nghị định số 141/2026/NĐ-CP" | DOCX NĐ 68 + chú thích VBHN 25 (OCR) | ai | 2026-11-21 |
| 4 | Thay "500 triệu đồng" bằng "01 tỷ đồng" ở: Điều 3, Điều 4, khoản 1 Điều 8, Điều 9, Điều 10, khoản 3 Điều 11, khoản 1 và 2 Điều 12, khoản 4 Điều 17, khoản 3 Điều 18 | Danh sách lấy từ bài toàn văn trên xaydungchinhsach.chinhphu.vn (25/5/2026) | Đối chiếu tự động: sau khi áp sửa đổi, không còn "500 triệu đồng" trong NĐ 68; OCR của VBHN 25 cũng không còn chỗ nào (trừ các chú thích ghi nhận việc thay thế) | ai | 2026-11-21 |
| 5 | Khoản 5 Điều 8 (hoá đơn điện tử) được thay toàn bộ: doanh thu năm **trên 01 tỷ** phải dùng hoá đơn điện tử có mã hoặc khởi tạo từ máy tính tiền; từ 01 tỷ trở xuống thì tự nguyện | "a) Hộ kinh doanh, cá nhân kinh doanh có doanh thu năm trên 01 tỷ đồng thì phải áp dụng hóa đơn điện tử có mã của cơ quan thuế, hóa đơn điện tử khởi tạo từ máy tính tiền…" (khoản 2 Điều 1 NĐ 141) | Bài toàn văn trên xaydungchinhsach.chinhphu.vn, khớp với OCR của VBHN 25; cấu trúc điểm a–c lấy theo VBHN | ai | 2026-11-21 |
| 6 | Phương pháp tính TNCN: từ trên ngưỡng đến 03 tỷ thì tính theo thuế suất × doanh thu, hoặc tự chọn theo thu nhập; trên 03 tỷ bắt buộc tính theo thu nhập × thuế suất | "Phương pháp tính thuế thu nhập cá nhân theo thuế suất nhân (x) doanh thu tính thuế áp dụng đối với cá nhân kinh doanh có doanh thu năm trên 500 triệu đồng [01 tỷ đồng] đến 03 tỷ đồng" · "…theo thu nhập tính thuế nhân (x) thuế suất áp dụng đối với cá nhân kinh doanh có doanh thu năm trên 03 tỷ đồng và trường hợp … lựa chọn phương pháp này" | NĐ 68 Điều 4 khoản 5 điểm a, b | ai | 2026-11-21 |
| 7 | Hộ đang tính theo doanh thu mà doanh thu thực tế năm vượt 03 tỷ thì từ năm sau phải chuyển sang tính theo thu nhập; đã chọn tính theo thu nhập thì phải giữ ổn định 02 năm | NĐ 68 Điều 4 khoản 5 điểm d (nguyên văn trong `articles.jsonl`, id `nd-68-2026:d4:k5`) | DOCX NĐ 68 | ai | 2026-11-21 |
| 8 | Hộ đến 01 tỷ đã lỡ kê khai, nộp thuế theo NĐ 68 thì được xử lý tiền thuế đã nộp (bù trừ, hoàn trả) theo Điều 12 NĐ 68 | "Trường hợp hộ kinh doanh, cá nhân kinh doanh tự xác định mức doanh thu năm từ hoạt động sản xuất, kinh doanh hàng hóa, dịch vụ từ 01 tỷ đồng trở xuống mà đã kê khai nộp thuế thu nhập cá nhân, thuế giá trị gia tăng theo quy định tại Nghị định số 68/2026/NĐ-CP thì được xử lý tiền thuế đã nộp theo quy định tại Điều 12 Nghị định số 68/2026/NĐ-CP." | NĐ 141 Điều 4 khoản 1 (DOCX Công báo số 272) | ai | 2026-11-21 |
| 9 | Thuế khoán chấm dứt từ 01/01/2026; không truy thu lại các năm đã khoán (trừ khi che giấu doanh thu) | NĐ 68 Điều 17 khoản 5 (nguyên văn trong `articles.jsonl`, id `nd-68-2026:d17:k5`) | DOCX NĐ 68 | ai | 2026-11-21 |
| 10 | Tỷ lệ % thuế GTGT và thuế suất TNCN **không nằm trong NĐ 68**. NĐ 68 dẫn sang Luật GTGT 48/2024/QH15, và khoản 2, khoản 3 Điều 7 Luật Thuế TNCN 109/2025/QH15 | NĐ 68 Điều 3 khoản 2, Điều 4 khoản 5 điểm a–b | DOCX NĐ 68 | ai | 2026-11-21 |

| 11 | NĐ 141 Điều 1 khoản 1: danh sách chỗ thay "500 triệu đồng" bằng "01 tỷ đồng" | "Sửa đổi cụm từ "500 triệu đồng" thành "01 tỷ đồng" tại Điều 3, Điều 4, khoản 1 Điều 8, Điều 9, Điều 10, khoản 3 Điều 11, khoản 1 và khoản 2 Điều 12, khoản 4 Điều 17, khoản 3 Điều 18 Nghị định số 68/2026/NĐ-CP." | DOCX NĐ 141; khớp với `amendments.json` (mục 4 ở trên) | ai | 2026-11-21 |

## Luật thuế: tỷ lệ, thuế suất, ngưỡng

| # | Khẳng định (khoá trong `rates.json`) | Câu gốc (trích nguyên văn) | Nguồn | Kiểm | Ngày |
|---|---|---|---|---|---|
| 12 | Luật giao Chính phủ quy định ngưỡng doanh thu (TNCN và GTGT); mức Chính phủ quy định hiện là 01 tỷ (mục 3) | "Cá nhân cư trú có hoạt động sản xuất, kinh doanh có doanh thu năm từ mức quy định của Chính phủ trở xuống không phải nộp thuế thu nhập cá nhân." · Luật GTGT Điều 5 khoản 25: "…có doanh thu năm từ mức quy định của Chính phủ trở xuống" | VBHN 112 Điều 7 khoản 1; VBHN 114 Điều 5 khoản 25; Luật 09/2026 Điều 5 khoản 2: "Quy định tại các điều 1, 2 và 3 của Luật này có hiệu lực thi hành từ ngày 01 tháng 01 năm 2026." | ai | 2026-11-21 |
| 13 | `gtgt.base`: GTGT tính trên **toàn bộ doanh thu** | "Doanh thu để tính thuế giá trị gia tăng là tổng số tiền bán hàng hóa, dịch vụ ghi trên hóa đơn bán hàng, bao gồm các khoản phụ thu và phí thu thêm…" | VBHN 114 Điều 12 khoản 2 điểm c | ai | 2026-11-21 |
| 14 | `groups[].gtgt`: 1% / 5% / 3% / 2% | "b1) Phân phối, cung cấp hàng hóa: 1%; b2) Dịch vụ, xây dựng không bao thầu nguyên vật liệu: 5%; b3) Sản xuất, vận tải, dịch vụ có gắn với hàng hóa, xây dựng có bao thầu nguyên vật liệu: 3%; b4) Hoạt động kinh doanh khác: 2%" | VBHN 114 Điều 12 khoản 2 điểm b | ai | 2026-11-21 |
| 15 | `tncn_revenue_method.base`: TNCN tính trên **phần doanh thu vượt ngưỡng** | "a) Doanh thu tính thuế được xác định bằng phần doanh thu vượt trên mức quy định tại khoản 1 Điều này" | VBHN 112 Điều 7 khoản 3 điểm a | ai | 2026-11-21 |
| 16 | `groups[].tncn`: 0,5% / 2% (cho thuê tài sản, đại lý 5%) / 1,5% / nội dung số 5% / khác 1% | "b) Phân phối, cung cấp hàng hoá: thuế suất 0,5%; c) Dịch vụ, xây dựng không bao thầu nguyên vật liệu: thuế suất 2%. Riêng hoạt động cho thuê tài sản, đại lý bảo hiểm, đại lý xổ số, đại lý bán hàng đa cấp: thuế suất 5%; d) Sản xuất, vận tải, dịch vụ có gắn với hàng hóa, xây dựng có bao thầu nguyên vật liệu: thuế suất 1,5%; đ) Hoạt động cung cấp sản phẩm và dịch vụ nội dung thông tin số về giải trí, trò chơi điện tử, phim số, ảnh số, nhạc số, quảng cáo số: thuế suất 5%; e) Hoạt động kinh doanh khác: thuế suất 1%." | VBHN 112 Điều 7 khoản 3 | ai | 2026-11-21 |
| 17 | `tncn_income_method`: 15% (trên ngưỡng đến 03 tỷ), 17% (trên 03 đến 50 tỷ), 20% (trên 50 tỷ) | "b) … đến 03 tỷ đồng: thuế suất 15%; c) … trên 03 tỷ đồng đến 50 tỷ đồng: thuế suất 17%; d) … trên 50 tỷ đồng: thuế suất 20%." | VBHN 112 Điều 7 khoản 2 | ai | 2026-11-21 |
| 18 | `rental_real_estate`: cho thuê bất động sản nộp 5% trên phần doanh thu vượt ngưỡng | "Cá nhân cho thuê bất động sản, trừ hoạt động kinh doanh lưu trú, nộp thuế thu nhập cá nhân được xác định bằng phần doanh thu vượt trên mức quy định tại khoản 1 Điều này nhân (x) với thuế suất 5%." | VBHN 112 Điều 7 khoản 4 | ai | 2026-11-21 |
| 19 | Luật TNCN: quy định về thu nhập kinh doanh áp dụng từ kỳ tính thuế 2026 | "Các quy định liên quan đến thu nhập từ kinh doanh, từ tiền lương, tiền công của cá nhân cư trú áp dụng từ kỳ tính thuế năm 2026." | VBHN 112 Điều 29 khoản 2 | ai | 2026-11-21 |
| 20 | `groups` cho-thue-dai-ly và noi-dung-so: **chưa có tỷ lệ GTGT** | Luật GTGT chỉ có 4 nhóm; "Bộ trưởng Bộ Tài chính quy định chi tiết nhóm hàng hóa, dịch vụ thuộc đối tượng áp dụng theo tỷ lệ % tại điểm b khoản 2 Điều này." TT 18/2026 không có bảng nhóm ngành (đã tìm "0,5%", "1,5%": không có) | VBHN 114 Điều 12 khoản 4; TT 18 | ai, **cần văn bản Bộ Tài chính** | 2026-11-21 |
| 21 | Ví dụ "quán ăn, cà phê thuộc nhóm sản xuất / dịch vụ gắn với hàng hóa" | Không có câu gốc. Đây là cách hiểu, không phải trích dẫn | — | **chưa** | — |

## Giảm thuế

| # | Khẳng định | Câu gốc | Nguồn | Kiểm | Ngày |
|---|---|---|---|---|---|
| 22 | `reductions.tncn-30`: giảm 30% thuế TNCN kỳ 2026 và 2027 nếu doanh thu năm không quá 10 tỷ, mọi phương pháp tính | "Giảm 30% số thuế thu nhập cá nhân phải nộp của kỳ tính thuế năm 2026 và năm 2027 đối với thu nhập từ kinh doanh của cá nhân cư trú có mức doanh thu hằng năm của năm 2026, năm 2027 không quá 10 tỷ đồng." · "…không phân biệt phương pháp tính thuế thu nhập cá nhân." | NQ 43/2026 Điều 1 khoản 1 (bản chép tay, đã đối chiếu với OCR tiếng Việt của bản scan); NĐ 398/2026 Điều 2 khoản 2 (DOCX Công báo số 576) | ai | 2026-11-21 |
| 23 | Doanh thu thực tế vượt 10 tỷ thì không được giảm, phải nộp bổ sung | "Trường hợp tổng doanh thu thực tế trong năm vượt quá 10 tỷ đồng thì không được áp dụng mức giảm thuế…" | NĐ 398 Điều 2 khoản 4 điểm c | ai | 2026-11-21 |
| 24 | `reductions.gtgt-20`: giảm 20% mức tỷ lệ % GTGT đến hết 31/12/2026, với hàng hóa, dịch vụ thuộc diện giảm | "Cơ sở kinh doanh (bao gồm cả hộ kinh doanh, cá nhân kinh doanh) tính thuế giá trị gia tăng theo phương pháp tỷ lệ % trên doanh thu được giảm 20% mức tỷ lệ % để tính thuế giá trị gia tăng khi thực hiện xuất hóa đơn đối với hàng hóa, dịch vụ được giảm thuế…" · "…từ ngày 01 tháng 7 năm 2025 đến hết ngày 31 tháng 12 năm 2026." | NĐ 174/2025 Điều 1 khoản 2 điểm b; Điều 2 khoản 1 | ai | 2026-11-21 |

## Chế độ đã bãi bỏ, ngưỡng cũ

| # | Khẳng định | Câu gốc | Nguồn | Kiểm | Ngày |
|---|---|---|---|---|---|
| 25 | Bỏ thuế khoán từ 01/01/2026 | "Hộ kinh doanh, cá nhân kinh doanh không áp dụng phương pháp khoán thuế từ ngày 01 tháng 01 năm 2026." | NQ 198/2025 Điều 10 khoản 6 | ai | 2026-11-21 |
| 26 | Bỏ lệ phí môn bài từ 01/01/2026 | "Chấm dứt việc thu, nộp lệ phí môn bài từ ngày 01 tháng 01 năm 2026." | NQ 198/2025 Điều 10 khoản 7 | ai | 2026-11-21 |
| 27 | Ngưỡng 200 triệu (Luật GTGT 48/2024 bản gốc) **chưa từng được áp dụng** | Luật 48 Điều 5 khoản 25: "…từ 200 triệu đồng trở xuống"; Điều 18 khoản 2: quy định này "có hiệu lực thi hành từ ngày 01 tháng 01 năm 2026"; Luật 149/2025 sửa thành 500 triệu, "có hiệu lực thi hành từ ngày 01 tháng 01 năm 2026" | Luật 48/2024 (.doc), Luật 149/2025 (DOCX) | ai | 2026-11-21 |
| 28 | Ngưỡng 100 triệu theo TT 40/2021 | Chưa có TT 40/2021 trong kho. TT 18/2026 Điều 9 khoản 2 xác nhận TT 40/2021 đã bị thay thế | — | **chưa** | — |

## Chưa đưa vào tính toán

- **Luật thông qua ngày 20/11/2026**, sửa Luật TNDN, Luật Thuế sử dụng đất phi nông nghiệp và Luật TNCN. Theo bài báo, mốc được chọn tính thuế theo tỷ lệ trên doanh thu nâng từ 03 tỷ lên 10 tỷ, áp dụng từ kỳ tính thuế 2027. Luật chưa đăng Công báo, nên chưa có số hiệu và chưa có văn bản gốc. Xem `rates.json` → `pending`.
- **Danh mục hàng hóa không được giảm GTGT** (phụ lục NĐ 174/2025): chưa tách vào `articles.jsonl`. Hệ thống không tự quyết hàng nào được giảm 20%.
