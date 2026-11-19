# Zheng et al. 2023, *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*: giải thích dễ hiểu

Bản giải thích trực quan, đọc trước thẻ `zheng2023.md`. PDF: `papers/pdf/zheng2023.pdf` (29 trang, chỉ cần khoảng 7 trang) · [arXiv:2306.05685](https://arxiv.org/abs/2306.05685) · NeurIPS 2023

**Tóm tắt:** GPT-4 có thể chấm thay người, mức đồng ý với người tương đương mức người đồng ý với nhau (trên 80%). Nhưng judge có 4 điểm yếu, trong đó có position bias, và bài đưa ra cách khắc phục cho từng điểm.

**Vì sao bài này quan trọng với project:** đây là bài **khai sinh** khái niệm "LLM-as-a-judge". **Prompt judge mà project sẽ dùng lấy từ bài này** (Figure 5).

## 1. Câu chuyện mở đầu

Bình muốn xếp hạng 6 chatbot. Cách chuẩn là thuê người chấm: nhóm tác giả thuê **58 chuyên gia** (chủ yếu nghiên cứu sinh) và thu được khoảng 3.000 phiếu chấm. Cách này đắt và chậm, mỗi lần có model mới lại phải thuê người chấm lại.

Bình nghĩ ra cách khác: đưa câu hỏi và 2 câu trả lời cho GPT-4, hỏi "câu nào tốt hơn?". Cách này rẻ, nhanh, chạy lại lúc nào cũng được. Bài báo trả lời 2 câu hỏi:
1. GPT-4 chấm có giống người không?
2. GPT-4 chấm sai theo những kiểu nào?

```
Câu hỏi + 2 câu trả lời → GPT-4 judge → "[[A]]" / "[[B]]" / "[[C]] hòa"
                                         ↓ so với
                              58 chuyên gia (~3K phiếu)
```

## 2. Ba kiểu judge (Mục 3.1, trang 4)

| Kiểu | Hình dung | Ưu / nhược |
|---|---|---|
| **Pairwise** | Đặt 2 bài văn cạnh nhau, hỏi bài nào hay hơn | Phân biệt được khác biệt nhỏ, nhưng số cặp tăng rất nhanh khi có nhiều model, và **có position bias** |
| **Single answer grading** | Chấm điểm 1–10 cho từng bài riêng lẻ | Dễ mở rộng, nhưng điểm tuyệt đối dễ dao động |
| **Reference-guided** | Chấm có đáp án mẫu kèm theo | Tốt cho toán, suy luận |

Project dùng **pairwise**, vì chỉ có so sánh 2 câu mới có "vị trí" để đổi chỗ.

## 3. Bốn điểm yếu của judge (Mục 3.3, trang 4–5)

### 3a. Position bias (Table 2, trang 5)

Thí nghiệm được thiết kế **khó nhất có thể**: cho GPT-3.5 trả lời **cùng một câu hỏi 2 lần**, nên 2 câu trả lời gần như giống hệt nhau. Sau đó cho judge chấm cả 2 thứ tự.

| Judge | Giữ nguyên kết luận khi đổi chỗ | Thiên về câu đầu | Thiên về câu sau |
|---|---|---|---|
| Claude-v1 | **23.8%** | 75.0% | 0.0% |
| GPT-3.5 | 46.2% | 50.0% | 1.2% |
| GPT-4 | **65.0%** | 30.0% | 5.0% |

Có thể hình dung như sau: đưa giám khảo 2 bài văn gần như giống hệt, hỏi bài nào hay hơn. Một giám khảo công bằng sẽ nói "ngang nhau" ở cả 2 lần. Thực tế thì giám khảo thường chọn **bài đọc trước**.

**Mẹo "rename":** tác giả đổi tên "Assistant A/B" thành tên khác để xem judge thiên về **vị trí** hay thiên về **cái tên**. Claude-v1 tăng từ 23.8% lên 56.2%, nghĩa là một phần bias của Claude là do nó thích **chữ "A"**. Ý này nối sang bài Zheng 2024 về label token bias.

### 3b. Verbosity bias: thích câu dài (Table 3, trang 5)

Tác giả lấy câu trả lời dạng danh sách rồi **chép lại danh sách đó bằng từ khác** và ghép vào đầu. Câu trả lời dài gấp đôi nhưng không thêm thông tin gì. Claude-v1 và GPT-3.5 bị lừa **91.3%**, GPT-4 chỉ bị lừa 8.7%.

→ Project đã chặn trước: prompt yêu cầu câu trả lời 2–4 câu, không định dạng.

### 3c. Self-enhancement bias: thích câu trả lời của chính mình (trang 5)

GPT-4 cho chính nó tỉ lệ thắng cao hơn khoảng 10%, Claude cho chính nó cao hơn khoảng 25%. Nhưng tác giả **không kết luận được**, vì dữ liệu ít và chênh lệch nhỏ.

### 3d. Yếu khi chấm toán (Table 4, trang 5)

GPT-4 **tự giải được** bài toán, nhưng khi chấm lại bị câu trả lời sai dẫn dắt. Cách sửa: **đưa đáp án mẫu** vào prompt. Số lần chấm sai giảm từ 14/20 xuống 3/20.

## 4. Bias nặng nhất ở đâu (Phụ lục D.1, Table 10–11, trang 25)

**Theo loại câu hỏi (Table 10):** câu hỏi **mở** bị bias nặng, còn câu hỏi có đáp án rõ thì nhẹ.

| Loại câu hỏi | Giữ nguyên kết luận |
|---|---|
| humanities | 36% |
| writing | 42% |
| stem | 44% |
| math, coding | 86% |

**Theo cặp model (Table 11, GPT-4 judge):** hai model càng chênh lệch thì càng ít bị bias.

```
GPT-3.5 vs Claude-v1   (ngang tài)    → 67.5% giữ nguyên
GPT-3.5 vs Vicuna-13B  (hơi chênh)    → 73.8%
GPT-3.5 vs LLaMA-13B   (chênh rất rõ) → 98.8%
```

Kết luận giống Wang 2023: **khi khó phân biệt, judge dựa vào vị trí.**

## 5. Cách khắc phục (Mục 3.4, trang 6)

**Swap bảo thủ.** Đây là cách bài này dùng cho mọi thí nghiệm sau. Chấm 2 lần với 2 thứ tự. Một câu **chỉ được tính thắng nếu thắng ở cả 2 lần**. Nếu 2 lần mâu thuẫn thì **tính là hòa**.

Giống thể thức lượt đi, lượt về trong bóng đá: phải thắng cả sân nhà lẫn sân khách mới chắc là đội mạnh hơn. Thắng một trận, thua một trận thì coi như hòa.

**Các cách khác:**
- **Few-shot:** đưa 3 ví dụ chấm mẫu. GPT-4 tăng từ 65.0% lên 77.5%, nhưng prompt dài hơn nên **đắt gấp 4 lần**, và có thể sinh ra bias mới.
- **CoT:** cho judge tự giải trước rồi mới chấm.
- **Reference-guided:** đưa đáp án mẫu vào prompt.

So với Wang 2023: swap bảo thủ **bỏ đi** những cặp mâu thuẫn (biến thành hòa), còn BPC **gộp** 2 lần chấm thành một (lấy trung bình). RQ4 của project so sánh chính 2 cách này.

## 6. Mức đồng ý với người (Mục 4.2, Table 5, Figure 2, trang 8)

- GPT-4 đồng ý với chuyên gia **85%**, cao hơn mức các chuyên gia đồng ý với nhau (**81%**). Con số này tính khi bỏ các phiếu hòa.
- Khi người chấm khác ý GPT-4, tác giả cho họ xem lời giải thích của GPT-4. 75% thấy hợp lý, 34% đổi ý theo GPT-4.
- Figure 2: mức đồng ý tăng từ 70% lên gần 100% khi 2 model càng chênh lệch.

**Nghịch lý cần hiểu:** vì sao bias nặng mà mức đồng ý với người vẫn cao?
- Thí nghiệm bias (Table 2) dùng 2 câu **gần như giống hệt nhau**, là trường hợp cực đoan nhất.
- Thí nghiệm đồng ý dùng câu trả lời thật, thường có chênh lệch, và đã áp dụng **swap bảo thủ**.

→ Judge tốt **trung bình**, nhưng không đáng tin **ở các cặp ngang tài**. Đây chính là điều project đo trên tiếng Việt.

## 7. Prompt judge: phần project dùng trực tiếp (Figure 5, trang 14)

Cấu trúc prompt:
1. Đóng vai giám khảo công bằng. Xét độ hữu ích, liên quan, chính xác, chiều sâu…
2. **"Begin your evaluation by comparing the two responses and provide a short explanation"**, tức là **giải thích trước**.
3. "Avoid any position biases…", "Do not allow the length…", "Do not favor certain names…"
4. **Cuối cùng** mới xuất verdict: `[[A]]`, `[[B]]` hoặc `[[C]]` (hòa).

**Hệ quả cho project:**
- Verdict nằm **ở cuối**, nên phải đọc xác suất tại token verdict (sau dấu `[[`), **không phải** token đầu tiên của output.
- Cách này khớp với khuyến nghị "lý do trước, điểm sau" (MEC) của Wang 2023.
- Có lựa chọn **hòa `[[C]]`**. Nhóm cần chốt: giữ (3 lựa chọn, giống paper) hay bỏ (chỉ còn so P(A) với P(B), đơn giản hơn).
- Prompt **đã có câu "tránh position bias"** mà bias vẫn còn. Điều này cho thấy chỉ dặn trong prompt là không đủ.

## 8. Cần lưu ý khi trích dẫn

- **Con số 65.0% của GPT-4 là trên cặp gần như giống hệt nhau.** Đừng trích nó như "GPT-4 lật 35% trong thực tế". Với cặp thật, con số là 67.5–98.8% (Table 11).
- **Mức đồng ý đo theo phiếu ngẫu nhiên** (Phụ lục D.3), không phải Cohen's kappa. Không so trực tiếp với kappa của nhóm được.
- **85% là khi bỏ các phiếu hòa** (cài đặt S2). Nếu tính cả hòa thì chỉ khoảng 66%.
- Đây là GPT-4, Claude-v1, GPT-3.5 bản 2023, toàn bộ là model đóng.

## 9. Giới hạn của bài, cũng là cơ hội cho project

| Bài này chưa làm | Project làm |
|---|---|
| Chỉ có tiếng Anh | Tiếng Việt, có so với bản tiếng Anh |
| Judge đóng, không xem được xác suất | Qwen mở, đọc được xác suất token |
| Nguyên nhân bias chỉ là phỏng đoán ("dữ liệu train hoặc kiến trúc trái→phải") | Đo xem bias có gắn với độ tự tin thấp không (RQ3) |
| Tác giả đề xuất hướng tương lai là judge mã nguồn mở (Mục 6) | Project dùng đúng judge mở |
| Câu hỏi mở, không có đáp án | ViQuAD có gold answer, làm mốc khách quan cho người chấm |

## 10. Áp dụng vào project, từng RQ

- **RQ1 (tỉ lệ lật):**
  - Báo cáo **đủ 4 cột** như Table 2: giữ nguyên, thiên câu đầu, thiên câu sau, lỗi format.
  - Từ đó so trực tiếp được: "GPT-4 tiếng Anh giữ nguyên 65–99% tùy cặp. Qwen trên tiếng Việt thì sao?"
  - Table 10 dự báo câu hỏi **why/how** (câu hỏi mở) sẽ có flip rate cao.
- **RQ2 (lật khi ngang tài):** Table 11 và Figure 2 là bằng chứng. Project chia nhóm theo **điểm người chấm**, trực tiếp hơn cách chia theo cặp model.
- **RQ3 (độ tự tin):** có thể làm thêm thí nghiệm "rename" với chi phí thấp, đổi nhãn A/B thành 1/2, để xem Qwen thiên về **vị trí** hay về **token "A"**.
- **RQ4:** so 3 cách:
  - chỉ dùng lần chấm thứ nhất;
  - **swap bảo thủ** (Zheng: mâu thuẫn thì tính hòa);
  - **BPC** (Wang: lấy trung bình 2 lần).

  Xem cách nào khớp với người chấm hơn.
- **Một câu hỏi cần nhóm chốt:** judge có được **xem gold answer** không? Reference-guided giúp giảm lỗi chấm sai nhiều (Table 4). Nhưng nếu judge xem gold mà người chấm cũng xem gold, thì cả hai cùng có mốc, so sánh sẽ công bằng hơn.

## 11. Đúc kết: 3 câu có thể nói với thầy

1. LLM judge (GPT-4) đồng ý với chuyên gia ở mức ngang chuyên gia đồng ý với nhau, nên dùng judge là hợp lý.
2. Nhưng judge có position bias mạnh nhất ở câu hỏi mở và cặp ngang tài. Chỉ dặn "đừng thiên vị" trong prompt là không đủ, cần đổi chỗ để kiểm tra.
3. Bài chỉ làm trên tiếng Anh với judge đóng. Project dùng chính prompt của bài, kiểm chứng lại trên tiếng Việt với judge mở và xác suất token.

## 12. Muốn tự kiểm chứng thì mở những trang này

Trang 1 (Abstract) → trang 2 (Figure 1) → trang 4–6 (Mục 3.1, 3.3, 3.4, Table 2–4) → trang 8 (Table 5, Figure 2) → trang 14 (Figure 5: prompt) → trang 25 (Table 10–11). Bỏ qua Chatbot Arena (Mục 2.3, 4.3), Mục 5, phần lớn phụ lục.

## Câu hỏi tự kiểm tra

1. Vì sao 65.0% của GPT-4 ở Table 2 **không** đại diện cho chất lượng chấm thực tế?
2. Mẹo "rename" giúp phân biệt 2 loại bias nào?
3. Swap bảo thủ khác BPC thế nào? Một cặp bị lật thì mỗi cách xử lý ra sao?
4. Vì sao project phải đọc xác suất ở token **cuối** chứ không phải token đầu của output judge?
5. Bias nặng mà mức đồng ý với người vẫn cao: giải thích nghịch lý này.
