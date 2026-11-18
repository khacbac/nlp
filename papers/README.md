# Đọc paper cho project Position Bias

Mục tiêu: đọc để **trả lời 4 câu hỏi nghiên cứu (RQ1–4) trong `proposal.md`**, không phải để hiểu hết từng paper.
Kết quả cuối cùng là `matrix.md` (bảng tổng hợp) và bảng "Bài học → Quyết định thiết kế" trong đó.

## Cấu trúc thư mục

| File | Dùng để |
|---|---|
| `README.md` | Danh sách đọc + quy trình (file này) |
| `card-template.md` | Mẫu thẻ đọc 1 trang, copy cho mỗi paper |
| `prompts.md` | Prompt mẫu để hỏi AI khi đọc |
| `matrix.md` | Ma trận tổng hợp + bảng Bài học → Quyết định |
| `cards/` | Thẻ đọc đã làm, đặt tên `<tacgia><nam>.md`, vd `wang2023.md` |
| `pdf/` | PDF tải về (đã gitignore, repo là public) |

## Danh sách đọc

### Tầng 1: Core, đọc kỹ (~2–3h/bài)

| # | Paper | Link | Đọc phần nào | Trả lời RQ |
|---|---|---|---|---|
| C1 | Wang et al. 2023, *Large Language Models are not Fair Evaluators* | [arXiv:2305.17926](https://arxiv.org/abs/2305.17926) | Method (MEC, **BPC**, HITLC), Table 1–2 | RQ1, RQ4 |
| C2 | Zheng et al. 2023, *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* (NeurIPS) | [arXiv:2306.05685](https://arxiv.org/abs/2306.05685) | Sec. 3 (các loại bias, cách đo consistency), Table 2, Table 11 | RQ1, RQ2 |
| C3 | Shi et al. 2024, *Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge* | [arXiv:2406.07791](https://arxiv.org/abs/2406.07791) | Metrics (repetition stability, position consistency, preference fairness), phần quality gap | RQ1, RQ2 |

### Tầng 2: Survey, chỉ đọc taxonomy và phần bias (~1h/bài)

| # | Survey | Link | Đọc phần nào |
|---|---|---|---|
| S1 | Gu et al. 2024, *A Survey on LLM-as-a-Judge* | [arXiv:2411.15594](https://arxiv.org/abs/2411.15594) · [resources](https://awesome-llm-as-a-judge.github.io) | Taxonomy, phần reliability/bias & mitigation → đặt project mình vào đâu trong taxonomy |
| S2 | Li et al. 2024, *From Generation to Judgment: Opportunities and Challenges of LLM-as-a-judge* (EMNLP 2025) | [arXiv:2411.16594](https://arxiv.org/abs/2411.16594) | Taxonomy "what / how / benchmark" |
| S3 | Li et al. 2024, *LLMs-as-Judges: A Comprehensive Survey on LLM-based Evaluation Methods* | [arXiv:2412.05579](https://arxiv.org/abs/2412.05579) | Chỉ đọc nếu S1/S2 thiếu phần bias |

### Tầng 3: Hỗ trợ, đọc abstract + hình + kết luận (~15 phút/bài)

| # | Paper | Link | Lý do đọc |
|---|---|---|---|
| H1 | Zheng et al. 2024, *Large Language Models Are Not Robust Multiple Choice Selectors* (ICLR) | [arXiv:2309.03882](https://arxiv.org/abs/2309.03882) | Label token bias "A"/"B" + cách đo prior bằng xác suất token (PriDe) → RQ3 |
| H2 | Liu et al. 2023, *Lost in the Middle* (TACL 2024) | [arXiv:2307.03172](https://arxiv.org/abs/2307.03172) | Giải thích vì sao vị trí trong context ảnh hưởng |
| H3 | Fu & Liu 2025, *How Reliable is Multilingual LLM-as-a-Judge?* (Findings EMNLP) | [arXiv:2505.12201](https://arxiv.org/abs/2505.12201) | Bằng chứng judge kém ở ngôn ngữ ít tài nguyên → khoảng trống tiếng Việt |

### Tiếng Việt / bối cảnh Việt Nam (~15–30 phút/bài)

| # | Paper | Link | Liên quan |
|---|---|---|---|
| V1 | Bui et al. 2025, *VMLU Benchmarks: A comprehensive benchmark toolkit for Vietnamese LLMs* (ACL 2025) | [ACL Anthology](https://aclanthology.org/2025.acl-long.563) | **Gần nhất**: có dùng LLM mã nguồn mở làm evaluator cho tiếng Việt, ghi nhận prompt ảnh hưởng kết quả. Kiểm tra họ có đo position bias không |
| V2 | Nguyen et al. 2024, *ViLLM-Eval* (VLSP 2023) | [arXiv:2404.11086](https://arxiv.org/abs/2404.11086) | Benchmark tiếng Việt dạng trắc nghiệm, không dùng judge |
| V3 | Truong et al. 2024, *Crossing Linguistic Horizons: Finetuning and Comprehensive Evaluation of Vietnamese LLMs* | [arXiv:2403.02715](https://arxiv.org/abs/2403.02715) | Đánh giá LLM tiếng Việt diện rộng, không xoay quanh judge |

**Kết quả tìm kiếm (11/2026):** chưa tìm thấy survey viết bằng tiếng Việt, cũng chưa thấy paper nào đo position bias của LLM judge trên câu trả lời tiếng Việt so với người chấm. Đây là khoảng trống, nên ghi vào báo cáo: "đã tìm ở ACL Anthology, arXiv, VLSP và không thấy". Nếu ai tìm thêm được thì bổ sung vào bảng trên.

Đọc thêm nếu còn thời gian: Soumik 2026, *Judging the Judges: A Systematic Evaluation of Bias Mitigation Strategies in LLM-as-a-Judge Pipelines* ([arXiv:2604.23178](https://arxiv.org/abs/2604.23178)), so sánh các cách giảm bias, trong đó có swap.

## Quy trình đọc 1 paper

1. **Lượt 1 (10 phút):** đưa PDF cho AI, dùng prompt P1 trong `prompts.md`. Quyết định có đọc tiếp không.
2. **Lượt 2:** tự đọc phần method + bảng chính. Chỗ khó thì dùng P2/P3.
3. **Lượt 3 (chỉ bài core):** dùng P5, để AI hỏi ngược lại mình.
4. Điền thẻ `cards/<ten>.md` từ `card-template.md`. **Tự mở PDF kiểm tra mọi con số AI đưa ra** trước khi ghi.
5. Thêm 1 hàng vào `matrix.md`.

## Chia việc (gợi ý)

| Người | Paper |
|---|---|
| Bắc | C1, H1 |
| Nhân | C2, H2 |
| Việt Anh | C3, H3 |
| Quang | S1 (+S2), V1 |

Sau đó họp 30 phút, mỗi người trình bày thẻ của mình 5 phút.
