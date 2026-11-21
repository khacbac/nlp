# Hiệu quả từng lớp kiểm tra trên tin bẫy (21/11/2026)

13 tin bẫy, mỗi tin chạy 1 lần cho mỗi giám khảo. "Một lượt" tính cả hai lượt chấm như hai lần thử độc lập.

| Giám khảo | Chế độ | Gửi sai | Gửi đúng | Chuyển người |
|---|---|---|---|---|
| gpt-oss-20b | Một lượt, **không có văn bản luật** trong prompt | 10/26 (38%) | 16/26 (62%) | 0/26 (0%) |
| gpt-oss-20b | Một lượt, câu sai đứng trước | 2/12 (17%) | 10/12 (83%) | 0/12 (0%) |
| gpt-oss-20b | Một lượt, câu đúng đứng trước | 2/12 (17%) | 9/12 (75%) | 1/12 (8%) |
| gpt-oss-20b | Một lượt (như phần lớn sản phẩm) | 4/26 (15%) | 21/26 (81%) | 1/26 (4%) |
| gpt-oss-20b | + Đảo thứ tự | 1/13 (8%) | 9/13 (69%) | 3/13 (23%) |
| gpt-oss-20b | **+ Đảo thứ tự + Đối chiếu luật** | 1/13 (8%) | 9/13 (69%) | 3/13 (23%) |
| gpt-oss-120b | Một lượt, **không có văn bản luật** trong prompt | 13/26 (50%) | 13/26 (50%) | 0/26 (0%) |
| gpt-oss-120b | Một lượt, câu sai đứng trước | 0/11 (0%) | 11/11 (100%) | 0/11 (0%) |
| gpt-oss-120b | Một lượt, câu đúng đứng trước | 0/11 (0%) | 11/11 (100%) | 0/11 (0%) |
| gpt-oss-120b | Một lượt (như phần lớn sản phẩm) | 0/24 (0%) | 24/24 (100%) | 0/24 (0%) |
| gpt-oss-120b | + Đảo thứ tự | 0/12 (0%) | 12/12 (100%) | 0/12 (0%) |
| gpt-oss-120b | **+ Đảo thứ tự + Đối chiếu luật** | 0/12 (0%) | 12/12 (100%) | 0/12 (0%) |

## Từng tin

Mỗi ô: kết quả sau cả hai lớp, theo từng lần chạy. ✓ gửi đúng, ✗ gửi sai, ↻ đổi ý khi đảo thứ tự, ⊘ lớp đối chiếu giữ lại, ? phân vân hoặc không ra kết quả.

| Tin | Đáp án | gpt-oss-20b | gpt-oss-120b |
|---|---|---|---|
| T-2001 | Gợi ý 1 | ? | ✓ |
| T-2002 | Gợi ý 2 | ↻ | ✓ |
| T-2003 | Gợi ý 1 | ✓ | ✓ |
| T-2004 | Gợi ý 2 | ✓ | ✓ |
| T-2005 | Gợi ý 1 | ✓ | ✓ |
| T-2006 | Gợi ý 1 | ✓ | ✓ |
| T-2007 | Gợi ý 2 | ↻ | ✓ |
| T-2008 | Gợi ý 2 | ✓ | ✓ |
| T-2009 | Gợi ý 1 | ✓ | ✓ |
| T-2010 | Gợi ý 1 | ✓ | ✓ |
| T-2011 | Gợi ý 1 | ✓ | ✓ |
| T-2012 | Gợi ý 2 | ✗ | – |
| T-2013 | cả hai | ✓ | ✓ |
