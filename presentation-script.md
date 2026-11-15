# Kịch bản trình bày: Thứ tự có quan trọng không?

Đề xuất đồ án cuối kỳ NLP501.22, nhóm ABNQ. Tổng thời gian khoảng 5 phút, gồm 10 màn.

## Chuẩn bị

- Mở `proposal.html#present-1` trong Chrome và bật toàn màn hình (F11 hoặc ⌃⌘F).
- Dùng phím → và ← để chuyển màn. Esc để thoát chế độ trình chiếu.
- Màu nền sáng hay tối đi theo cài đặt sáng/tối của máy. Kiểm tra trước trên máy chiếu: nền tối thường dễ đọc hơn trong phòng sáng đèn.
- Mở sẵn trang trước khi lên. Máy cần có mạng để tải font; nếu mất mạng, trang vẫn hiển thị bằng font hệ thống.
- Màn 4 (40 giây), màn 9 (20 giây) và màn 10 (30 giây) là các màn quan trọng nhất. Nếu đã quá 2 phút 20 giây khi rời màn 5, hãy rút gọn màn 6 để giữ đủ thời gian cho màn 9 và 10.

| Màn | Nội dung | Thời gian | Hết màn lúc |
|---|---|---|---|
| 1 | Tiêu đề | 15 giây | 0:15 |
| 2 | Cô Hoa chấm bài | 30 giây | 0:45 |
| 3 | Bằng chứng ở người | 25 giây | 1:10 |
| 4 | Bằng chứng ở LLM | 40 giây | 1:50 |
| 5 | Nguyên nhân | 25 giây | 2:15 |
| 6 | Khoảng trống | 25 giây | 2:40 |
| 7 | Bốn câu hỏi nghiên cứu | 35 giây | 3:15 |
| 8 | Hướng tiếp cận | 35 giây | 3:50 |
| 9 | Vì sao 3 mô hình, không phải 2 | 20 giây | 4:10 |
| 10 | Lựa chọn kỹ thuật | 30 giây | 4:40 |
| 11 | Tóm tắt đề tài và đầu ra | 25 giây | 5:05 |
| 12 | Toàn cảnh quy trình (cảm ơn, hỏi đáp) | — | — |
| 13 | Tiêu chí đánh giá (dự phòng khi hỏi đáp) | — | — |

Nếu bị giới hạn đúng 5 phút, bỏ câu "Ngoài ra, nhóm so tỉ lệ flip giữa tiếng Việt và tiếng Anh…" ở màn 7, vì màn 11 đã nhắc lại ý này.

Phần in nghiêng trong ngoặc vuông là hướng dẫn hành động, không đọc thành lời.

---

## Màn 1 · Tiêu đề (15 giây)

> Em chào thầy và các bạn. Em là [tên], đại diện nhóm ABNQ. Đề tài của nhóm là thiên vị vị trí của LLM judge, kiểm chứng trên tiếng Việt. Câu hỏi của nhóm rất đơn giản: thứ tự có quan trọng không?

*[Chỉ vào cán cân: hai thẻ X và Y đổi chỗ, nhưng cán cân vẫn nghiêng về bên trái.]*

## Màn 2 · Cô Hoa chấm bài (30 giây)

> Thử hình dung cô Hoa chọn bài văn hay hơn giữa bài của An và bài của Bình. Sáng thứ Hai, cô đọc bài của An trước và chọn An. Sáng thứ Ba, vẫn hai bài đó, cô đọc bài của Bình trước và chọn Bình. Hai bài không đổi một chữ, nhưng người thắng đã đổi.
>
> Trong đề tài, cô Hoa là một LLM được nhờ chấm, gọi là **judge**. Mỗi lần judge đổi ý như vậy là một **flip**. Thói quen này gọi là **position bias**.

*[Câu cuối là định nghĩa ba thuật ngữ. Đọc chậm ở câu này.]*

## Màn 3 · Bằng chứng ở người (25 giây)

> Hiện tượng này đã được đo trên người thật. Bruine de Bruin (2005) phân tích dữ liệu Eurovision và trượt băng nghệ thuật: tiết mục diễn càng về sau thì điểm càng cao.

*[Chỉ vào biểu đồ cột nhỏ. Đây là sơ đồ minh hoạ xu hướng, không phải số liệu của bài báo, nên đừng đọc độ cao cột như con số thật.]*

> Zhao và cộng sự (2017) phân tích gần 150 nghìn điểm của 88 người chấm bài luận, và thấy điểm của một bài bị kéo về gần điểm của bài chấm ngay trước.

## Màn 4 · Bằng chứng ở LLM (40 giây)

> Với LLM thì sao? Zheng và cộng sự, trong bài giới thiệu MT-Bench ở NeurIPS 2023, cho ba mô hình chấm cùng một cặp câu trả lời rất giống nhau, theo cả hai thứ tự.

*[Chỉ vào biểu đồ trên cùng.]*

> Phần đầu mỗi thanh là tỉ lệ judge giữ nguyên phán quyết sau khi đổi chỗ, phần màu hồng là khi judge chọn câu đứng trước. Claude-v1 chỉ nhất quán ở 23,8% số cặp; 75% số cặp nó chọn câu đứng trước. GPT-3.5 nhất quán ở 46%. Ngay cả GPT-4 cũng chỉ đạt 65%.

*[Chỉ xuống ô dưới bên trái.]*

> Wang và cộng sự (2023) còn cho thấy, khi ChatGPT làm giám khảo, chỉ cần đổi thứ tự là Vicuna-13B "thắng" được ChatGPT ở 66 trên 80 câu hỏi.

*[Chỉ xuống ô dưới bên phải.]*

> Khi GPT-4 chấm, hai mô hình càng chênh nhau rõ thì nó càng nhất quán, từ 67,5% lên 98,8%. Nghĩa là thiên vị mạnh nhất khi hai câu trả lời khó phân biệt, cũng là lúc ta cần judge nhất.

## Màn 5 · Nguyên nhân (25 giây)

> Vì sao lại như vậy? Ở cả hai phía, nguyên nhân chưa được xác định chắc chắn. Ô bên trái là các giải thích cho con người. Ô bên phải là ba giải thích cho LLM: do dữ liệu huấn luyện hoặc do kiến trúc đọc từ trái sang phải; mô hình có sẵn thói quen chọn nhãn "A" hơn "B", bất kể nội dung, gọi là token bias; và mô hình dùng thông tin ở đầu, cuối ngữ cảnh tốt hơn phần giữa.
>
*[Chỉ vào khung hồng "Điểm gặp nhau".]*

> Điểm chung là thứ tự chi phối mạnh nhất khi hai thứ cần so khó phân biệt. Nhóm không khẳng định người và máy có cùng cơ chế.

## Màn 6 · Khoảng trống (25 giây)

> Xếp lại: ta đã biết con người bị thứ tự chi phối, LLM judge tiếng Anh cũng flip, và judge kém ổn định khi đổi ngôn ngữ. Fu và Liu (2025) đo trên 25 ngôn ngữ, độ nhất quán chỉ đạt kappa khoảng 0,3, kém nhất ở ngôn ngữ ít tài nguyên.
>
> Còn tiếng Việt, với câu trả lời dài và có đối chiếu người chấm, nhóm chưa tìm thấy nghiên cứu nào. Đề tài này nhắm vào chỗ trống đó.

*[Chỉ vào cột cuối, cột có gạch hồng phía trên.]*

## Màn 7 · Bốn câu hỏi nghiên cứu (35 giây)

*[Đi lần lượt bốn thẻ: trên trái, trên phải, dưới trái, dưới phải. Mỗi thẻ đọc câu hỏi trên slide, rồi nói thêm một câu theo chuyện cô Hoa.]*

> Nhóm đặt bốn câu hỏi.
>
> Một: judge flip thường xuyên đến mức nào, tức là cô Hoa có hay đổi ý không. Nhóm đo bằng tỉ lệ flip.
> Hai: flip có dồn vào các cặp gần ngang nhau không, hay cả khi một bài hơn hẳn cô vẫn đổi ý. Nhóm đo flip theo độ chênh điểm của người chấm.
> Ba: lúc flip, judge có đang lưỡng lự không. Nhóm đo bằng xác suất judge gán cho "A" và "B"; gần 50/50 nghĩa là lưỡng lự.
> Bốn: nếu chỉ giữ những phán quyết trùng nhau ở cả hai thứ tự, kết quả có khớp người chấm hơn không.
>
> Ngoài ra, nhóm so tỉ lệ flip giữa tiếng Việt và tiếng Anh trên cùng nội dung.

## Màn 8 · Hướng tiếp cận (35 giây)

*[Đi theo mũi tên từ trái sang phải. Ở ô LLM judge, chỉ vào hai lượt: X và Y đổi vị trí A, B.]*

> Hướng tiếp cận gồm bốn bước, đi từ trái sang phải.
>
> Một: lấy 500 câu hỏi "vì sao", "như thế nào" có đáp án từ UIT-ViQuAD 2.0, bộ đọc hiểu tiếng Việt của VLSP 2021, mỗi đoạn văn chỉ lấy một câu.
> Hai: cho ba mô hình dùng miễn phí là Qwen, gpt-oss và Gemini trả lời cùng các câu hỏi đó. Mỗi câu có ba câu trả lời, ghép thành ba cặp X và Y, tổng cộng 1500 cặp.
> Ba: chấm song song. Bốn người chấm, mỗi câu trả lời do hai người cho điểm độc lập. LLM judge chấm mỗi cặp hai lượt: lượt đầu X ở vị trí A, lượt sau đổi chỗ, Y ở vị trí A. Mỗi lượt lưu lại xác suất "A" và "B".
> Bốn: đánh giá theo sáu tiêu chí trong ô cuối, từ tỉ lệ flip, độ ưa vị trí đầu, độ tự tin, đến độ khớp với người chấm sau khi cân bằng hai thứ tự. Nhóm không huấn luyện mô hình nào.

## Màn 9 · Vì sao 3 mô hình, không phải 2 (20 giây)

*[Chỉ vào biểu đồ thanh, đọc hai thanh GPT-4.]*

> Mỗi cặp vẫn chỉ là hai câu trả lời đổi chỗ, như cô Hoa. Nhưng vì sao nhóm dùng ba mô hình? Wang và cộng sự cho cùng GPT-4 chấm hai loại cặp: cặp gần ngang nhau thì flip 46%, cặp chênh rõ chỉ 5%. Độ chênh quyết định mức thiên vị.
>
> Ba mô hình cho ba cặp mỗi câu, với độ chênh khác nhau, nên đo được cả vùng sát nhau lẫn vùng chênh rõ. Đây cũng là cách làm của các nghiên cứu trước, trong bảng phía dưới.

*[Nếu bị hỏi vì sao không ghép với một mô hình mốc như Shi et al.: ghép mọi cặp cho đủ 3 mức chênh mà chỉ cần 3 mô hình. Nếu bị hỏi về độc lập thống kê: 3 cặp cùng câu hỏi không độc lập, nên khoảng tin cậy tính bằng bootstrap theo câu hỏi.]*

## Màn 10 · Lựa chọn kỹ thuật (30 giây)

*[Đọc theo từng dòng, chỉ nói ý chính của cột "Vì sao chọn", không đọc nguyên văn.]*

> Mỗi kỹ thuật được chọn vì một lý do cụ thể.
> **Chấm theo cặp, cả hai thứ tự:** thiên vị vị trí chỉ lộ ra khi có hai vị trí để đổi. Chấm từng câu riêng lẻ thì không đo được.
> **Ba mô hình free sinh câu trả lời:** Qwen, gpt-oss, Gemini mạnh yếu khác nhau ở tiếng Việt, nên có cả cặp chênh rõ lẫn cặp gần ngang nhau. Đây cũng là các mô hình mà một nhóm ít kinh phí thực sự phải chọn giữa.
> **Judge mã mở Qwen2.5:** nhóm cần xác suất token, mà không phải API trả phí nào cũng trả về. Qwen chạy được trên Colab và có hỗ trợ tiếng Việt.
> **Xác suất token "A" và "B":** đọc thẳng từ đầu ra của Transformer decoder trong cùng lần chấm. Đây chính là bước sinh token đã học trong môn.
> **Balanced Position Calibration** của Wang và cộng sự: gộp kết quả hai thứ tự đã chấm sẵn, không cần huấn luyện.
> **Cohen's kappa và Krippendorff's alpha:** trừ đi phần đồng ý do ngẫu nhiên, nên cho biết rubric có đủ rõ không. Alpha dùng được khi bốn người mỗi người chỉ chấm một phần.
> Cuối cùng, **F1 và cosine embedding** là hai baseline so sánh văn bản, dùng lại biểu diễn của môn học.
>
> Nhóm không fine-tune judge và không dùng API trả phí làm judge chính.

## Màn 11 · Tóm tắt đề tài và đầu ra (25 giây)

*[Chỉ vào dòng "Đầu ra dự kiến".]*

> Đồ án sẽ cho ra bốn thứ: sáu tiêu chí đánh giá đo trên tiếng Việt, có so với tiếng Anh; phân tích flip xảy ra khi nào; khuyến nghị có nên chấm hai thứ tự, kèm xếp hạng Qwen, gpt-oss, Gemini trên tiếng Việt; và một demo trực tiếp.
>
> Qua đó, nhóm muốn góp phần trả lời câu hỏi: khi nào phán quyết của LLM judge đáng tin, nhất là với tiếng Việt. Về lâu dài, một judge đáng tin là nền để xây harness tự chọn mô hình free phù hợp cho từng câu hỏi, vừa trả lời tốt vừa tiết kiệm chi phí.

*[Chuyển sang màn 12 rồi mới cảm ơn.]*

## Màn 12 · Toàn cảnh quy trình (nền khi hỏi đáp, không tính giờ)

> Em xin cảm ơn thầy và các bạn. Đây là toàn cảnh quy trình của nhóm. Nhóm sẵn sàng nhận câu hỏi.

*[Để màn này trên màn hình suốt phần hỏi đáp. Khi được hỏi về cách làm, chỉ vào cột tương ứng: cột 2 cho câu trả lời của Qwen, gpt-oss, Gemini, cột 3 cho hai lượt chấm đổi thứ tự, cột 4 cho xác suất token, cột 5 cho cách xác định flip, cột 6 cho người chấm, cột 7 cho các tiêu chí đánh giá. Nếu hỏi các con số trong hình: đó là ví dụ giả định, chưa phải kết quả. Câu hỏi thật ưu tiên dạng "vì sao", "như thế nào". Nếu được hỏi chi tiết cách tính một tiêu chí, nhấn → sang màn 13.]*

## Màn 13 · Tiêu chí đánh giá (dự phòng cho hỏi đáp)

*[Chỉ mở khi được hỏi cách tính. Mỗi dòng: tên tiêu chí, câu hỏi nghiên cứu nó trả lời, công thức.]*

---

## Chuẩn bị trả lời câu hỏi

**Đầu ra cụ thể của đồ án là gì?**
Có bốn thứ: tỉ lệ flip đo được trên tiếng Việt, kèm so sánh với tiếng Anh; phân tích flip xảy ra khi nào và có liên quan đến độ tự tin của judge không; một khuyến nghị dùng judge đã được kiểm chứng trên dữ liệu thật; và một demo trực tiếp, trong đó judge đổi phán quyết khi hai câu trả lời đổi chỗ.

**Đề tài này khác gì Zheng et al.?**
Nhóm làm trên tiếng Việt, đối chiếu với người chấm, và phân tích flip theo độ chênh chất lượng và độ tự tin của judge. Đề tài không nhằm phát hiện ra position bias, vì hiện tượng này đã được ghi nhận ở tiếng Anh.

**Vì sao không dùng GPT-4 làm judge?**
Mô hình mã mở cho lấy trực tiếp xác suất token "A" và "B", điều mà câu hỏi 3 cần. Ngoài ra, chạy trên Colab thì không tốn phí API và người khác tái lập được thí nghiệm.

**Câu trả lời do mô hình nào sinh ra?**
Ba mô hình dùng miễn phí: Qwen2.5-7B-Instruct chạy trên Colab, gpt-oss-20b, mô hình mã mở của OpenAI, và Gemini Flash-Lite qua free tier của Google AI Studio, khoảng 500 request mỗi ngày nên chạy trong một đến hai ngày. Cả ba nhận cùng một prompt, yêu cầu trả lời 2–4 câu, không định dạng. gpt-oss-20b chạy với reasoning effort thấp và chỉ lấy phần trả lời cuối. Mỗi câu hỏi có ba câu trả lời, ghép thành ba cặp, tổng 1500 cặp.

**Qwen vừa trả lời vừa làm judge, có bị thiên vị không?**
Có thể. Judge có thể ưa câu trả lời của chính họ mình (self-enhancement bias). Nhưng điều này không tạo ra flip, vì cùng một cặp được chấm ở cả hai thứ tự; nó chỉ có thể làm lệch người thắng. Nhóm báo cáo riêng các cặp có Qwen để thấy ảnh hưởng này.

**Vì sao chọn ba mô hình free?**
Đây là lựa chọn thực tế của một nhóm ít kinh phí. Về sau, nhóm muốn xây một harness tự chọn mô hình free phù hợp cho từng câu hỏi để trả lời tốt mà vẫn tiết kiệm chi phí. Muốn vậy cần một judge so sánh các mô hình một cách công bằng, và đồ án này kiểm tra điều kiện đó.

**Đã có Qwen 3.x, sao vẫn dùng Qwen2.5-7B?**
Nhóm giữ có chủ ý. Đề tài cần các cặp có chất lượng chênh nhau, và một mô hình nhỏ, cũ hơn giúp tạo độ chênh đó. Mục tiêu là đo judge, không phải tìm mô hình trả lời tốt nhất.

**Ba mô hình mạnh yếu thế nào ở tiếng Việt?**
Chưa có bảng điểm tiếng Việt chung cho đúng ba bản này. Một đánh giá độc lập cho thấy gpt-oss yếu ở các tác vụ đa ngôn ngữ, nên nhiều khả năng nó là mô hình yếu nhất. Điều đó có ích cho đề tài vì tạo ra các cặp chênh rõ. Thứ hạng thật sẽ do điểm người chấm quyết định.

**Câu dài có được judge ưa hơn không?**
Có thể, đó là verbosity bias. Nhóm giới hạn câu trả lời 2–4 câu trong prompt và ghi lại độ dài từng câu, để kiểm tra flip có đi kèm chênh lệch độ dài hay không.

**Sao không dùng hết bộ dữ liệu, chỉ lấy 500 câu?**
Giới hạn nằm ở người chấm, không ở máy. 500 câu cho 1500 câu trả lời, mỗi câu cần hai người chấm, tức 3000 lượt chấm; chia cho bốn người, mỗi người khoảng 750 câu trả lời, tầm 12 giờ. Với 500 câu, sai số của tỉ lệ flip trong nhóm cặp gần ngang nhau vào khoảng ±5 điểm, nhỏ hơn khoảng 2,5 lần so với các bài 80 câu. Lên 1000 câu thì công chấm gấp đôi mà sai số chỉ giảm thêm khoảng 1,3 điểm, trong khi người chấm mệt sẽ làm điểm tham chiếu nhiễu hơn.

**Sao lấy câu từ tập train, không phải validation?**
Nhóm không huấn luyện mô hình nào nên tập train không bị "dùng" vào việc gì khác. Tập validation chỉ có 469 câu "vì sao", "như thế nào" nằm trên 318 đoạn văn, không đủ 500 câu nếu mỗi đoạn văn chỉ lấy một câu.

**Judge có thể đã thấy UIT-ViQuAD lúc huấn luyện không?**
Có thể. Đây là bộ dữ liệu công khai, và cả tập train lẫn validation đều có trên mạng. Tuy vậy, thứ được chấm là câu trả lời do mô hình sinh ra, không phải đáp án gốc, nên ảnh hưởng đến việc đo flip là hạn chế. Nhóm đã ghi điều này trong phần giới hạn.

**Balanced Position Calibration là gì?**
Đây là một cách giảm thiểu trong Wang et al. (2023): chấm cặp câu trả lời theo cả hai thứ tự, rồi lấy trung bình điểm của hai lần.

**Token bias là gì?**
Judge trả lời bằng một token, "A" hoặc "B". Ngoài phần xác suất đến từ nội dung, mô hình vốn đã ưa token "A" hơn. Câu đứng trước luôn mang nhãn "A", nên ưa "A" cũng là ưa câu đứng trước. Khi hai câu gần ngang nhau, thói quen này đủ để lật phán quyết. Lưu ý: Zheng et al. (2024) đo hiện tượng này trên câu hỏi trắc nghiệm. Với việc chấm theo cặp, đây mới là một nguyên nhân có thể, chưa được chứng minh.

**Flip được tính thế nào?**
Mỗi cặp được chấm hai lần, lần hai đổi chỗ hai câu trả lời. Nếu câu thắng ở hai lần khác nhau thì cặp đó là một flip. Tỉ lệ flip bằng số cặp flip chia cho tổng số cặp.

**Vì sao so với tiếng Anh?**
Để biết hiện tượng này có nặng hơn ở tiếng Việt không. Phần tiếng Anh là bản dịch máy của cùng 500 câu, nên khác biệt giữa hai ngôn ngữ có thể một phần do chất lượng bản dịch.
