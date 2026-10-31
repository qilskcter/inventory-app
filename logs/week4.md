# NHẬT KÝ CÔNG VIỆC (WORKLOG) - TUẦN 4

---

## I. THÔNG TIN CHUNG
* **Tên dự án:** Hệ thống quản lý kho hàng và cảnh báo tồn kho (`inventory-app`)
* **Phân nhóm môn học:** Domain Apps - Đợt 1, 2026–2027
* **Giảng viên hướng dẫn:** ThS. Huỳnh Xuân Phụng
* **Thành viên nhóm:**
  1. **Nguyễn Đình Khanh** - MSSV: `24110244` (Nhóm trưởng / Backend, Tích hợp & Kiểm thử tổng thể)
  2. **Võ Minh Quân** - MSSV: `24110312` (Database, Tối ưu chi phí, Hạ tầng & Dọn dẹp tài nguyên)
* **AWS Region:** `us-east-1` (N. Virginia)
* **Môi trường hiện có:** Elastic Beanstalk `inventory-env-py312`, Amazon RDS PostgreSQL `inventory-db`, Amazon S3 Private Bucket `inventory-reports-us-east-1-24110244`, Amazon SNS Topic `inventory-low-stock-alert`

> **Lưu ý nguyên tắc an toàn:** Nhật ký này xác lập kế hoạch phân công công việc chi tiết cho Tuần 4. Chỉ đánh dấu hoàn thành (`[x]`) và ghi nhận kết quả sau khi đã trực tiếp thực thi trên hệ thống, nghiệm thu thành công và lưu đầy đủ ảnh minh chứng xác thực. Tuyệt đối không hardcode mật khẩu, access key, token hay thông tin xác thực vào repository, tài liệu hoặc ảnh chụp màn hình.

---

## II. MỤC TIÊU TUẦN 4: KIỂM THỬ TỔNG THỂ, TỐI ƯU CHI PHÍ, DỌN DẸP TÀI NGUYÊN, VIẾT BÁO CÁO VÀ DEMO

Tuần 4 là giai đoạn hoàn thiện và nghiệm thu tổng thể dự án Điện toán đám mây. Nhóm tập trung vào 5 mục tiêu cốt lõi:

1. **Kiểm thử tổng thể toàn diện (End-to-End System & Load Testing):** Thực thi chuỗi kiểm thử liên hoàn từ giao diện Web UI, RESTful API, xuất báo cáo tồn kho CSV lên Amazon S3 Private, phát cảnh báo biến động kho qua Amazon SNS; thực hiện kiểm thử tải nhẹ (10–20 concurrent requests) để đo lường độ trễ (latency), thông lượng (throughput) và xác nhận tỷ lệ lỗi HTTP 5xx duy trì ở mức 0%.
2. **Tối ưu hóa hiệu năng và chi phí (Performance & Cost Optimization):** Triển khai Connection Pooling (`ThreadedConnectionPool`) tại tầng ứng dụng Flask để tái sử dụng socket TCP tới RDS, giảm tải tài nguyên CPU/RAM cho instance `db.t3.micro`; rà soát toàn diện bảng điều khiển AWS Billing & Cost Management nhằm bảo đảm chi phí tích lũy nằm an toàn trong hạn mức cấp phép của AWS Learner Lab.
3. **Quy trình dọn dẹp và giải phóng tài nguyên an toàn (Safe Resource Teardown Policy):** Thiết lập quy trình dọn dẹp có biên bản phê duyệt (Sign-off Protocol) đối với các tài nguyên thử nghiệm, dữ liệu test (`REG-TEST-*`), các file báo cáo tạm, và snapshot không cần thiết; xây dựng hướng dẫn dừng/hủy tài nguyên an toàn sau buổi nghiệm thu nhằm tránh phát sinh chi phí ngoài ý muốn.
4. **Xây dựng kịch bản và chuẩn bị Demo sản phẩm (Live Demo Preparation):** Biên soạn kịch bản trình diễn (Demo Script) mạch lạc, phân vai rõ ràng giữa 2 sinh viên; chuẩn bị sẵn các dữ liệu mẫu trực quan minh họa trọn vẹn các tính năng nổi bật: CRUD sản phẩm, cảnh báo kho chạm ngưỡng theo thời gian thực tới email, xuất CSV an toàn và cơ chế chịu lỗi database tạm thời (HTTP 503 / `Retry-After: 5`).
5. **Hoàn thiện tài liệu tổng kết và báo cáo kỹ thuật (Final Documentation & Technical Report):** Tổng hợp toàn bộ mã nguồn, sơ đồ kiến trúc đám mây hoàn chỉnh, bảng ma trận kiểm thử tổng thể, đối soát Git commit history, hoàn thiện báo cáo Tuần 4 và báo cáo nghiệm thu tổng thể môn học đạt chuẩn kỹ thuật.

---

## III. BẢNG PHÂN CÔNG VÀ THỜI GIAN DỰ KIẾN (TỪ THỨ TƯ ĐẾN CHỦ NHẬT)

### 1. Nguyễn Đình Khanh (MSSV: 24110244)
* **Vai trò:** Backend, tích hợp ứng dụng, kiểm thử tổng thể và kịch bản Demo

| Ngày | Thời gian | Nội dung công việc dự kiến | Công cụ | Số giờ | Kết quả / minh chứng dự kiến |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **Thứ Tư** | 20:00–23:00 | • Triển khai Connection Pooling (`psycopg2.pool.ThreadedConnectionPool` kích thước 2–5 kết nối) trong `init_db.py` và `app.py`.<br>• Kiểm thử tính ổn định của pool kết nối khi xử lý chuỗi request liên tục, kiểm tra việc giải phóng connection trong `finally`.<br>• Cập nhật và kiểm tra 33 unit tests hiện hữu đảm bảo tương thích 100% với cơ chế Connection Pool mới. | Python, Flask, `psycopg2.pool`, pytest/unittest | 3.0h | Mã nguồn Connection Pooling hoàn thiện; log khởi tạo và giải phóng connection; 100% unit tests vượt qua. |
| **Thứ Năm** | 13:00–16:00 | • Xây dựng kịch bản kiểm thử tải nhẹ (Load Testing) bằng công cụ `locust` hoặc `k6` (mô phỏng 10–20 người dùng đồng thời).<br>• Thực thi kiểm thử tải đối với các endpoint đọc (`GET /api/products`), xuất báo cáo (`GET /api/reports/inventory/csv`) và giao dịch kho (`POST /api/transactions`).<br>• Đo lường thời gian đáp ứng (Response Time), thông lượng (RPS) và tỷ lệ lỗi; ghi nhận biểu đồ hiệu năng. | Locust/k6, cURL, Gunicorn, CloudWatch | 3.0h | Báo cáo kiểm thử tải với các chỉ số RPS, latency p95/p99; log xác nhận không xuất hiện lỗi HTTP 500 do nghẽn connection. |
| **Thứ Sáu** | 13:30–16:30 | • Soạn thảo kịch bản Live Demo chi tiết từng bước (Step-by-step Demo Flow) từ Web UI đến Backend API và dịch vụ AWS.<br>• Chuẩn bị dữ liệu demo trực quan (SKU, hình ảnh, email subscriber SNS thực tế).<br>• Thực hiện kiểm thử toàn trình (E2E Test) đối chiếu phản hồi email SNS và file CSV tải lên S3 Private theo đúng kịch bản demo. | Browser, Postman/cURL, S3 Console, Gmail | 3.0h | Tài liệu kịch bản Demo (`demo_script.md`); biên bản kiểm thử E2E xác nhận các bước demo hoạt động trơn tru. |
| **Thứ Bảy** | 09:00–11:30 | • Phối hợp cùng Quân thực hiện buổi diễn tập Demo (Dry-run Demo), bấm giờ và chuẩn hóa thao tác thuyết trình.<br>• Kiểm thử các tình huống ngoại lệ trong demo: cố tình nhập xuất âm, trùng SKU, và ngắt kết nối RDS mô phỏng lỗi 503.<br>• Ghi hình video demo dự phòng (Backup Video Demo) chất lượng cao 1080p phòng ngừa sự cố mạng phòng lab. | OBS/QuickTime, Web UI, Beanstalk, RDS | 2.5h | Video demo dự phòng hoàn chỉnh; danh mục phân vai và mốc thời gian trình bày chuẩn bị cho buổi báo cáo. |
| **Chủ Nhật** | 14:00–16:30 | • Rà soát chất lượng mã nguồn lần cuối, dọn dẹp các tệp tạm, cập nhật `README.md` và `requirements.txt`.<br>• Tổng hợp toàn bộ số liệu kiểm thử tải, minh chứng demo vào Báo cáo kỹ thuật Tuần 4 (`documents/week_4/week4.md`).<br>• Xuất file báo cáo Word (`week4.docx`) và bàn giao sản phẩm hoàn thiện. | Git, Markdown, python-docx, Pandoc | 2.5h | Báo cáo Tuần 4 hoàn thiện kèm bản Word; kho mã nguồn sạch, tài liệu hướng dẫn vận hành đầy đủ. |

* **Tổng số giờ dự kiến của Nguyễn Đình Khanh:** **14.0 giờ**.

---

### 2. Võ Minh Quân (MSSV: 24110312)
* **Vai trò:** Database, hạ tầng, tối ưu chi phí, giám sát CloudWatch và dọn dẹp tài nguyên

| Ngày | Thời gian | Nội dung công việc dự kiến | Công cụ | Số giờ | Kết quả / minh chứng dự kiến |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **Thứ Tư** | 20:00–23:00 | • Rà soát thông số cấu hình cơ sở dữ liệu RDS PostgreSQL (`inventory-db`) và tài nguyên EC2 Beanstalk.<br>• Phối hợp đồng bộ thông số cấu hình giữa 2 môi trường; bảo đảm kết nối an toàn trong mạng nội bộ VPC.<br>• Thiết lập CloudWatch Metric Alarms tự động theo dõi: CPU RDS > 80% và tỷ lệ lỗi HTTP 5xx > 1% liên kết tới SNS Topic. | AWS Console, RDS, CloudWatch Alarms, SNS | 3.0h | Cấu hình CloudWatch Alarms hoàn tất; ảnh chụp trạng thái Alarm `OK` và cấu hình Notification Action. |
| **Thứ Năm** | 14:00–17:00 | • Rà soát tổng thể chi phí trên AWS Billing & Cost Management và hạn mức tín dụng Learner Lab.<br>• Kiểm tra các tài nguyên phụ trợ đang chạy (EBS Volumes, Elastic IPs, S3 Buckets, RDS Snapshots) nhằm phát hiện lãng phí.<br>• Tối ưu hóa dung lượng lưu trữ: áp dụng vòng đời (Lifecycle Rule) cho S3 Bucket tự động dọn báo cáo sau 7 ngày; tinh chỉnh retention cho CloudWatch Log Groups. | AWS Billing, S3 Lifecycle, CloudWatch Logs | 3.0h | Bảng thống kê chi phí chi tiết từng dịch vụ; cấu hình S3 Lifecycle và Log Retention 7 ngày tiết kiệm dung lượng. |
| **Thứ Sáu** | 08:30–11:30 | • Xây dựng quy trình dọn dẹp tài nguyên an toàn (Resource Teardown Plan) sau khi kết thúc nghiệm thu môn học.<br>• Tạo Manual Snapshot cuối cùng cho RDS PostgreSQL (`inventory-db-final-snapshot`) để lưu trữ dữ liệu an toàn.<br>• Soạn thảo tài liệu hướng dẫn hủy tài nguyên từng bước (Step-by-step Teardown Guide) theo đúng thứ tự phụ thuộc. | AWS Console, RDS Snapshots, Markdown | 3.0h | Snapshot cơ sở dữ liệu hoàn tất; tài liệu quy trình dọn dẹp tài nguyên (`teardown_guide.md`) có phê duyệt. |
| **Thứ Bảy** | 14:00–16:30 | • Tham gia buổi diễn tập Demo cùng Khanh: phụ trách phần trình diễn giám sát CloudWatch, cấu hình S3, SNS và Security Groups.<br>• Giám sát trực tiếp biểu đồ CloudWatch Metrics (CPU, DatabaseConnections, NetworkIn/Out) trong lúc Khanh chạy kiểm thử tải.<br>• Kiểm tra việc dọn dẹp các SKU thử nghiệm phát sinh trong buổi diễn tập theo đúng chính sách an toàn dữ liệu. | CloudWatch Dashboard, AWS Console, Session Manager | 2.5h | Biểu đồ CloudWatch Metrics ghi nhận trong phiên test tải; biên bản xác nhận dọn dẹp dữ liệu thử nghiệm. |
| **Chủ Nhật** | 09:00–11:30 | • Tổng hợp số liệu giám sát, tối ưu chi phí và báo cáo phân tích hạ tầng vào Báo cáo Tuần 4.<br>• Rà soát toàn bộ ảnh minh chứng hạ tầng (che mờ thông tin nhạy cảm, số tài khoản AWS, token).<br>• Đối chiếu hạn mức chi phí cuối kỳ và hoàn thiện phần đóng góp cá nhân trong báo cáo tổng kết. | AWS Billing, CloudWatch, Markdown | 2.5h | Phần báo cáo hạ tầng & chi phí hoàn chỉnh; bảng số dư chi phí cuối kỳ; sẵn sàng cho buổi bảo vệ đồ án. |

* **Tổng số giờ dự kiến của Võ Minh Quân:** **14.0 giờ**.

---

## IV. DANH SÁCH CÔNG VIỆC CẦN LÀM (CHECKLIST THEO GIAI ĐOẠN)

### Giai đoạn 1: Tối ưu hiệu năng & Kiểm thử tổng thể
- [x] Triển khai Connection Pooling (`ThreadedConnectionPool`) tại `init_db.py`, giới hạn 2–5 kết nối.
- [x] Kiểm thử tự động hồi quy: xác nhận 100% unit tests (33/33 tests) chạy thành công với Connection Pool.
- [x] Thực hiện kịch bản kiểm thử tải nhẹ (10–20 concurrent users) đo lường độ trễ và thông lượng.
- [x] Xác nhận không có hiện tượng cạn kiệt kết nối (Connection Exhaustion) hoặc lỗi HTTP 500 trên CloudWatch Logs.

### Giai đoạn 2: Giám sát chủ động & Tối ưu chi phí
- [ ] Cấu hình CloudWatch Metric Alarm theo dõi CPU RDS > 80% gắn action gửi thông báo qua SNS.
- [ ] Cấu hình CloudWatch Metric Alarm theo dõi HTTP 5xx Errors > 1% trên Elastic Beanstalk.
- [ ] Thiết lập S3 Lifecycle Rule tự động xóa hoặc chuyển lưu trữ báo cáo cũ sau 7 ngày.
- [ ] Cấu hình Retention Period cho toàn bộ CloudWatch Log Groups ở mức 7 ngày để giảm chi phí lưu trữ log.
- [ ] Rà soát AWS Cost Explorer và số dư tín dụng AWS Learner Lab, lập bảng phân bổ chi phí chi tiết.

### Giai đoạn 3: Chuẩn bị kịch bản và diễn tập Demo
- [x] Soạn thảo kịch bản Demo ([`documents/week_4/demo_script.md`](../documents/week_4/demo_script.md)) chi tiết các bước thực hiện và phân vai thuyết minh.
- [x] Chuẩn bị bộ dữ liệu demo chuẩn hóa (`W4-DEMO-01`, `W4-DEMO-02`, `W4-DEMO-03`, email nhận cảnh báo `24110244@student.hcmute.edu.vn` trạng thái `Confirmed`).
- [x] Thực hiện kiểm thử toàn trình E2E ([`tests/verify_e2e_demo.py`](../tests/verify_e2e_demo.py)) đối chiếu phản hồi email SNS và file CSV tải lên S3 Private theo đúng kịch bản demo (6/6 ca E2E ĐẠT).
- [ ] Thực hiện ít nhất 01 buổi diễn tập Live Demo (Dry-run), đo lường thời gian trình bày dưới 10–15 phút.
- [ ] Ghi hình video demo dự phòng (1080p có lồng tiếng/thuyết minh) tải lên thư mục lưu trữ dự phòng.

### Giai đoạn 4: Hoàn thiện báo cáo kỹ thuật & Minh chứng
- [ ] Cập nhật toàn diện tài liệu kỹ thuật Tuần 4 (`documents/week_4/week4.md`) theo chuẩn cấu trúc nhóm.
- [ ] Trích xuất bảng commit Git chính thức, phân tích diff và chứng minh 100% không hardcode bí mật.
- [ ] Chụp và chuẩn hóa toàn bộ ảnh minh chứng kiểm thử tải, CloudWatch Alarms, S3 Lifecycle và chi phí.
- [ ] Chuyển đổi báo cáo sang định dạng Word (`week4.docx`) phục vụ in ấn/nộp bài.

### Giai đoạn 5: Quy trình dọn dẹp tài nguyên an toàn (Post-Demo Teardown)
- [ ] Tạo bản Final Snapshot lưu trữ cho cơ sở dữ liệu RDS PostgreSQL trước khi có bất kỳ thao tác dọn dẹp nào.
- [ ] Soạn thảo và đối chiếu biên bản dọn dẹp tài nguyên có chữ ký xác nhận (Sign-off) của 2 thành viên.
- [ ] Hướng dẫn thứ tự terminate tài nguyên an toàn: Elastic Beanstalk Environment $\rightarrow$ RDS DB $\rightarrow$ S3 Objects $\rightarrow$ CloudWatch Alarms $\rightarrow$ SNS Topics.

---

## V. QUY ƯỚC MINH CHỨNG (DỰ KIẾN TUẦN 4)

Toàn bộ ảnh chụp màn hình minh chứng Tuần 4 dự kiến lưu tại thư mục `documents/week_4/screenshots/`. Chỉ đưa ảnh vào báo cáo sau khi đã thực hiện thành công và kiểm tra che mờ các thông tin nhạy cảm:

| Tên file minh chứng | Nội dung ghi nhận thực tế dự kiến |
| :--- | :--- |
| `65_week4_connection_pool_init.png` | Log khởi tạo và vận hành của `ThreadedConnectionPool` trên ứng dụng Flask/Gunicorn. |
| `66_week4_load_test_execution.png` | Quá trình thực thi kiểm thử tải (Locust/k6) với 10–20 concurrent users mô phỏng truy cập kho. |
| `67_week4_load_test_metrics.png` | Biểu đồ kết quả kiểm thử tải: Response Time, Requests Per Second (RPS) và 0% Failure Rate. |
| `68_week4_cloudwatch_alarms_config.png` | Cấu hình 02 CloudWatch Metric Alarms (RDS CPU > 80% và Beanstalk 5xx Errors > 1%). |
| `69_week4_cloudwatch_alarm_state_ok.png` | Trạng thái hoạt động bình thường (`OK`) của các CloudWatch Metric Alarms trên Dashboard. |
| `70_week4_s3_lifecycle_rule.png` | Cấu hình quy tắc vòng đời (Lifecycle Rule) tự động dọn dẹp object sau 7 ngày trên S3 Bucket. |
| `71_week4_cloudwatch_log_retention.png` | Cấu hình thời hạn lưu trữ (Retention: 7 days) cho các CloudWatch Log Groups của Beanstalk. |
| `72_week4_aws_billing_cost_summary.png` | Bảng đối soát chi phí chi tiết các dịch vụ trên AWS Billing & Cost Management trong hạn mức Lab. |
| `73_week4_rds_final_snapshot.png` | Bản Snapshot cuối cùng của Amazon RDS PostgreSQL (`inventory-db-final-snapshot`) trạng thái `Available`. |
| `74_week4_e2e_demo_flow.png` | Luồng thực hiện Live Demo hoàn chỉnh: Thao tác xuất kho $\rightarrow$ Kích hoạt cảnh báo SNS $\rightarrow$ Email thông báo thực tế. |
| `75_week4_safe_cleanup_signoff.png` | Biên bản nghiệm thu và danh mục tài nguyên đã được dọn dẹp an toàn có chữ ký xác nhận của nhóm. |

---

## VI. NGUYÊN TẮC AN TOÀN, BẢO VỆ DỮ LIỆU VÀ QUẢN LÝ NGÂN SÁCH LAB

* **Bảo vệ toàn vẹn dữ liệu sản xuất:** Mọi thao tác kiểm thử tải và demo chỉ được phép sử dụng tiền tố SKU thử nghiệm chuyên biệt (`W4-DEMO-*`, `LOAD-TEST-*`). Tuyệt đối không can thiệp vào các bản ghi gốc ban đầu của hệ thống.
* **Nguyên tắc Snapshot trước khi dọn dẹp:** Không được phép xóa hoặc terminate bất kỳ cơ sở dữ liệu RDS nào nếu chưa tạo và kiểm tra thành công bản Manual Snapshot độc lập.
* **Kiểm soát chi phí nghiêm ngặt:** Theo dõi chặt chẽ hạn mức chi phí trên AWS Billing; tuyệt đối không tạo tài nguyên ngoài danh mục cho phép (như NAT Gateway, Multi-AZ RDS, hoặc Application Load Balancer có phí) nếu chưa có phê duyệt từ giảng viên hướng dẫn.
* **Loại bỏ nguy cơ rò rỉ thông tin (Zero Secret Leak):** Tiếp tục duy trì chính sách 100% không hardcode mật khẩu hay AWS API keys vào mã nguồn, commit history, file cấu hình, hay ảnh chụp màn hình minh chứng.
* **Quy trình dọn dẹp tài nguyên có phê duyệt:** Việc tắt/xóa tài nguyên sau khi hoàn tất demo phải tuân thủ nghiêm ngặt danh sách kiểm kê và có sự đồng thuận của cả 2 thành viên trong nhóm.

---

## VII. TIÊU CHÍ NGHIỆM THU VÀ BÀN GIAO DỰ ÁN (ACCEPTANCE CRITERIA)

Dự án được đánh giá là hoàn thành xuất sắc khi đáp ứng trọn vẹn 100% các tiêu chí nghiệm thu sau:

1. **Hiệu năng & Ổn định:** Hệ thống duy trì thời gian phản hồi API trung bình $< 200\text{ms}$; xử lý mượt mà tối thiểu 10–20 người dùng đồng thời; tỷ lệ lỗi HTTP 5xx đạt chính xác 0.0%.
2. **Tính toàn vẹn nghiệp vụ:** Toàn bộ chức năng quản lý kho hàng (CRUD sản phẩm, nhập/xuất kho nguyên tử, xuất báo cáo CSV an toàn phòng chống injection, lưu trữ S3 Private mã hóa AES-256, cảnh báo tự động qua SNS chống gửi lặp) hoạt động đồng bộ và chính xác.
3. **Giám sát & Tự động hóa:** Hoàn thiện cảnh báo CloudWatch Alarms chủ động; cấu hình vòng đời S3 và retention log tự động tối ưu chi phí; template CloudFormation được validate cú pháp hợp lệ.
4. **Chi phí tài khoản:** Tổng chi phí tiêu thụ nằm an toàn trong hạn mức được cấp của AWS Learner Lab, có bảng số liệu đối soát minh bạch từ AWS Billing.
5. **Chất lượng bàn giao:** Mã nguồn được chuẩn hóa trên GitHub (sạch sẽ, không hardcode credentials); có video demo dự phòng; báo cáo kỹ thuật Tuần 4 và báo cáo tổng kết hoàn chỉnh cả bản Markdown và bản Word (`.docx`).
