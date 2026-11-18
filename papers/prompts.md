# Prompt mẫu để đọc paper cùng AI

Quy tắc chung:
- **Luôn đính kèm PDF.** Đừng hỏi AI về paper chỉ dựa trên trí nhớ của nó.
- **Bắt AI ghi nguồn** (section / table / trang) cho mọi thông tin, rồi tự mở PDF kiểm tra con số.
- Dán bối cảnh project (khối dưới đây) vào đầu cuộc trò chuyện để AI trả lời đúng trọng tâm.

```
Bối cảnh: mình làm project thạc sĩ NLP về position bias của LLM judge trên tiếng Việt.
Judge chấm pairwise 2 câu trả lời, chấm cả 2 thứ tự (swap), đo Flip Rate, độ tự tin
từ xác suất token "A"/"B", và thử Balanced Position Calibration. Dữ liệu: 500 câu hỏi
UIT-ViQuAD 2.0, câu trả lời từ Qwen2.5-7B, gpt-oss-20b, Gemini Flash-Lite, có 4 người chấm.
Câu hỏi nghiên cứu:
RQ1 tỉ lệ flip; RQ2 flip có tập trung ở cặp có chất lượng gần nhau không;
RQ3 flip có trùng với độ tự tin thấp không; RQ4 chấm 2 chiều có tăng độ khớp với người chấm không.
Mình là người mới, hãy giải thích bằng tiếng Việt, dễ hiểu, giữ thuật ngữ tiếng Anh.
Mọi thông tin phải kèm nguồn (section/table/trang). Không chắc thì nói không chắc.
```

## P1: Lượt 1, quyết định có đọc tiếp không
```
Đọc PDF đính kèm. Trả lời ngắn gọn:
1. Paper giải quyết vấn đề gì (1 câu)?
2. Làm bằng cách nào (3 gạch đầu dòng)?
3. 2–3 kết quả chính, kèm con số và bảng nguồn.
4. Phần nào của paper liên quan nhất tới RQ nào của mình? Mình nên đọc kỹ section/bảng nào?
```

## P2: Hiểu một khái niệm khó
```
Giải thích <khái niệm, vd: Balanced Position Calibration> trong paper này:
- Bắt đầu bằng một ví dụ cụ thể với 1 câu hỏi và 2 câu trả lời.
- Sau đó mới đưa công thức, giải thích từng ký hiệu.
- Nếu không có kỹ thuật này thì kết quả sẽ sai thế nào?
```

## P3: Đọc hiểu một bảng
```
Giải thích Table <n>: mỗi hàng, mỗi cột là gì? Kết luận chính tác giả rút ra từ bảng này là gì?
Có con số nào mình có thể so trực tiếp với kết quả tiếng Việt của mình không?
```

## P4: Rút ra cho project (điền mục 6–7 của thẻ)
```
So sánh paper này với project của mình:
1. Kỹ thuật/metric nào mình nên dùng lại nguyên bản? Cái nào cần điều chỉnh, vì sao?
2. Paper chưa làm gì mà project mình làm được (khoảng trống)?
3. Hạn chế nào của paper cũng có thể xảy ra với project mình?
```

## P5: Lượt 3, để AI kiểm tra mình hiểu chưa
```
Đóng vai giảng viên. Hỏi mình 5 câu về paper này, từ dễ tới khó, mỗi lần 1 câu.
Chờ mình trả lời rồi mới nhận xét: đúng/sai chỗ nào, dẫn chứng từ paper.
Câu cuối phải là câu "áp dụng vào project tiếng Việt của mình thế nào".
```

## P6: Tổng hợp nhiều paper (khi đã có vài thẻ)
```
Đây là các thẻ đọc của nhóm [dán nội dung]. Hãy:
1. Chỉ ra điểm các paper đồng ý và mâu thuẫn với nhau.
2. Đề xuất cách sắp xếp phần Related Work (theo chủ đề, không theo từng paper).
3. Kiểm tra xem mỗi quyết định thiết kế trong proposal đã có paper nào ủng hộ chưa.
```
