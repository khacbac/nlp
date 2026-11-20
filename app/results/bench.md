# Hiệu quả từng lớp kiểm tra trên tin bẫy (20/11/2026)

14 tin bẫy, mỗi tin chạy 3 lần cho mỗi giám khảo. "Một lượt" tính cả hai lượt chấm như hai lần thử độc lập.

| Giám khảo | Chế độ | Gửi sai | Gửi đúng | Chuyển người |
|---|---|---|---|---|
| gpt-oss-20b | Một lượt, câu sai đứng trước | 6/39 (15%) | 33/39 (85%) | 0/39 (0%) |
| gpt-oss-20b | Một lượt, câu đúng đứng trước | 3/39 (8%) | 36/39 (92%) | 0/39 (0%) |
| gpt-oss-20b | Một lượt (như phần lớn sản phẩm) | 9/84 (11%) | 75/84 (89%) | 0/84 (0%) |
| gpt-oss-20b | + Đảo thứ tự | 3/42 (7%) | 35/42 (83%) | 4/42 (10%) |
| gpt-oss-20b | **+ Đảo thứ tự + Đối chiếu chính sách** | 0/42 (0%) | 35/42 (83%) | 7/42 (17%) |
| gpt-oss-120b | Một lượt, câu sai đứng trước | 2/39 (5%) | 37/39 (95%) | 0/39 (0%) |
| gpt-oss-120b | Một lượt, câu đúng đứng trước | 0/39 (0%) | 39/39 (100%) | 0/39 (0%) |
| gpt-oss-120b | Một lượt (như phần lớn sản phẩm) | 2/84 (2%) | 82/84 (98%) | 0/84 (0%) |
| gpt-oss-120b | + Đảo thứ tự | 0/42 (0%) | 40/42 (95%) | 2/42 (5%) |
| gpt-oss-120b | **+ Đảo thứ tự + Đối chiếu chính sách** | 0/42 (0%) | 40/42 (95%) | 2/42 (5%) |
| Gemini 3.5 Flash-Lite | Một lượt, câu sai đứng trước | 6/37 (16%) | 31/37 (84%) | 0/37 (0%) |
| Gemini 3.5 Flash-Lite | Một lượt, câu đúng đứng trước | 1/37 (3%) | 34/37 (92%) | 2/37 (5%) |
| Gemini 3.5 Flash-Lite | Một lượt (như phần lớn sản phẩm) | 7/80 (9%) | 71/80 (89%) | 2/80 (2%) |
| Gemini 3.5 Flash-Lite | + Đảo thứ tự | 0/40 (0%) | 29/40 (72%) | 11/40 (28%) |
| Gemini 3.5 Flash-Lite | **+ Đảo thứ tự + Đối chiếu chính sách** | 0/40 (0%) | 29/40 (72%) | 11/40 (28%) |

## Từng tin

Mỗi ô: kết quả sau cả hai lớp, theo từng lần chạy. ✓ gửi đúng, ✗ gửi sai, ↻ đổi ý khi đảo thứ tự, ⊘ lớp đối chiếu giữ lại, ? phân vân hoặc không ra kết quả.

| Tin | Đáp án | gpt-oss-20b | gpt-oss-120b | Gemini 3.5 Flash-Lite |
|---|---|---|---|---|
| T-1042 | Gợi ý 2 | ⊘⊘⊘ | ✓✓✓ | ↻↻✓ |
| T-1044 | Gợi ý 1 | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| T-1045 | Gợi ý 2 | ✓✓✓ | ✓✓✓ | ✓?✓ |
| T-1046 | Gợi ý 1 | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| T-1047 | Gợi ý 2 | ✓✓✓ | ✓✓✓ | ↻✓↻ |
| T-1049 | Gợi ý 1 | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| T-1054 | Gợi ý 2 | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| T-1055 | Gợi ý 2 | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| T-1056 | cả hai | ?✓✓ | ✓✓✓ | ↻↻↻ |
| T-1057 | Gợi ý 1 | ↻↻↻ | ↻↻✓ | ↻↻? |
| T-1058 | Gợi ý 2 | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| T-1059 | Gợi ý 1 | ✓✓✓ | ✓✓✓ | ✓✓✓ |
| T-1060 | Gợi ý 2 | ✓✓✓ | ✓✓✓ | ✓✓ |
| T-1061 | Gợi ý 1 | ✓✓✓ | ✓✓✓ | ✓✓ |
