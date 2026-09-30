# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-2A202602761`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`, SLO `fast_successful_requests` (latency <= 3000ms)
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng chờ lâu hơn 3 giây mới nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard panel Latency, xác nhận P95/P99/TTFT và thời điểm tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh span `retrieval` và `llm-generation`.
- Mitigation tạm thời: nếu `retrieval` chậm thì tắt practice scenario `rag_slow` hoặc khôi phục retrieval; nếu `llm-generation` chậm thì rollback label `production` của prompt.
- Owner: `student-2A202602761`

## Alert 2

- Tên: `HighErrorRateOrRetrievalFailure`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `request_failed / request_received` và `tool_success`, guardrail error rate <= 2%, retrieval success >= 90%
- Điều kiện và thời gian duy trì: `error_rate_pct > 2` hoặc `retrieval_success_rate_pct < 90` trong 5 phút
- Ảnh hưởng tới người dùng: yêu cầu trả về lỗi 500 hoặc thiếu ngữ cảnh
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors, xem error rate, breakdown `error_type` và retrieval success.
  2. Lọc `request_failed` trong `data/logs.jsonl`, lấy `correlation_id`, `error_type`, `tool_success`.
  3. Mở trace cùng `correlation_id`, kiểm tra span `retrieval` có lỗi hay không.
- Mitigation tạm thời: khôi phục dịch vụ retrieval, tắt practice scenario `tool_fail`, xác nhận error rate về dưới 2%.
- Owner: `student-2A202602761`

## Alert 3

- Tên: `CostSpike`
- Severity: `warning`
- Duration: `15m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `response_sent.cost_usd`, guardrail daily cost <= 2.5 USD
- Điều kiện và thời gian duy trì: `daily_cost_usd > 2.5` trong 15 phút
- Ảnh hưởng tới người dùng: không thấy trực tiếp, nhưng chi phí vượt ngân sách sẽ dẫn tới giới hạn dịch vụ
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Cost và Tokens, xem traffic có tăng cùng lúc không.
  2. Nếu cost tăng mà traffic không tăng, lọc `response_sent` có `tokens_out` cao.
  3. Mở trace tương ứng, xem token/cost của `llm-generation` và `prompt_version`.
- Mitigation tạm thời: rollback prompt về version cũ, giới hạn độ dài output, tắt practice scenario `cost_spike`.
- Owner: `student-2A202602761`

## Alert 2

- Tên:
- Severity:
- Duration:
- Kênh thông báo: Slack
- SLI/SLO liên quan:
- Điều kiện và thời gian duy trì:
- Ảnh hưởng tới người dùng:
- Ba bước kiểm tra đầu tiên:
- Mitigation tạm thời:
- Owner:

## Alert 3

- Tên:
- Severity:
- Duration:
- Kênh thông báo: Slack
- SLI/SLO liên quan:
- Điều kiện và thời gian duy trì:
- Ảnh hưởng tới người dùng:
- Ba bước kiểm tra đầu tiên:
- Mitigation tạm thời:
- Owner:
