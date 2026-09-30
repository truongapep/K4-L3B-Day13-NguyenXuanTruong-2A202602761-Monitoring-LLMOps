# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Xuân Trường
- **MSSV:** 2A202602761
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/VinUni-AI20k/K4-L3B-Day13-Monitoring-LLMOps.git
- **Commit SHA cuối:** a8b6fd82c352eb64d0b5b1de993bd95a07979d2e
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-agent-request-02761`

## 2. Evidence index

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png, evidence/13-incident-log1.png`  |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Baseline lỗi do correlation ID = `MISSING` và thiếu enrichment; sau CP1 đạt đủ 4 tiêu chí |
| `validate_dashboard.py` | 6/6 panels | 6/6 panels | Contract đã hợp lệ từ đầu; dashboard runtime dựng thêm bằng Streamlit |
| `pytest` | 22 passed, 0 failed | 24 passed, 0 failed | Thêm 2 test mới của starter/BTC; không sửa file test nào của BTC |
| Số traces hợp lệ | 10 (baseline chưa có child span) | <ĐIỀN số trace trong project cá nhân, tối thiểu 10> | Mỗi trace có `lab-agent-run` với hai con `retrieval`, `llm-generation` |
| Số PII leak | 0 | 0 | Validator + request thử có email/SĐT/CCCD/thẻ đều bị che |
| Latency P95 / TTFT P95 | P95 1170 ms / TTFT P95 50 ms | Lúc bình thường: <ĐIỀN từ dashboard sau fix>. Lúc incident: P95 3574 ms / TTFT P95 50 ms | Incident làm P95 vượt SLO 3000 ms; TTFT không đổi |
| Retrieval success rate | 100% | 100% (kể cả lúc incident) | Incident `rag_slow` chỉ làm chậm, không gây lỗi |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** `CorrelationIdMiddleware` gọi `clear_contextvars()` đầu mỗi request, đọc header `x-request-id` (nếu không có thì sinh `req-<8-hex>` từ `uuid4`), `bind_contextvars(correlation_id=...)` để mọi log dùng chung, lưu vào `request.state`, và trả lại qua response header `x-request-id` cùng `x-response-time-ms`. Đã kiểm tra bằng request có header `req-abcd1234`, response trả đúng ID đó.
- **Các metadata được ghi vào structured log:** `ts`, `level`, `service`, `event`, `correlation_id`, `user_id_hash` (SHA-256 rút gọn, không ghi `user_id` thô), `session_id`, `feature`, `model`, `env`; riêng `response_sent` có thêm `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` được đăng ký trong danh sách processor của structlog **trước** `JsonlFileProcessor` (bước ghi file) và trước `JSONRenderer`, nên dữ liệu đã được che trước khi serialize. Hàm scrub đệ quy vào dict/list lồng nhau trong `payload`. `app/pii.py` có rule cho email, điện thoại VN, CCCD, thẻ thanh toán <và passport nếu bạn đã thêm>. Preview trong log và trace đều qua `summarize_text`/`scrub_text`.
- **Cách kiểm chứng kết quả:** `validate_logs.py` đạt 100/100 với 0 PII leak (`evidence/02-log-validator.png`); gửi request thật chứa email, SĐT, CCCD, thẻ và xác nhận log chỉ còn `[REDACTED_*]` (`evidence/05-pii-redaction.png`); pytest 24 passed.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Key Langfuse của project cá nhân nằm trong `.env` (không commit). Trace xuất hiện trong project này sau khi tôi tự chạy `load_test.py` và các request `/chat`; mỗi trace có metadata `correlation_id` trùng với log của request tôi vừa gửi. Xem `evidence/06-trace-list.png`.
- **Cấu trúc root/retrieval/generation observations:** `day13-agent-request` → `lab-agent-run` (agent) → `retrieval` (retriever, `_traced_retrieve`) + `llm-generation` (generation, `_traced_generate`, có model, `usage_details` input/output, `cost_details`). Input/output được scrub và cắt ngắn, root không capture raw input/output. Xem `evidence/07-trace-waterfall.png`.
- **Cách nối trace với log:** `correlation_id` được đưa vào trace metadata qua `propagate_attributes` và metadata của generation; tìm trace bằng đúng `correlation_id` lấy từ `data/logs.jsonl`. Xem `evidence/08-trace-metadata.png`.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** <ĐIỀN: version 1, labels `baseline` + `production`>
- **Version/label candidate:** <ĐIỀN: version 2, label `candidate`>
- **Trace ID của mỗi version:** baseline: `<ĐIỀN trace ID>` (`prompt_version=<ĐIỀN>`, `prompt_source=langfuse`); candidate: `<ĐIỀN trace ID>` (`prompt_version=<ĐIỀN>`). Cùng message đầu vào cho cả hai. Generation hiển thị link tới prompt `day13-chat`.
- **Cách promote và rollback `production`:** <ĐIỀN đúng thao tác bạn đã làm: chuyển label `production` từ v1 sang v2 trên Langfuse UI, chạy request được trace `prompt_version=2`, rồi chuyển `production` về v1 và chạy request được trace `prompt_version=1`. Không sửa code khi đổi version> (`evidence/09-prompt-versions.png`, `evidence/10-prompt-rollback.png`). Prompt được cache 60 giây nên restart API sau khi đổi label để thấy hiệu lực ngay.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dashboard Streamlit (`dashboard/app.py`) đọc `data/logs.jsonl`, đọc threshold từ `config/dashboard.yaml`, time range mặc định 60 phút, refresh 30 giây. Sáu panel: (1) Latency P50/P95/P99 + TTFT P95 (ms, SLO P95 ≤ 3000), (2) Traffic (request/phút, ≥ 1), (3) Errors + retrieval success (%, error ≤ 2%, retrieval ≥ 90%), (4) Cost (USD, ≤ 2.5), (5) Tokens in/out (≤ 50000), (6) Quality proxy (0–1, ≥ 0.75). Xem `evidence/11-dashboard-overview.png`. Threshold cost/tokens là tổng cả cửa sổ nên hiển thị ở dòng chú thích, không vẽ thành đường theo phút.
- **SLO và lý do chọn:** `fast_successful_requests`: 99.5% request thành công và `latency_ms <= 3000` trong 28 ngày. Baseline của tôi có P95 khoảng 1170 ms, P99 khoảng 2963 ms, nên ngưỡng 3000 ms đủ chặt để phát hiện suy giảm nhưng không báo động giả với request bình thường.
- **Cách tính error budget:** SLO 99.5% nghĩa là error budget 0.5%. Với 10,000 request trong 28 ngày, tối đa 50 request được phép lỗi hoặc chậm hơn 3000 ms. Trong lần incident, 5/5 request của challenge có `latency_ms` > 2000 ms và 1/5 vượt 3000 ms, nên nếu sự cố kéo dài sẽ tiêu hết budget nhanh.
- **Ba alert và runbook tương ứng** (`config/alert_rules.yaml`, `docs/alerts.md`): `HighLatencyP95` (warning, P95 > 3000 ms trong 5m, runbook alert-1); `HighErrorRateOrRetrievalFailure` (critical, error rate > 2% hoặc retrieval success < 90% trong 5m, runbook alert-2); `CostSpike` (warning, cost > 2.5 USD/ngày trong 15m, runbook alert-3). Cả ba gửi Slack `#k4-l3b-alerts`, owner `student-2A202602761`, dựa trên triệu chứng.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1` (incident do file challenge chỉ định: `rag_slow`, `affected_feature=monitoring`, ngưỡng 2000 ms)
- **Khoảng thời gian điều tra:** 2026-09-30 từ 09:54:10Z đến 09:54:21Z (5 request challenge, UTC)
- **Triệu chứng từ metrics:** Latency tăng bất thường: P50 2653 ms, P95 3574 ms, P99 3758 ms (vượt ngưỡng challenge 2000 ms và SLO 3000 ms), trong khi baseline P95 khoảng 1170 ms. TTFT P95 giữ 50 ms, error rate 0%, retrieval success 100%, token/cost không đổi bất thường. Xem `evidence/12-incident-metric.png`.
- **Log line và correlation ID liên quan:** `response_sent`, `correlation_id=req-54e736da`, `feature=monitoring`, `latency_ms=2653`, `ttft_ms=50`, `tokens_out=142`, `cost_usd=0.00219`. Bốn trong năm request có `latency_ms` khoảng 2653 ms, request đầu 3804 ms (`req-7875cd44`). Xem `evidence/13-incident-log.png`.
- **Trace ID và span gây ảnh hưởng:** Trace `<ĐIỀN trace ID>` (cùng `correlation_id=req-54e736da`): span `retrieval` = `<ĐIỀN ms>`, span `llm-generation` = `<ĐIỀN ms>`. Đối chứng sau fix (`req-05b06c74`): `retrieval` = `<ĐIỀN ms>`. Xem `evidence/14-incident-trace.png`.
- **Root cause:** <VIẾT SAU KHI trace xác nhận. Nếu `retrieval` chiếm phần lớn thời gian (khoảng 2,5 s) còn `llm-generation` không đổi, thì: bước retrieval bị chậm (khoảng 2,5 s do incident `rag_slow`), không phải LLM, token hay prompt.> Ghi chú: thời gian client đo (6.8–14.8 s) lớn hơn `latency_ms` phía server (khoảng 2.65 s) vì các request bị xử lý lần lượt, cách nhau khoảng 2.66 s trong log, nên request sau phải xếp hàng.
- **Fix action:** Tắt incident bằng `python scripts/inject_incident.py --disable`, chạy lại workload challenge. Client đo 320–790 ms; `latency_ms` phía server sau fix: <ĐIỀN từ bảng log sau fix>.
- **Preventive measure:** Dùng alert `HighLatencyP95` (P95 > 3000 ms trong 5m) với runbook mở trace so sánh span; bổ sung alert và timeout riêng cho span `retrieval` (có fallback trả lời khi retrieval chậm); kiểm tra xử lý song song của endpoint vì các request đang bị xếp hàng làm latency phía người dùng tăng gấp nhiều lần.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Tạo child observation bằng decorator `@observe` (retrieval và generation) thay vì `start_as_current_observation` trên client, để test BTC (dùng client giả) vẫn qua mà không sửa file test, đồng thời giữ `propagate_attributes(prompt=...)` để generation liên kết prompt version.
- **Một lỗi/blocker đã gặp:** Sau khi thêm span, test `test_agent_prompt_trace.py` fail vì client giả không có `start_as_current_observation`; sau đó `ImportError` do `app/tracing.py` chưa có hai hàm `update_current_*_safe`. Ngoài ra `.venv` mới thiếu `streamlit`/`pandas` sau khi đổi tên thư mục.
- **Cách tìm nguyên nhân và xử lý:** Đọc traceback và test để biết contract, không sửa file test của BTC; sửa trong `app/`, kiểm tra chữ ký SDK bằng `inspect.signature`; cài lại thư viện bằng `python -m pip install` vào đúng `.venv`.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics cho biết triệu chứng và thời điểm (P95 vượt SLO). Logs chọn ra request cụ thể qua `correlation_id` và loại trừ nhóm nguyên nhân (TTFT, token, cost không đổi). Traces cho biết span nào chiếm thời gian. Kết luận chỉ hợp lệ khi cả ba lớp cùng chỉ về một nguyên nhân.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt version cho biết request dùng prompt nào để tách regression do prompt khỏi lỗi hạ tầng; token/cost giúp phát hiện prompt dài hoặc output tăng; SLO/error budget định lượng mức chấp nhận được; rollback label `production` là cách khôi phục nhanh không cần deploy code.
- **Điều quan trọng nhất đã học:** Không kết luận root cause từ một lớp dữ liệu; và số đo phía client, phía server, phía span có thể khác nhau nên phải nêu rõ nguồn của từng số.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** <ĐIỀN: ví dụ tên repo và tên project Langfuse chưa đúng mẫu đề; dashboard chỉ dựa trên log local; threshold cost/tokens không vẽ theo phút>

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.