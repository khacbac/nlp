# Wang et al. 2023, *Large Language Models are not Fair Evaluators*: giải thích dễ hiểu

Bản giải thích trực quan, đọc trước thẻ `wang2023.md`. PDF: `papers/pdf/wang2023.pdf` · [arXiv:2305.17926](https://arxiv.org/abs/2305.17926)

**Tóm tắt:** chỉ cần đổi thứ tự hai câu trả lời là LLM giám khảo đổi luôn kết luận. Bài đề xuất 3 cách sửa đơn giản, không cần train lại model.

## 1. Câu chuyện mở đầu

Giả sử An muốn biết Vicuna-13B hay ChatGPT trả lời tốt hơn. An nhờ GPT-4 chấm:

```
Lần 1:  [Vicuna] [ChatGPT]  →  GPT-4: "Vicuna tốt hơn"
Lần 2:  [ChatGPT] [Vicuna]  →  GPT-4: "ChatGPT tốt hơn"
```

Hai câu trả lời giữ nguyên, chỉ đổi chỗ, vậy mà kết luận đảo ngược. Prompt còn ghi rõ "đừng để thứ tự ảnh hưởng" mà vẫn bị như vậy (Figure 1, Table 1).

Hãy hình dung một ban giám khảo cuộc thi hát luôn cho thí sinh hát trước điểm cao hơn. Ai được xếp lượt đầu thì thắng, bất kể hát hay dở. Nếu không phát hiện ra chuyện này, An sẽ công bố "Vicuna ngang ChatGPT", trong khi kết quả đó thật ra do cách xếp thứ tự mà ra.

## 2. Phát hiện 1: bias rất lớn, và mỗi judge lệch một kiểu (Table 2, trang 3)

Tác giả định nghĩa **Conflict Rate** (công thức 1): chấm mỗi cặp 2 lần với 2 thứ tự, đếm số cặp có kết luận khác nhau giữa 2 lần, rồi chia cho tổng số cặp. Đây chính là **Flip Rate** trong project.

| Judge | Cặp so sánh | Tỉ lệ lật |
|---|---|---|
| GPT-4 | Vicuna vs ChatGPT (ngang tài) | **46.3%** |
| GPT-4 | Vicuna vs Alpaca (chênh rõ) | 5.0% |
| ChatGPT | Vicuna vs ChatGPT | **82.5%** |
| ChatGPT | Vicuna vs Alpaca | 52.5% |

Cần nắm 2 điều từ bảng này:
- **Judge mạnh hơn thì ít lật hơn**, nhưng GPT-4 vẫn lật gần một nửa số cặp ngang tài.
- **Mỗi judge lệch về một hướng.** GPT-4 thiên về câu đứng **trước**. ChatGPT thiên về câu đứng **sau**: Vicuna chỉ thắng 2.5% khi đứng trước, nhưng thắng 82.5% khi đứng sau. Vì vậy khi dùng một judge mới như Qwen, không thể đoán trước nó lệch về phía nào mà phải đo.

## 3. Phát hiện 2: bias nặng nhất khi hai câu ngang nhau (Figure 2, trang 3)

Tác giả chia các cặp theo **chênh lệch điểm** giữa hai câu. Khi chênh ≤ 1 điểm (thang 10), GPT-4 lật rất nhiều. Khi chênh ≥ 3 điểm, gần như không lật nữa.

Giống như chấm hai bài văn: nếu một bài 9 điểm, một bài 4 điểm thì đọc bài nào trước cũng không quan trọng. Nếu hai bài cùng khoảng 7 điểm thì ấn tượng từ bài đọc trước dễ quyết định kết quả. Khi không có lý do rõ ràng để chọn, judge dựa vào vị trí.

Đây chính là giả thuyết của **RQ2** trong project.

## 4. Ba cách sửa (Mục 3, trang 4–5)

```
              ┌─ MEC: viết lý do trước, cho điểm sau (chạy k=3 lần)
câu hỏi + 2 ──┼─ BPC: chấm cả 2 thứ tự, lấy trung bình
câu trả lời   └─ HITLC: nếu judge "lưỡng lự" → chuyển cho người chấm
```

**MEC (Multiple Evidence Calibration): lý do trước, điểm sau.**
- Prompt gốc bắt model cho điểm trước rồi mới giải thích. Model sinh chữ từ trái sang phải, nên khi đã cho điểm thì phần giải thích chỉ còn là biện minh cho điểm đó. Giống học sinh khoanh đáp án trước rồi mới viết lời giải cho khớp.
- MEC đảo lại: phân tích trước, cho điểm sau. Chạy 3 lần rồi lấy trung bình.

**BPC (Balanced Position Calibration): chấm 2 chiều rồi lấy trung bình.**
- Giống bóng đá đổi sân sau hiệp một: không đội nào được hưởng lợi từ gió hay nắng suốt cả trận.
- Mỗi câu trả lời được chấm ở cả vị trí đầu lẫn vị trí sau. Điểm cuối cùng là trung bình (công thức 2).

**HITLC (Human-in-the-Loop Calibration): khi judge lưỡng lự thì hỏi người.**
- Tác giả gom 6 kết quả chấm của một cặp (3 lần × 2 thứ tự).
- Nếu cả 6 lần đều nói "A thắng" thì judge chắc chắn, entropy thấp.
- Nếu kết quả lẫn lộn, ví dụ 3 lần thắng, 2 lần thua, 1 lần hòa, thì entropy cao. Chỉ số này gọi là **BPDE**.
- 20% cặp có BPDE cao nhất được chuyển cho người chấm.

## 5. Kết quả (Table 4, trang 6)

Thước đo là **mức khớp với nhãn đa số của 3 người chấm**:
- **Accuracy:** tỉ lệ cặp mà judge chọn giống người.
- **Kappa:** giống accuracy nhưng trừ đi phần trùng do may mắn. Kappa bằng 0 tức là chỉ ngang đoán mò, bằng 1 tức là khớp hoàn toàn.

| | Accuracy | Kappa |
|---|---|---|
| Người với người (trung bình) | 71.7% | 0.54 |
| ChatGPT, chấm kiểu thường | 44.4% | **0.06** (gần như đoán mò) |
| ChatGPT + MEC + BPC | 58.7% | 0.31 |
| GPT-4, chấm kiểu thường | 52.7% | 0.24 |
| GPT-4 + MEC + BPC | 62.5% | 0.37 |
| GPT-4 + MEC + BPC + 20% người chấm | 73.8% | 0.56 (ngang người) |

**Chi tiết đáng chú ý nhất:** "MEC 3 lần + BPC" cho kết quả tốt hơn "MEC 6 lần", dù cả hai đều gọi model 6 lần. Như vậy phần cải thiện thật sự đến từ việc đổi vị trí, chứ không chỉ từ việc chấm nhiều lần hơn.

**Cũng đáng chú ý:** ngay cả người với người cũng chỉ khớp nhau 71.7%. Chấm câu trả lời mở vốn khó, kể cả với người.

## 6. Cần lưu ý khi trích dẫn bài này

- **BPC gốc lấy trung bình điểm 1–10.** Project sẽ lấy trung bình **xác suất token A/B**. Đây là một điều chỉnh của nhóm, phải ghi rõ trong báo cáo, không được viết như thể paper làm vậy.
- **Sau khi áp BPC thì không còn tính được flip rate** (Table 5 ghi "N/A"), vì hai lần chấm đã gộp thành một kết quả. Nên RQ4 chỉ so được **mức khớp với người chấm**.
- **Người chấm là chính 3 tác giả**, không giấu mục đích nghiên cứu, và chỉ có 80 câu hỏi. Đây là quy mô nhỏ.
- **Đây là GPT-4 bản 2023.** Đừng trích con số này như thể judge hiện nay vẫn y như vậy.

## 7. Giới hạn của bài, cũng là cơ hội cho project

| Bài này chưa làm | Project làm |
|---|---|
| Chỉ có tiếng Anh | Tiếng Việt, có so với bản tiếng Anh |
| Judge đóng, không xem được xác suất | Qwen mở, đọc được xác suất token |
| Đo "lưỡng lự" bằng cách chạy 6 lần (tốn kém) | Confidence margin chỉ cần 1 lần chạy (rẻ) |
| Chênh lệch chất lượng lấy từ **điểm của chính LLM** (vòng vo) | Chênh lệch lấy từ **điểm người chấm** |
| 80 câu × 2 cặp | 500 câu × 3 cặp = 1500 cặp |

## 8. Áp dụng vào project, từng RQ

- **RQ1 (tỉ lệ lật):** dùng định nghĩa Conflict Rate (công thức 1). Lấy Table 2 làm mốc: "GPT-4 tiếng Anh lật 46.3% ở cặp ngang tài. Qwen trên tiếng Việt thì sao?"
- **RQ2 (lật khi ngang tài):** lặp lại Figure 2, nhưng trục hoành là **chênh lệch điểm người chấm**.
- **RQ3 (độ tự tin):** BPDE và confidence margin cùng trả lời một câu hỏi: judge có đang lưỡng lự không? Thêm một phân tích: confidence margin (1 lần chạy) có tìm ra các cặp bị lật tốt như cách chạy nhiều lần không? Nếu có, đó là cách rẻ hơn hẳn.
- **RQ4 (BPC):** ví dụ cụ thể với cặp X và Y:

  ```
  Lần 1: X ở vị trí A → P(A) = 0.70  → P(X) = 0.70  → X thắng
  Lần 2: X ở vị trí B → P(B) = 0.40  → P(X) = 0.40  → Y thắng   ← lật!
  BPC:   P(X) = (0.70 + 0.40) / 2 = 0.55  → X thắng sát nút
  ```

  Sau đó so: chỉ dùng lần chấm thứ nhất, chỉ giữ các cặp không bị lật, hay dùng BPC, thì cách nào khớp với người chấm hơn?

- **Rubric người chấm:** kappa giữa người với người của bài là 0.54. Nếu 4 annotator của nhóm đạt mức tương đương thì đó là bình thường, không phải do rubric tồi.

## 9. Đúc kết: 3 câu có thể nói với thầy

1. Judge LLM có position bias mạnh và có hướng. Mỗi model lệch một kiểu, nên phải đo, không đoán trước được.
2. Bias tập trung ở các cặp ngang tài, cũng là lúc người ta cần judge nhất.
3. Chấm cả 2 chiều rồi gộp lại (BPC) là cách sửa rẻ và hiệu quả. Nhưng bài chỉ làm trên tiếng Anh, judge đóng, quy mô nhỏ. Project kiểm chứng lại trên tiếng Việt, dùng judge mở, so với người chấm.

## 10. Muốn tự kiểm chứng thì mở những phần này

Trang 1 (Figure 1) → trang 3 (Table 2, công thức 1, Figure 2) → trang 5 (Mục 3.2) → trang 6 (Table 4). Tổng cộng khoảng 4 trang. Phần còn lại có thể bỏ qua.

## Câu hỏi tự kiểm tra

1. ChatGPT cho Vicuna thắng 2.5% khi Vicuna đứng trước và 82.5% khi đứng sau. Vậy ChatGPT thiên về vị trí nào?
2. Nếu project chỉ chấm mỗi cặp **một lần**, luôn đặt Qwen ở vị trí A, thì kết quả xếp hạng sẽ bị sai theo cách nào?
3. Vì sao "MEC 3 lần + BPC" tốt hơn "MEC 6 lần" lại chứng minh vị trí là nguyên nhân thật?
4. Vì sao sau BPC không còn tính được flip rate?
