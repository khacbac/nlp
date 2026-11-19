# Shi et al. 2024, *Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge*: giải thích dễ hiểu

Bản giải thích trực quan, đọc trước thẻ `shi2024.md`. PDF: `papers/pdf/shi2024.pdf` (23 trang, chỉ cần khoảng 6 trang) · [arXiv:2406.07791](https://arxiv.org/abs/2406.07791), **bản v9 (11/2025)**

**Tóm tắt:** position bias **không phải ngẫu nhiên**. Bias thay đổi theo từng judge và từng loại task, bị ảnh hưởng mạnh bởi **chênh lệch chất lượng** giữa các câu trả lời, và gần như không phụ thuộc độ dài.

**Vị trí của bài so với 2 bài trước:**
- Wang 2023 và Zheng 2023 **phát hiện** position bias như một vấn đề phụ.
- Shi 2024 **mổ xẻ riêng** position bias: đo bằng 3 metric, trên 15 judge, rồi đi tìm nguyên nhân.

## 1. Câu chuyện mở đầu

Chi đọc Wang và Zheng xong thì thắc mắc: "Judge lật kết quả khi đổi chỗ. Nhưng nếu **không đổi chỗ**, chỉ hỏi lại y nguyên, nó có ra kết quả khác không? Nếu có, thì việc 'lật' có khi chỉ là **ngẫu nhiên**, chẳng liên quan gì đến vị trí."

Có thể hình dung bằng một cái cân đĩa. Trước khi kết luận "cân lệch về đĩa trái", phải làm 3 bước:
1. **Cân cùng một vật 3 lần ở cùng một đĩa.** Số đo có giống nhau không? Nếu không giống thì cân bị nhiễu, mọi kết luận sau đều vô nghĩa. → **Repetition Stability (RS)**
2. **Đổi vật sang đĩa kia.** Kết quả có giữ nguyên không? → **Position Consistency (PC)**
3. **Nếu không giữ nguyên thì cân lệch về phía nào**, trái hay phải? → **Preference Fairness (PF)**

```
Hỏi lặp lại y nguyên ──→ RS: có ổn định không?    (nếu không → dừng, bias chỉ là nhiễu)
        ↓ ổn định
Đổi chỗ 2 câu ─────────→ PC: có giữ nguyên người thắng không?
        ↓ không giữ
Hướng lệch ────────────→ PF: thiên câu đầu (−) hay câu sau (+)?
```

## 2. Thiết lập thí nghiệm (Mục 2.1, 3.1, trang 3–6)

- **15 judge:** 12 đóng (GPT, Claude, Gemini) và 3 mở (Llama-3.1-8B, Llama-3.3-70B, Llama-3.1-405B).
- **MTBench:** 30 model trả lời, mỗi model **đấu với một đối thủ cố định** là vicuna-13b. Judge chỉ chọn A hoặc B (2 lựa chọn).
- **DevBench:** câu hỏi lập trình, 10 model đấu với lời giải của người. Judge chọn A, B hoặc C = hòa (3 lựa chọn).
- **List-wise:** so 3 câu cùng lúc, hoán vị để mỗi câu được đứng đầu một lần.
- **Temperature = 1**, tức là judge có sampling nên có thể trả lời khác nhau giữa các lần. Vì vậy mới cần đo RS.
- **Không có người chấm.** Bài chỉ đo judge có **nhất quán** không, không đo judge có **đúng** không.

## 3. Ba metric (Mục 2.2, trang 3–4)

### RS (Repetition Stability): hỏi lại có ra như cũ không?

Hỏi cùng một prompt 3 lần. Judge trả lời A, A, B thì RS = 2/3 ≈ 0.67. Trả lời A, A, A thì RS = 1.0. Lấy trung bình trên mọi câu hỏi.

**Vì sao cần:** nếu RS thấp thì judge lật khi đổi chỗ **có thể chỉ là ngẫu nhiên**, chưa thể quy cho vị trí.

### PC (Position Consistency): đổi chỗ có giữ nguyên người thắng không?

Bằng **1 − Flip Rate** của project, và giống "consistency" của Zheng 2023. Không có gì mới.

### PF (Preference Fairness): lệch về phía nào, nhiều hay ít?

Thang đo từ −1 đến +1:

```
−1 ←──────────── 0 ────────────→ +1
luôn chọn câu đầu   công bằng   luôn chọn câu sau
(primacy)                       (recency)
```

**Vì sao phải nghĩ ra metric mới?** Hai cách đo cũ đều có lỗi.
- **Cách 1:** đếm số cặp thiên câu đầu, chia cho **tổng số cặp**. Con số phụ thuộc kích thước dữ liệu, nên khó so giữa các benchmark.
- **Cách 2:** đếm số cặp thiên câu đầu, chia cho **số cặp bị lật**. Phạt oan judge tốt.

Ví dụ cho cách 2: một judge giữ nguyên kết luận ở 95% số cặp, chỉ lật 5%, nhưng cả 5% đó đều thiên về câu đầu. Cách 2 sẽ báo "100% thiên câu đầu", nghe như judge rất tệ, dù thật ra judge gần như công bằng.

PF kết hợp cả 2 cách rồi chuẩn hóa (công thức 3), để judge nhất quán cao không bị phạt oan. Không cần nhớ công thức. Chỉ cần nhớ: **PF gần 0 là công bằng, và dấu cho biết hướng lệch.**

## 4. Đo "chênh lệch chất lượng" thế nào (Mục 2.3, trang 4)

Mỗi model đấu với đối thủ cố định trên nhiều câu hỏi. Kết quả mỗi câu được tính như sau:
- thắng ở cả 2 thứ tự: **thắng**;
- hòa ở cả 2 thứ tự: **hòa**;
- 2 lần mâu thuẫn: **cũng tính như hòa** (giống swap bảo thủ của Zheng).

Từ đó tính **tỉ lệ thắng tổng (owr)**, với hòa được tính nửa trận thắng.
- owr ≈ 0.5: ngang tài đối thủ, **chênh lệch nhỏ**.
- owr gần 0 hoặc gần 1: thua đậm hoặc thắng đậm, **chênh lệch lớn**.
- Chênh lệch chất lượng = |owr − 0.5|.

⚠️ **Điểm yếu quan trọng:** owr được tính **từ chính kết luận của các judge**. Tức là dùng judge để đo độ khó, rồi lại dùng độ khó đó giải thích vì sao judge bị bias. Lập luận này hơi vòng vo. **Project của bạn tránh được lỗi này** vì đo chênh lệch bằng **điểm người chấm**.

## 5. Các phát hiện chính (Mục 4, trang 6–8)

**① Bias không phải ngẫu nhiên** (Table 2, trang 7)
Các judge mạnh có RS > 0.85. Mạnh nhất (Claude-3.5-Sonnet, GPT-4, Llama-3.3-70B) có RS > 0.95. Judge trả lời gần như giống hệt khi hỏi lại, nên **việc lật khi đổi chỗ là do vị trí thật**.

**② Bias thay đổi theo judge và theo task** (Figure 2a-b, Table 2)
- Cùng là GPT-4, trên MTBench thì thiên câu **sau**, nhưng trên DevBench lại thiên câu **đầu**.
- Claude-3.5-Sonnet có PF = 0.01 (gần như công bằng) trên MTBench, nhưng PF = 0.22 (thiên câu sau) trên DevBench.

→ **Không thể đoán trước hướng lệch.** Đổi ngôn ngữ hoặc đổi loại câu hỏi là có thể đổi hướng. Đây là lý do điều kiện **tiếng Việt và tiếng Anh** của project có giá trị.

**③ Nhất quán cao chưa chắc đã công bằng** (Figure 2c)
Có judge PC cao nhưng mỗi khi lật thì vẫn lật về một phía. → Nên báo **cả hai**: tỉ lệ lật và hướng lệch.

**④ Chênh lệch chất lượng càng lớn thì càng nhất quán** (Figure 2d-f, trang 8)
Đồ thị PC theo owr có hình **chữ U**: thấp ở giữa (owr ≈ 0.5, ngang tài), cao ở hai đầu (thắng đậm hoặc thua đậm). Giống kết luận của Wang và Zheng, nhưng ở quy mô lớn hơn nhiều. Tuy vậy **có nhiều ngoại lệ**, nên chênh lệch chất lượng không phải yếu tố duy nhất.

**⑤ Độ dài gần như không ảnh hưởng** (Table 1, trang 6)
Độ dài câu hỏi, câu trả lời, prompt đều ảnh hưởng **rất yếu**. Chỉ có độ dài câu trả lời là có ý nghĩa thống kê, và chỉ với hướng lệch (PF).

**⑥ Ví dụ dễ và ví dụ khó** (Figure 3, trang 8)
- Hơn 50% dữ liệu là "dễ": trên 80% số judge đồng ý với nhau.
- Dưới 2% là "rất khó": đa số judge bất đồng.

Ví dụ khó thường có cả 3 đặc điểm cùng lúc: **judge bất đồng + chênh lệch nhỏ + nhiều judge bị position bias**.

## 6. Cần lưu ý khi trích dẫn

- **Ghi rõ bản v9.** Tên bài và số liệu đã đổi qua 9 phiên bản. Bản đầu tên là "...in Pairwise Comparative Assessments by LLMs".
- **Quy mô không khớp trong chính bài:** abstract ghi ">150,000" lượt chấm, Mục 3.1 ghi ">100,000". Nên trích con số nhỏ hoặc ghi rõ lấy từ phần nào.
- **Bài nói "strongly affected"**, không nói chênh lệch chất lượng là yếu tố **mạnh nhất**. Trong phân tích hồi quy (Table 1), các biến có ý nghĩa thống kê là **dòng judge, model trả lời, loại task**. (Proposal đã được sửa theo đúng ý này.)
- **Không có người chấm**, nên không trích bài này để nói về độ đúng của judge.
- **Temperature = 1**, khác với khi chạy greedy.

## 7. Giới hạn của bài, cũng là cơ hội cho project

| Bài này chưa làm | Project làm |
|---|---|
| Không có người chấm, chỉ đo nhất quán | 4 người chấm, đo được cả nhất quán **và** độ đúng |
| Chênh lệch chất lượng lấy từ chính các judge (vòng vo) | Lấy từ **điểm người chấm** |
| Chỉ có tiếng Anh | Tiếng Việt, có so với bản tiếng Anh |
| Không dùng xác suất token. Tác giả còn cho rằng cách cần truy cập bên trong model là "không thực tế" (Mục 1) | Qwen mở, đọc được xác suất, nên đo được độ tự tin (RQ3) |
| Judge mở chỉ có Llama | Qwen, chưa ai đo |
| Mỗi model đấu với một đối thủ cố định | Mọi cặp trong 3 model (3 cặp mỗi câu hỏi) |

## 8. Áp dụng vào project, từng RQ

- **Trước RQ1, kiểm tra RS:**
  - Nếu judge Qwen chạy **greedy** (temperature 0) thì RS = 1 hiển nhiên. Chỉ cần ghi rõ "chạy greedy nên kết quả xác định".
  - Nếu có **sampling** thì chạy lại khoảng 50 cặp 2–3 lần, **cùng thứ tự**, để đo RS. Nếu bỏ qua, người phản biện sẽ hỏi: "Lật vì vị trí hay vì ngẫu nhiên?"
- **RQ1:** báo **Flip Rate (= 1 − PC)** và **hướng lệch**. Có thể dùng PF để so trực tiếp với 15 judge trong Table 2.
- **RQ2:** Figure 2d-f là bằng chứng mạnh nhất. Project vẽ lại hình chữ U đó nhưng trục hoành là **chênh lệch điểm người chấm**. Đây là đóng góp rõ ràng, vì cả 3 bài core đều chỉ dùng điểm của LLM.
- **Phân tích thêm, chi phí thấp:** Shi tìm ví dụ khó bằng cách xem **các judge bất đồng**. Project có thể xem **2 người chấm bất đồng**: các cặp bị Qwen lật có trùng với các cặp mà 2 annotator chấm lệch nhau không? Nếu trùng thì cặp đó **khó với cả người lẫn máy**.
- **Điều kiện tiếng Việt và tiếng Anh:** phát hiện ② dự báo Qwen có thể **lệch hướng khác nhau** giữa 2 ngôn ngữ. Đây là giả thuyết đáng kiểm tra.

## 9. Đúc kết: 3 câu có thể nói với thầy

1. Position bias của judge mạnh là **có hệ thống**, không phải nhiễu: hỏi lại y nguyên thì kết quả giống hệt, nhưng đổi chỗ thì lật.
2. Hướng và mức độ bias **thay đổi theo judge và task**, không đoán trước được. Bias nặng nhất khi 2 câu trả lời ngang tài, gần như không phụ thuộc độ dài.
3. Bài không có người chấm và đo chênh lệch bằng chính LLM. Project bổ sung người chấm, đo chênh lệch bằng điểm người, và dùng xác suất token của judge mở. Bài này cho rằng việc cuối là "không thực tế" với model đóng.

## 10. Muốn tự kiểm chứng thì mở những trang này

Trang 1 (Abstract) → trang 2 (Figure 1: sơ đồ 3 metric) → trang 3–4 (Mục 2.2 metric, Mục 2.3 chênh lệch chất lượng; **bỏ qua công thức PF**) → trang 6–8 (Mục 4, Table 1, Table 2, Figure 2, Figure 3) → trang 9 (Limitations). Bỏ qua list-wise, phụ lục, các bảng hồi quy (Table 4–9).

## Câu hỏi tự kiểm tra

1. Vì sao phải đo RS **trước** khi kết luận có position bias?
2. Một judge có PC = 0.95 nhưng PF = −0.4. Judge này tốt hay tệ? Nên báo cáo thế nào?
3. Vì sao cách đo chênh lệch chất lượng của Shi bị coi là "vòng vo", và project tránh được bằng cách nào?
4. GPT-4 thiên câu sau trên MTBench nhưng thiên câu đầu trên DevBench. Điều này gợi ý gì cho điều kiện tiếng Việt và tiếng Anh?
5. Nếu Qwen chạy greedy, có cần đo RS không? Vì sao?
