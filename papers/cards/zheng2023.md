# Zheng et al. 2023, Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena

- **Link:** [arXiv:2306.05685](https://arxiv.org/abs/2306.05685) (v4, 24/12/2023), NeurIPS 2023 Datasets & Benchmarks · code + dữ liệu: [FastChat/llm_judge](https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge)
- **Người đọc / ngày:** Claude viết nháp 18/11/2026. **Cần một thành viên đọc đối chiếu PDF rồi tick các ô ☐.**
- **Tầng:** Core. Đây là paper **khai sinh** khái niệm "LLM-as-a-judge"; prompt judge của project lấy từ đây.

## 1. Vấn đề
Benchmark cũ (MMLU, HELM…) không đo được người dùng thích câu trả lời nào trong hội thoại mở, còn thuê người chấm thì đắt. Câu hỏi đặt ra: một LLM mạnh (GPT-4) có thể chấm thay người không, và nó có những thiên lệch gì?

## 2. Phương pháp
- **3 kiểu judge** (Sec. 3.1):
  - **pairwise** (chọn A, B hoặc hòa);
  - **single answer grading** (chấm điểm 1–10 cho từng câu);
  - **reference-guided** (có đáp án mẫu kèm theo).
- **4 hạn chế được chỉ ra** (Sec. 3.3): position bias, verbosity bias, self-enhancement bias, yếu khi chấm toán/suy luận.
- **Đo position bias:** dùng GPT-3.5 sinh **2 câu trả lời rất giống nhau** (temperature 0.7) cho các câu turn-1 của MT-Bench, chấm 2 thứ tự, rồi báo:
  - **Consistency**: % giữ nguyên verdict khi swap;
  - % thiên về vị trí đầu, % thiên về vị trí sau;
  - % lỗi format.
  Có thêm prompt **"rename"** (đổi tên trợ lý) để tách bias do **vị trí** khỏi bias do **tên**.
- **Cách khắc phục** (Sec. 3.4):
  - **Swap bảo thủ:** chấm 2 lần; chỉ tính thắng khi thắng ở **cả 2** thứ tự, còn lại tính là **hòa**. Các thí nghiệm sau trong paper đều dùng cách này.
  - **Swap ngẫu nhiên:** gán vị trí ngẫu nhiên, chỉ hiệu quả khi số lượng ví dụ lớn.
  - **Few-shot judge**, **CoT judge**, **reference-guided judge**, và **fine-tune** một judge (Vicuna-13B).
- **Prompt pairwise mặc định** (Fig. 5, Phụ lục A): judge **giải thích trước**, sau đó mới xuất verdict dạng `[[A]]` / `[[B]]` / `[[C]]` (C = hòa).

## 3. Dữ liệu
- **MT-Bench:** 80 câu hỏi multi-turn, 8 loại. 6 model trả lời (GPT-4, GPT-3.5, Claude-v1, Vicuna-13B, Alpaca-13B, LLaMA-13B). **58 người chấm chuyên gia** (chủ yếu nghiên cứu sinh), tổng khoảng 3K phiếu (Sec. 4.1).
- **Chatbot Arena:** lấy mẫu 3K phiếu từ 30K phiếu crowdsourced.
- **Agreement** = xác suất 2 giám khảo ngẫu nhiên (thuộc 2 loại) đồng ý trên một câu ngẫu nhiên (Sec. 4.1, Phụ lục D.3).

## 4. Kết quả chính
| Kết quả | Con số | Nguồn | Đã tự kiểm tra? |
|---|---|---|---|
| Consistency khi swap (prompt default): Claude-v1 / GPT-3.5 / GPT-4 | 23.8% / 46.2% / 65.0% | Table 2 | ☐ |
| Phần lớn judge thiên về vị trí **đầu**. GPT-4: 30.0% thiên đầu, 5.0% thiên sau | | Table 2 | ☐ |
| Claude-v1 thiên về **tên** "Assistant A": khi đổi tên, consistency tăng 23.8% → 56.2% | | Table 2 | ☐ |
| Đổi prompt sang chấm điểm ("score") **làm GPT-4 kém đi**: 65.0% → 51.2% | | Table 9 | ☐ |
| Bias nặng ở câu hỏi mở: consistency writing 42%, humanities 36%, stem 44%; math/coding 86% | GPT-4 | Table 10 | ☐ |
| Theo cặp model (GPT-4 judge): GPT-3.5 vs Claude-v1 67.5% → vs Vicuna-13B 73.8% → vs LLaMA-13B 98.8% | | Table 11 | ☐ |
| Few-shot tăng consistency của GPT-4 65.0% → 77.5%, nhưng prompt dài hơn nên đắt gấp 4 lần, và có thể thêm bias mới | | Sec. 3.4, Table 12 | ☐ |
| Verbosity: tấn công "repetitive list" thành công với Claude-v1 và GPT-3.5 ở 91.3%, GPT-4 chỉ 8.7% | | Table 3 | ☐ |
| Agreement GPT-4 (pair) với người, không tính hòa (S2): **85%**, cao hơn agreement người–người (**81%**) | | Table 5, Sec. 4.2 | ☐ |
| Agreement GPT-4 với người tăng từ 70% lên gần 100% khi chênh lệch win rate của cặp model lớn dần | | Fig. 2, Sec. 4.2 | ☐ |
| Toán: tỉ lệ chấm sai giảm từ 14/20 (default) → 6/20 (CoT) → 3/20 (reference) | | Table 4 | ☐ |

## 5. Hạn chế
- **Tác giả nêu** (Sec. 6): chỉ đo helpfulness, bỏ qua safety; gộp nhiều tiêu chí thành một điểm; nguyên nhân của position bias mới chỉ là phỏng đoán ("dữ liệu train hoặc kiến trúc causal trái→phải"), để lại cho nghiên cứu sau.
- **Mình thấy:**
  - Thí nghiệm position bias (Table 2) dùng **2 câu trả lời gần như giống nhau, cùng do GPT-3.5 sinh**. Đây là tình huống cực đoan nhất, nên 65% không đại diện cho dữ liệu thật. Table 11 cho thấy với cặp thật, con số cao hơn nhiều.
  - Chỉ có tiếng Anh, judge đều là API đóng nên không có xác suất token.
  - Agreement đo theo **phiếu**, không phải theo cùng một bộ người chấm cho từng câu, nên khó so trực tiếp với kappa.

## 6. Mình lấy gì cho project ⭐
| Từ paper | Dùng trong project | RQ |
|---|---|---|
| Prompt pairwise Fig. 5 | Prompt judge (proposal ghi "MT-Bench pairwise judge prompt"). **Chú ý:** prompt này **giải thích trước, verdict `[[A]]/[[B]]/[[C]]` ở cuối**, nên phải đọc logprob ở token verdict cuối, **không phải** token đầu tiên của output. Điều này cũng giải quyết luôn điểm "MEC" trong thẻ Wang 2023 | RQ3 |
| Có lựa chọn hòa `[[C]]` | Cần quyết định: giữ 3 lựa chọn (giống paper) hay bỏ C (2 lựa chọn, dễ tính P(A) vs P(B) hơn). Nếu giữ C thì định nghĩa Flip Rate và Confidence Margin phải xử lý tie | RQ1, RQ3 |
| Consistency, biased-first, biased-second (Table 2) | Chính là Flip Rate (= 1 − consistency) và First-Position Preference của project. **Báo cáo đủ 4 cột như Table 2** (kèm % lỗi format) để so trực tiếp với tiếng Anh | RQ1 |
| Swap bảo thủ (thắng cả 2 lần mới tính thắng, ngược lại là hòa) | Chính là chiến lược "chỉ giữ verdict nhất quán" trong RQ4. Trích Sec. 3.4 | RQ4 |
| Table 11 + Fig. 2 | Bằng chứng cho RQ2 (gap lớn thì ít flip). Project đo gap bằng **điểm người chấm**, trực tiếp hơn | RQ2 |
| Table 10: câu hỏi mở bị bias nặng hơn | Hỗ trợ việc chọn câu hỏi "why/how" (câu trả lời dài, mở): dự kiến flip rate cao | RQ1 |
| Prompt "rename" | Thí nghiệm phụ rẻ: đổi nhãn A/B thành 1/2 hoặc X/Y để xem judge Qwen thiên về **vị trí** hay **nhãn token** (nối với Zheng 2024 / H1) | RQ3 |

## 7. Khoảng trống còn lại ⭐
- Không có ngôn ngữ nào ngoài tiếng Anh.
- Judge là API đóng, nên không phân tích được **độ tự tin** của judge khi nó flip.
- Chưa đo **câu trả lời có gold reference** từ một bộ dữ liệu đọc hiểu.
- Tác giả để mở: "judge mã nguồn mở" (Sec. 6, Future directions). Project dùng Qwen2.5 làm judge, nằm đúng hướng này.

## 8. Câu hỏi còn thắc mắc
- Table 2 tính "biased toward first" thế nào khi một lượt ra hòa và lượt kia ra A? Cần xem code FastChat.
- Project có dùng **turn-1 only** như MT-Bench không? (ViQuAD vốn là single-turn, nên không cần prompt multi-turn ở Fig. 9.)
