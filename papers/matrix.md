# Ma trận tổng hợp

Điền 1 hàng sau mỗi thẻ đọc. Bảng này sẽ thành phần Related Work của báo cáo.
Các ô có "?" là chưa kiểm chứng từ PDF, sửa lại khi đọc xong.

## 1. So sánh các paper

| Paper | Judge | Ngôn ngữ | Dữ liệu | Metric đo bias | Cách giảm bias | Phát hiện chính | So với người chấm? |
|---|---|---|---|---|---|---|---|
| Zheng 2023 (C2) ✓ | GPT-4, GPT-3.5, Claude-v1 | EN | MT-Bench 80 câu, 6 model; Arena 3K phiếu | Consistency, biased first/second | Swap bảo thủ, few-shot, CoT, reference | Consistency 65.0% (GPT-4) trên cặp gần như giống nhau (Table 2); 98.8% khi cặp chênh lệch (Table 11); câu mở bias nặng hơn (Table 10) | Có (58 chuyên gia, ~3K phiếu; GPT-4–người 85% vs người–người 81%) |
| Wang 2023 (C1) ✓ | GPT-4, ChatGPT | EN | Vicuna-80, 2 cặp model | Conflict Rate (Eq. 1) | MEC, BPC, HITLC | Conflict 46.3% (cặp gần) vs 5.0% (cặp chênh), GPT-4, Table 2; MEC+BPC kappa 0.24→0.37 (Table 4) | Có (3 tác giả, đa số; kappa người 0.54) |
| Shi 2024 (C3) ✓ v9 | 15 judges (12 đóng, 3 Llama mở) | EN | MTBench (30 ứng viên), DevBench (10 ứng viên), đấu với baseline cố định | Repetition Stability, Position Consistency, Preference Fairness | – (chỉ phân tích) | RS > 0.85 nên bias không ngẫu nhiên; quality gap lớn thì PC cao; độ dài ảnh hưởng yếu; hướng bias đổi theo task | **Không** (gap tính từ chính các judge) |
| Zheng 2024 (H1) | 20 LLMs | EN | MMLU, ARC, CSQA | Selection bias theo ID token | PriDe | Bias chủ yếu do prior của token A/B/C/D | Không (có đáp án) |
| Fu & Liu 2025 (H3) | 5 models | 25 ngôn ngữ | 5 task, dữ liệu song song | Fleiss' kappa giữa ngôn ngữ | Ensemble | Kappa ~0.3, kém nhất ở ngôn ngữ ít tài nguyên | ? |
| VMLU 2025 (V1) | LLM mở ? | VI | VMLU | ? | ? | LLM mở làm evaluator được, prompt ảnh hưởng | ? |
| **Project này** | Qwen2.5-Instruct | **VI** (+EN) | UIT-ViQuAD 2.0, 500 câu, câu trả lời dài | Flip Rate, First-Position Preference, Confidence Margin | Chấm 2 chiều, BPC | – | **Có, 4 người, 2 người/câu** |

## 2. Bài học → Quyết định thiết kế

Bảng này là phần quan trọng nhất để trình bày với thầy.

| Bài học từ paper | Nguồn | Quyết định trong project |
|---|---|---|
| Đổi thứ tự 2 câu trả lời là đủ làm judge đổi verdict | Wang 2023; Zheng 2023 | Chấm mỗi cặp 2 lần, chỉ đổi vị trí A/B |
| Bias mạnh nhất khi 2 câu trả lời có chất lượng gần nhau | Shi 2024; Zheng 2023 Table 11 | Dùng 3 model để có nhiều mức quality gap; RQ2 chia bin theo điểm người chấm |
| Model có prior với token "A"/"B" | Zheng 2024 | Đọc xác suất token làm độ tự tin (RQ3) |
| BPC giảm bias mà không cần train | Wang 2023 | Thử BPC cho RQ4 |
| Judge kém ổn định ở ngôn ngữ ít tài nguyên | Fu & Liu 2025 | Đo trên tiếng Việt, so với bản dịch tiếng Anh |
| Cho lý do trước rồi mới chấm (MEC) thì khớp người hơn | Wang 2023 Sec. 3.1, Table 4 | Prompt MT-Bench (Zheng 2023 Fig. 5) **vốn đã giải thích trước, verdict `[[A]]/[[B]]/[[C]]` ở cuối**, nên đọc logprob ở token verdict cuối. Cách này đã đáp ứng MEC (với k = 1) |
| Prompt MT-Bench có lựa chọn hòa `[[C]]` | Zheng 2023 Fig. 5; Shi 2024 Sec. 2.1 (chế độ 2 hoặc 3 lựa chọn) | **Chưa chốt:** giữ C (3 lựa chọn) hay bỏ (2 lựa chọn). Ảnh hưởng tới cách tính Flip Rate và Confidence Margin |
| Phải chứng minh bias không phải nhiễu ngẫu nhiên (Repetition Stability) | Shi 2024 Eq. 1, Table 2 | Chạy judge greedy (temperature 0) và ghi rõ; nếu sample thì đo RS trên khoảng 50 cặp |
| Cần báo cả consistency lẫn hướng lệch; PC cao chưa chắc đã công bằng | Zheng 2023 Table 2; Shi 2024 Fig. 2c | Báo Flip Rate + First-Position Preference (+ PF nếu kịp), kèm % lỗi format như Table 2 của Zheng |
| Câu hỏi mở bị bias nặng hơn | Zheng 2023 Table 10 | Củng cố việc chọn câu hỏi why/how |
| Quality gap lớn thì bias giảm, nhưng các paper đo gap bằng **chính LLM** | Wang 2023 Fig. 2; Zheng 2023 Table 11; Shi 2024 Fig. 2d-f | Project đo gap bằng **điểm người chấm** (RQ2), đây là đóng góp. Đã sửa proposal (.md và .html) theo đúng chữ của Shi: "strongly affected by the quality gap" |
| BPC gốc lấy trung bình **điểm 1–10** | Wang 2023 Eq. 2 | Project áp BPC lên **xác suất token A/B**, cần ghi rõ đây là điều chỉnh |
| (thêm khi đọc) | | |

## 3. Khoảng trống project lấp vào

- Chưa có nghiên cứu đo position bias trên **câu trả lời tiếng Việt dài** so với **người chấm**.
- Cả 3 paper core đều dùng judge **đóng** (trừ 3 Llama trong Shi) và **không dùng xác suất token**. Shi 2024 (Sec. 1) còn coi các cách cần truy cập nội bộ model là "không thực tế với model đóng". Project dùng judge mở Qwen nên đo được độ tự tin (RQ3).
- Quality gap trong cả 3 paper đều đo bằng điểm/verdict của **chính LLM**. Project đo bằng **người chấm**.
- Câu trả lời có **gold reference** (ViQuAD), khác với câu hỏi mở của MT-Bench/Vicuna.
