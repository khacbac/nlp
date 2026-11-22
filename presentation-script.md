# Kịch bản thuyết trình cuối kỳ: Thứ tự có quan trọng không?

Seminar NLP501.22, chủ đề 18 (Đánh giá LLM: Benchmark và LLM-as-a-Judge), nhóm ABNQ. Khoảng 25 phút: 21 phút nói, 4 phút demo. Kịch bản thuyết trình proposal cũ vẫn còn trong lịch sử git.

Lời nói cho từng slide nằm trong ghi chú người nói của `slides/index.html` (phím `N`, hoặc phím `P` để mở cửa sổ presenter có đồng hồ). File này chỉ ghi phần chuẩn bị, thời lượng và câu hỏi dự kiến.

## Chuẩn bị

1. Mở `slides/index.html` trong Chrome và bấm `F` để vào toàn màn hình. Các phím: `←` `→` chuyển slide, `O` xem tổng quan, `N` hiện ghi chú, `P` mở cửa sổ presenter (kéo cửa sổ này sang màn hình laptop).
2. Bản dự phòng là `slides/slides.pdf`. Máy cần có mạng để tải font Be Vietnam Pro; nếu mất mạng, slide sẽ hiển thị bằng font hệ thống.
3. Demo: chạy `python app/server.py` trước giờ trình bày rồi mở http://localhost:8010. Vào Cài đặt, bật **Chế độ trình bày** và **Chế độ người duyệt**, tắt **Tự trả lời**. Chi tiết xem `app/DEMO.md`.
4. Gói Groq miễn phí chỉ cho 8.000 token mỗi phút. Không chạy thử cả hộp thư ngay trước giờ lên. Nếu demo hỏng, mở `demo.html`: trang này có ba cặp flip thật và chạy offline.

## Thời lượng

| Phần | Slide | Thời gian | Hết phần lúc |
|---|---|---|---|
| Mở đầu: bìa, mục lục, tóm tắt | 1–3 | 1:30 | 1:30 |
| 01 Bối cảnh | 4–8 | 3:00 | 4:30 |
| 02 Paper và survey | 9–17 | 6:15 | 10:45 |
| 03 Thí nghiệm | 18–21 | 2:30 | 13:15 |
| 04 Kết quả | 22–32 | 6:45 | 20:00 |
| 05 Ứng dụng và demo | 33–36 | 2:00 + 4:00 demo | 26:00 |
| 06 Kết luận | 37–41 | 2:00 | 28:00 |
| Tài liệu, phụ lục | 42–43 | khi được hỏi | |

- Năm slide quan trọng nhất: **Tóm tắt (3)**, **Đúc kết từ tài liệu (16)**, **RQ4 (29)**, **Tỉ lệ verdict đáng tin T (30)** và **Bài học mang về (40)**.
- Slide 14 (ba công trình 2026) và 30 (T = 15,9%) mới thêm, mỗi slide khoảng 45 giây. Giữ demo trực tiếp; nếu thiếu giờ, lướt nhanh qua các slide không nằm trong danh sách quan trọng ở trên.

## Phân công gợi ý

| Người | Slide |
|---|---|
| Bắc | 1–8 và demo |
| Nhân | 9–17 (paper và survey) |
| Việt Anh | 18–28 |
| Quang | 29–43 |

## Câu hỏi dự kiến

**Đề tài khác gì Zheng et al. và Wang et al.?**
Có bốn điểm khác:
- Làm trên tiếng Việt.
- Judge là mô hình mở, nên đọc được xác suất token (RQ3).
- Độ chênh chất lượng đo bằng người chấm, không bằng chính LLM.
- Có đáp án gốc nên so được với một baseline đơn giản.

Nhóm không nhằm phát hiện ra thiên vị vị trí, vì hiện tượng này đã được ghi nhận ở tiếng Anh.

**Kết quả này có đúng cho GPT-4 hay Claude không?**
Chưa biết. Kết quả nói về một judge 7B. Survey của Gu et al. cũng đo được LLaMA3-8B chỉ nhất quán 39%, còn GPT-4-turbo đạt 80%. Tuy vậy, judge mạnh cũng không hết thiên vị: GPT-4o chỉ đạt 50,9% trên JudgeBench. Chạy judge lớn hơn là hướng tiếp theo số 3.

**Baseline F1 được xem đáp án gốc, so như vậy có công bằng không?**
Không hoàn toàn, và slide RQ4 đã ghi rõ điều này. Judge được thiết lập giống MT-Bench, không có đáp án. Dù vậy, bài học thực tế vẫn đúng: khi có đáp án chuẩn thì nên dùng nó. Hướng tiếp theo số 2 cho judge xem đáp án gốc để đo khoảng cách này.

**Vì sao chọn Qwen làm judge khi Qwen cũng là một mô hình trả lời?**
Qwen là mô hình mở và chạy được trên Colab T4, nên lấy được xác suất token mà không tốn phí API. Có thể có thiên vị tự đề cao, nhưng số liệu cho thấy ngược lại: judge xếp Qwen cuối. Thiên vị này cũng không tạo ra flip, vì cùng một cặp được chấm ở cả hai thứ tự.

**Tie (hoà) được xử lý thế nào?**
Một lượt chấm ra `[[C]]` vẫn có người thắng: đó là câu có xác suất A/B cao hơn sau khi chuẩn hoá. Nếu bỏ hết các cặp có verdict hoà, flip rate vẫn còn 34,8%.

**Rò rỉ dữ liệu (câu hỏi mở của chủ đề) ảnh hưởng thế nào?**
Câu hỏi lấy từ tập train công khai của UIT-ViQuAD, nên mô hình có thể đã thấy. Điều này ảnh hưởng đến chất lượng câu trả lời, không ảnh hưởng đến phép đo flip, vì flip so cùng một cặp ở hai thứ tự. Với benchmark trắc nghiệm như MMLU, rò rỉ nguy hiểm hơn, vì điểm số đo trực tiếp việc chọn đúng đáp án.

**Vì sao judge lại thích gpt-oss?**
Có hai lý do:
- Một phần do độ dài: judge chọn câu dài hơn ở 69% số cặp.
- gpt-oss và Gemini dài gần bằng nhau, nên nhóm nghi chữ in đậm. Judge nhìn thấy định dạng này, còn người chấm thì không. Đây là hướng tiếp theo số 1.

**Sao không để một AI khác đối chiếu luật trong ứng dụng?**
Làm vậy là thêm một judge nữa, mang đúng những thiên vị đang đo. Lớp đối chiếu viết bằng quy tắc nên không có thiên vị vị trí và không bị lệnh cài tác động. Đổi lại, nó chỉ bắt được số và từ khoá: tự bắt được 8 trên 12 bản nháp sai.

**Bench 13 tin bẫy có đủ để kết luận không?**
Không. Mỗi ô chỉ chạy một lần vì hạn mức Groq miễn phí. Slide đã ghi đây là minh hoạ. Cần chạy lại với `--repeats 3`.

**Survey nói gì về nguyên nhân của thiên vị vị trí?**
Cả hai survey (Gu, Li) đều chưa đưa ra cơ chế. Li et al. ghi rõ đây là việc cần nghiên cứu. Có hai giả thuyết cụ thể:
- Ưu ái token "A" (Zheng 2024, trên câu hỏi trắc nghiệm).
- Với mô hình suy luận, phần sau được đọc như kết luận (Wang 2025).

**Giải thích trước khi chấm có giúp không?**
Các nghiên cứu đang mâu thuẫn. Gu et al. thấy lời giải thích làm giảm nhất quán vị trí, còn Fu & Liu thấy nó tăng nhất quán giữa các ngôn ngữ. Judge của nhóm ghi verdict trước ở 85,5% số lượt chấm, nên chưa kiểm được điều này. Đây là hướng tiếp theo số 5.

**T = 15,9% tính thế nào? C = 100% có phải gian lận không?**
T = C·(A − φ/2) của Kumar et al. 2026, trên 813 cặp có người thắng: φ = 42,4%, A = 37,1% (trung bình hai thứ tự). Ép về hai lựa chọn nên cặp bị flip có đúng một lượt đúng, vì vậy A − φ/2 chính là tỉ lệ cặp vừa nhất quán vừa khớp người: 129/813. C = 100% vì judge chạy greedy, nhiệt độ 0; đó là do thiết lập, không phải đo được, và slide đã ghi rõ. Paper đo C giảm trung bình 12,1 điểm khi nhiệt độ từ 0 lên 1.

**Sao không hiệu chỉnh kết quả judge theo Lee et al. 2026?**
Thí nghiệm của nhóm có điểm người cho toàn bộ 1.500 cặp, nên so trực tiếp được, không cần ước lượng. Hiệu chỉnh bằng q₀ (độ đặc hiệu) và q₁ (độ nhạy) dùng khi chỉ có nhãn người cho một tập nhỏ và muốn báo tỉ lệ thắng trên tập lớn kèm khoảng tin cậy. Đây là hướng tiếp theo số 7.

**Paper của Zhou et al. liên quan gì đến tiếng Việt?**
Họ thấy cùng một nội dung, ngôn ngữ ít tài nguyên (có tiếng Việt) lại được chấm cao hơn khoảng 0,4–0,5 điểm trên thang 1–5, trong khi độ chính xác pairwise vẫn trên 90%. Thí nghiệm của nhóm là pairwise trong cùng một ngôn ngữ nên không đo được lệch này. Nếu chạy điều kiện tiếng Anh (hướng số 4), cần đo cả điểm tuyệt đối, không chỉ flip.
