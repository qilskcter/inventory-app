# BÁO CÁO KỸ THUẬT VÀ KẾT QUẢ TRIỂN KHAI - TUẦN 3
## RÀ SOÁT TÍCH HỢP FLASK - RDS, XUẤT BÁO CÁO S3 PRIVATE VÀ THIẾT KẾ CẢNH BÁO AMAZON SNS

**Dự án:** Hệ thống quản lý kho hàng và cảnh báo tồn kho (`inventory-app`)  
**Môn học:** Điện toán đám mây (Cloud Computing)  
**Sinh viên thực hiện:**
- Nguyễn Đình Khanh (MSSV: `24110244`) - Nhóm trưởng / Backend & Cloud Deployment
- Võ Minh Quân (MSSV: `24110312`) - Thành viên / Database & Infrastructure Setup  
**Giảng viên hướng dẫn:** ThS. Huỳnh Xuân Phụng  
**AWS Region:** `us-east-1` (N. Virginia)

---

> **Phạm vi báo cáo:** Báo cáo ghi nhận kết quả rà soát chi tiết luồng kết nối Flask → Amazon RDS PostgreSQL trên Elastic Beanstalk Environment đang hoạt động (`inventory-env-py312`), kiểm thử toàn diện các endpoint RESTful API sản phẩm và giao dịch kho, kiểm tra cơ chế xử lý lỗi dữ liệu và phản hồi lỗi database tạm thời (HTTP 503 / Retry-After) với ảnh minh chứng thực tế (Hình 1–3). Tài liệu ghi nhận thiết kế và triển khai module xuất báo cáo tồn kho định dạng CSV an toàn (phòng chống CSV Formula Injection, hỗ trợ dữ liệu rỗng) và tích hợp lưu trữ tự động vào Amazon S3 Private Bucket tuân thủ nguyên tắc Least Privilege (không hardcode credential, dùng IAM Role `LabInstanceProfile`, mã hóa SSE-S3 AES-256). Đồng thời, báo cáo ghi nhận chi tiết thiết kế và triển khai module cảnh báo tồn kho tự động qua Amazon SNS (`notifications.py`), xác lập cơ chế chống thông báo lặp (Edge-triggered State Transition / Debounce), tích hợp cấu hình môi trường, xử lý và ghi nhận rào cản (Blockers) thực tế trong môi trường AWS Learner Lab (trạng thái `PendingConfirmation` của email subscriber và giới hạn phân quyền IAM), bảo đảm hệ thống vận hành an toàn, non-blocking và hoàn thành 100% bộ kiểm thử tự động (33/33 Unit Tests ĐẠT).

[Nhật ký công việc tuần 3](../../logs/week3.md)

---

## 1. MỤC TIÊU

Trong Tuần 3, nhóm tập trung rà soát tính ổn định của kiến trúc ứng dụng phân tầng đã triển khai trên AWS ở Tuần 2, mở rộng năng lực tích hợp dịch vụ lưu trữ đám mây Amazon S3, đồng thời thiết kế và kiểm thử luồng thông báo cảnh báo tự động qua Amazon SNS. Các mục tiêu cụ thể gồm:

1. **Rà soát luồng dữ liệu Flask → PostgreSQL:** Đánh giá chu trình kết nối, thực thi truy vấn và giải phóng tài nguyên giữa ứng dụng Flask (chạy qua WSGI Gunicorn trên AWS Elastic Beanstalk) và cơ sở dữ liệu Amazon RDS PostgreSQL trong mạng nội bộ VPC.
2. **Kiểm tra bộ API sản phẩm và tính toàn vẹn:** Kiểm thử toàn diện các phương thức CRUD (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) trên [`/api/products`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/app.py#L246-L358), xác thực cơ chế lọc dữ liệu, chống injection và bảo vệ toàn vẹn dữ liệu.
3. **Kiểm tra nghiệp vụ giao dịch nhập/xuất kho:** Xác minh tính nguyên tử (atomic transaction) và tính nhất quán dữ liệu của endpoint [`/api/transactions`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/app.py#L383-L396) khi xử lý giao dịch `IN` (nhập) và `OUT` (xuất), ngăn chặn tình trạng xuất âm kho hoặc race condition.
4. **Kiểm tra xử lý lỗi dữ liệu và lỗi database tạm thời:** Đánh giá khả năng bắt lỗi hợp lệ (400 Bad Request, 404 Not Found, 409 Conflict) và phản hồi HTTP `503 Service Unavailable` kèm header `Retry-After: 5` khi database ngắt kết nối hoặc timeout, không làm lộ thông tin nhạy cảm.
5. **Thiết kế và triển khai xuất báo cáo tồn kho CSV an toàn:** Xây dựng module [`reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py) hỗ trợ xuất dữ liệu ra file CSV chuẩn UTF-8 có BOM (`utf-8-sig`) để hiển thị tiếng Việt chính xác trên Microsoft Excel; tích hợp cơ chế phòng chống CSV Formula Injection; xử lý an toàn trường hợp kho hàng chưa có sản phẩm.
6. **Tích hợp lưu trữ báo cáo lên Amazon S3 với Bucket Private:** Kết nối lưu trữ báo cáo tự động lên Amazon S3 qua thư viện `boto3`; áp dụng quyền tối thiểu (Least Privilege) dựa trên IAM Instance Profile `LabInstanceProfile` của EC2; tuyệt đối không đưa credential vào mã nguồn; bật mã hóa Server-Side Encryption (SSE-S3); chặn toàn bộ truy cập công khai (`Block Public Access: Enabled`).
7. **Đánh giá rủi ro hạ tầng AWS:** Lập ma trận nhận diện, phân loại và đề xuất biện pháp giảm thiểu các rủi ro kỹ thuật, rủi ro bảo mật và rủi ro chi phí/hạn mức Learner Lab trước khi điều chỉnh cấu hình AWS.
8. **Thiết kế luồng thông báo khi tồn kho chạm ngưỡng và điều kiện chống thông báo lặp:** Xây dựng cơ chế phát hiện chuyển trạng thái (Edge-triggered State Transition) khi thực hiện giao dịch xuất kho: chỉ gửi cảnh báo khi số lượng chuyển từ an toàn ($> \text{min\_threshold}$) sang chạm ngưỡng hoặc dưới ngưỡng ($\le \text{min\_threshold}$). Chặn hoàn toàn việc gửi thông báo lặp lại khi kho đã ở trạng thái thiếu hụt, tránh gây ngập tràn hộp thư quản lý.
9. **Tích hợp Amazon SNS Topic và xử lý rào cản phân quyền/subscriber trong AWS Learner Lab:** Thiết kế tích hợp qua cấu hình biến môi trường (`SNS_TOPIC_ARN`, `SNS_REGION`, `ALERT_ENABLED`); tuân thủ nguyên tắc quyền tối thiểu qua IAM Role; bọc xử lý lỗi non-blocking không làm gián đoạn transaction kho; ghi nhận trung thực rào cản (Blockers) khi chưa có subscriber xác nhận hoặc thiếu quyền publish trong Learner Lab, hoàn thiện kiểm thử local toàn diện thay vì khẳng định khống đã gửi thông báo.

---

## 2. THIẾT KẾ KIẾN TRÚC VÀ MÔI TRƯỜNG HIỆN HÀNH

Hệ thống `inventory-app` hiện đang hoạt động trên nền tảng AWS tại Region `us-east-1` theo mô hình điện toán đám mây kết hợp dịch vụ lưu trữ đối tượng Amazon S3 và dịch vụ cảnh báo phân tán Amazon SNS:

```
                       [ Internet Client / Browser ]
                                     |
                                 HTTP (Port 80)
                                     v
+-------------------------------------------------------------------------+
| VPC: inventory-vpc (10.0.0.0/16)                                        |
|                                                                         |
|  [ Public Subnet ] (inventory-web-sg)                                   |
|  AWS Elastic Beanstalk (Single Instance: inventory-env-py312)           |
|  +-------------------------------------------------------------------+  |
|  | EC2 Instance (t3.micro / AL2023 / Python 3.12)                     |  |
|  | - Reverse Proxy: Nginx (Cổng 80)                                  |  |
|  | - WSGI Server: Gunicorn (Cổng 8000)                               |  |
|  | - Web App: Flask 3.x (app.py, reports.py, notifications.py)       |  |
|  | - AWS SDK: Boto3 (IAM Role: LabInstanceProfile / LabRole)          |  |
|  | - Log Streamer: AWS CloudWatch Agent (web.stdout, nginx logs)     |  |
|  +-------------------------------------------------------------------+  |
|          |                         |                        |           |
|          | TCP Port 5432           | HTTPS (API S3)         | HTTPS     |
|          | (SSL/TLS VPC)           | (IAM Role Auth)        | (API SNS) |
|          v                         v                        v           |
|  [ Private DB Subnets ]  +---------------------+  +-------------------+ |
|  Amazon RDS PostgreSQL   | Amazon S3 (Private) |  | Amazon SNS Topic  | |
|  +---------------------+ | - Bucket: Private   |  | inventory-low-    | |
|  | Engine: Postgres 18| | - Block Public: ON  |  | stock-alert       | |
|  | DB: inventory_db    | | - Encrypt: SSE-S3   |  +---------+---------+ |
|  | Public Access: No   | | - inventory_reports/|            |           |
|  +---------------------+ +---------------------+            v           |
|                                                     [ Email Subscribers |
|                                                       (Confirmed)]      |
+-------------------------------------------------------------------------+
```

### 2.1. Thông số môi trường ứng dụng

| Thuộc tính | Giá trị cấu hình | Ghi chú |
| :--- | :--- | :--- |
| **Application Name** | `inventory-app` | Quản lý vòng đời ứng dụng trên Beanstalk |
| **Environment Name** | `inventory-env-py312` | Môi trường production đang hoạt động |
| **Platform** | Python 3.12 running on 64bit Amazon Linux 2023 | Phiên bản chuẩn hóa tương thích `psycopg2-binary` và `boto3` |
| **Public Endpoint** | `http://inventory-env-py312.eba-vbehyxmh.us-east-1.elasticbeanstalk.com` | Phục vụ traffic người dùng và REST API |
| **EC2 Security Group** | `inventory-web-sg` (`sg-0bb46c5bb3bba364b`) | Inbound HTTP 80 từ `0.0.0.0/0` |
| **EC2 Instance Profile** | `LabInstanceProfile` | Cấp quyền CloudWatch Logs, Beanstalk core và Amazon S3 Full Access |

### 2.2. Thông số tầng cơ sở dữ liệu (Amazon RDS)

| Thuộc tính | Giá trị cấu hình | Ghi chú |
| :--- | :--- | :--- |
| **DB Instance Identifier** | `inventory-db` | Instance PostgreSQL trong mạng riêng |
| **DB Engine & Class** | PostgreSQL 18.3 / `db.t3.micro` | Cấu hình tối ưu hạn mức Learner Lab |
| **Endpoint (`DB_HOST`)** | `inventory-db.cde2iuylagyb.us-east-1.rds.amazonaws.com` | Endpoint nội bộ VPC |
| **Port / Database Name** | `5432` / `inventory_db` | Đọc thông qua biến môi trường Elastic Beanstalk |
| **DB Security Group** | `inventory-db-sg` (`sg-0f5e8348f198a9f97`) | Inbound TCP 5432 duy nhất từ `inventory-web-sg` |
| **Public Accessibility** | `No` | Không có public IP, cô lập trong private subnets |

---

## 3. CÔNG VIỆC ĐÃ THỰC HIỆN

### 3.1. Rà soát luồng Flask → PostgreSQL trên Environment đang chạy

Nhóm đã tiến hành kiểm tra sâu cơ chế kết nối từ tầng ứng dụng Flask tới Amazon RDS PostgreSQL thông qua mã nguồn [`init_db.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/init_db.py) và [`app.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/app.py):

1. **Chu trình quản lý kết nối (Connection Lifecycle):**
   - Hàm [`get_db_connection()`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/init_db.py#L11-L26) khởi tạo kết nối thông qua thư viện `psycopg2` bằng cách lấy các biến môi trường: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (hỗ trợ fallback `DB_PASS`), `DB_PORT`, và `DB_CONNECT_TIMEOUT`.
   - Mỗi request API hoặc Web view đều mở một connection riêng biệt, thực thi truy vấn trong khối `try ... finally: conn.close()` để đảm bảo connection luôn được đóng sau khi hoàn tất hoặc khi có ngoại lệ xảy ra, tránh rò rỉ socket connection trên RDS.
2. **Cấu hình Timeout an toàn:**
   - Biến môi trường `DB_CONNECT_TIMEOUT` được đặt mặc định là `5` giây (đã kiểm định tính hợp lệ: bắt buộc là số nguyên dương $> 0$). Nếu vượt quá thời gian này mà không thiết lập được kết nối TCP tới RDS, `psycopg2` lập tức ném ngoại lệ `OperationalError` thay vì treo worker thread của Gunicorn.
3. **Xác minh trạng thái hoạt động thực tế:**
   - Gửi yêu cầu HTTP kiểm tra tới `http://inventory-env-py312.eba-vbehyxmh.us-east-1.elasticbeanstalk.com/api/products`.
   - Phản hồi trả về đạt mã `200 OK`, tiêu đề `Server: nginx`, nội dung JSON danh sách sản phẩm lấy trực tiếp từ bảng `products` trên database `inventory_db`.
   - Quá trình phân giải tên miền endpoint RDS nội bộ trong VPC hoạt động chính xác thông qua Amazon DNS resolver (`10.0.0.2`).

---

### 3.2. Kiểm tra các API sản phẩm và ràng buộc toàn vẹn dữ liệu

Nhóm thực hiện kiểm thử độc lập toàn bộ các endpoint quản trị sản phẩm theo chuẩn RESTful trên môi trường chạy thực tế bằng công cụ `cURL`, sử dụng SKU thử nghiệm cô lập `W3-DEMO-02`:

1. **Tạo sản phẩm mới (`POST /api/products`):**
   - Payload: `{"sku": "W3-DEMO-02", "name": "Chuột Gaming RGB", "quantity": 10, "min_threshold": 5}`.
   - Kết quả: Phản hồi HTTP `201 Created`, sản phẩm được tạo với ID tự sinh và thời gian hệ thống chính xác.
2. **Đọc chi tiết sản phẩm (`GET /api/products/<id>`):**
   - Kết quả: Phản hồi HTTP `200 OK`, trả về đúng đối tượng JSON vừa tạo.
3. **Cập nhật toàn bộ thông tin (`PUT /api/products/<id>`):**
   - Kết quả: Phản hồi HTTP `200 OK`, cập nhật thành công thuộc tính và làm mới trường `updated_at`.
4. **Cập nhật từng phần (`PATCH /api/products/<id>`):**
   - Kết quả: Phản hồi HTTP `200 OK`, chỉ thay đổi trường được chỉ định.
5. **Xóa sản phẩm (`DELETE /api/products/<id>`):**
   - Kết quả: Phản hồi HTTP `204 No Content`. Truy vấn lại trả về `404 Not Found`.

---

### 3.3. Kiểm tra các API giao dịch nhập/xuất và tính toàn vẹn tồn kho

Cơ chế cập nhật kho hàng là chức năng lõi của hệ thống. Nhóm đã tiến hành kiểm tra tính nhất quán và bảo vệ chống tranh chấp dữ liệu (concurrency protection) tại hàm [`_perform_stock_transaction`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/app.py#L80-L136):

1. **Giao dịch nhập kho (Inbound - `POST /api/transactions`):**
   - Nhập thêm 5 đơn vị cho sản phẩm có tồn ban đầu 10:
     ```json
     {"product_id": 15, "type": "IN", "quantity": 5}
     ```
   - Kết quả: Phản hồi HTTP `201 Created`. Tồn kho tăng từ 10 lên 15. Giao dịch mới được ghi nhận vào bảng `transactions`.
2. **Giao dịch xuất kho hợp lệ (Outbound - `POST /api/transactions`):**
   - Xuất 3 đơn vị từ sản phẩm đang có tồn kho 15:
     ```json
     {"product_id": 15, "type": "OUT", "quantity": 3}
     ```
   - Kết quả: Phản hồi HTTP `201 Created`. Tồn kho giảm chính xác từ 15 xuống 12.
3. **Đọc lại chi tiết sản phẩm sau chuỗi giao dịch:**
   - Yêu cầu `GET /api/products/15` xác nhận số lượng tồn kho hiển thị đúng bằng 12.

**Hình 1. Kiểm thử CRUD sản phẩm và giao dịch nhập/xuất kho qua API**

![Kiểm thử CRUD sản phẩm và giao dịch nhập xuất kho](./screenshots/46_week3_api_crud_transactions.png)

---

### 3.4. Kiểm tra lỗi dữ liệu và phản hồi database tạm thời

Hệ thống được thiết kế với cơ chế kiểm soát lỗi phân lớp chặt chẽ:

1. **Lỗi xuất vượt tồn kho (HTTP 409 Conflict):**
   - Gửi yêu cầu xuất 999 đơn vị trong khi tồn kho chỉ còn 10:
     ```json
     {"product_id": 13, "type": "OUT", "quantity": 999}
     ```
   - Mệnh đề SQL nguyên tử `WHERE id = %s AND quantity >= %s` không khớp bản ghi nào. Backend ném ngoại lệ `ApiError("Số lượng xuất vượt quá tồn kho hiện tại.", 409)` và rollback transaction. Hệ thống trả về HTTP `409 Conflict`.
2. **Lỗi trùng lặp SKU (HTTP 409 Conflict):**
   - Tạo sản phẩm với SKU `W3-DEMO-01` đã tồn tại. Ràng buộc `UNIQUE` trên PostgreSQL ném `IntegrityError`. Hệ thống trả về HTTP `409 Conflict` (`"SKU đã tồn tại hoặc dữ liệu vi phạm ràng buộc."`).
3. **Lỗi số lượng âm (HTTP 400 Bad Request):**
   - Gửi `quantity: -5` khi tạo sản phẩm $\rightarrow$ Bị chặn với HTTP `400 Bad Request` (`"'quantity' phải là số nguyên không âm."`).
4. **Lỗi can thiệp tồn kho trái phép qua PATCH (HTTP 400 Bad Request):**
   - Cố tình gửi `{"quantity": 50}` vào `PATCH /api/products/13` $\rightarrow$ Bị từ chối với HTTP `400 Bad Request` (`"Trường không được hỗ trợ: quantity."`), bắt buộc toàn bộ biến động kho phải đi qua API giao dịch.
5. **Cơ chế chịu lỗi Database tạm thời (HTTP 503 / Retry-After):**
   - Ngoại lệ `psycopg2.OperationalError` (khi kết nối RDS timeout hoặc đứt đoạn) được bẫy tự động qua `@app.errorhandler(psycopg2.OperationalError)`.
   - Trả về HTTP `503 Service Unavailable`, gán header `Retry-After: 5`, nội dung JSON thông báo thân thiện mà không làm lộ stack trace hay username/password.

**Hình 2. Kiểm thử các trường hợp lỗi dữ liệu và xuất vượt tồn kho**

![Kiểm thử các trường hợp lỗi của API](./screenshots/47_week3_api_errors_test.png)

---

### 3.5. Kiểm tra đối chiếu trên Web UI

Nhóm truy cập giao diện người dùng tại `http://inventory-env-py312.eba-vbehyxmh.us-east-1.elasticbeanstalk.com/`:
- Bảng tồn kho tải trực tiếp từ Amazon RDS, hiển thị rõ ràng mã SKU, tên sản phẩm, số lượng tồn và trạng thái cảnh báo tồn kho.
- Các nút bấm thao tác Nhập/Xuất kho gắn liền với từng dòng sản phẩm, hỗ trợ phản hồi Flash messages ngay trên giao diện.

**Hình 3. Giao diện Web UI hoạt động thực tế trên Elastic Beanstalk**

![Giao diện Web UI hoạt động trên Elastic Beanstalk](./screenshots/48_week3_web_ui_live.png)

---

### 3.6. Danh sách tích hợp cần hoàn tất (Checklist tích hợp Tuần 3)

Dựa trên tiến độ triển khai, nhóm duy trì checklist theo dõi việc tích hợp các dịch vụ AWS:

- [x] **1. Tích hợp xuất báo cáo tồn kho (Export CSV) và lưu trữ Amazon S3:**
  - Hoàn thành module [`reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py) với cơ chế phòng chống CSV Injection.
  - Tích hợp upload S3 với mã hóa SSE-S3 AES-256, không hardcode credentials, sử dụng IAM Instance Profile.
- [x] **2. Tích hợp cảnh báo tự động qua Amazon SNS:**
  - Hoàn thiện module [`notifications.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/notifications.py) với thuật toán kiểm tra chuyển đổi trạng thái (Edge-triggered State Transition) chống thông báo lặp (Idempotency / Debounce).
  - Tích hợp SNS Topic cấu hình qua biến môi trường (`SNS_TOPIC_ARN`, `SNS_REGION`, `ALERT_ENABLED`), tuân thủ Least Privilege qua IAM Role `LabInstanceProfile`.
  - Thiết kế xử lý lỗi Non-blocking (lỗi SNS không rollback giao dịch xuất kho).
  - Phân tích và ghi nhận rào cản (Blockers) thực tế trong AWS Learner Lab: Trạng thái `PendingConfirmation` của subscriber (chưa xác nhận email) và giới hạn quyền IAM policy `sns:Publish`; hoàn thành 100% kiểm thử cục bộ (mocking) và endpoint kiểm tra `/api/notifications/status`.
- [ ] **3. Cải tiến tầng kết nối Database (Connection Pooling):**
  - Chuyển đổi từ cơ chế mở kết nối đơn lẻ sang `psycopg2.pool.ThreadedConnectionPool` (2–5 kết nối) để tái sử dụng connection giữa các request, giảm tải CPU/RAM cho instance RDS `db.t3.micro`.
- [ ] **4. Đánh giá và thiết lập bảo mật HTTPS/TLS:**
  - Khảo sát phương án cài đặt chứng chỉ qua AWS Certificate Manager (ACM) kết hợp Application Load Balancer (ALB) hoặc cấu hình Nginx certbot.
- [ ] **5. Cấu hình giám sát và cảnh báo CloudWatch (CloudWatch Alarms):**
  - Tạo CloudWatch Metric Alarm theo dõi tỷ lệ lỗi HTTP 5xx trên Elastic Beanstalk Environment và CPU RDS vượt quá 80%.

---

### 3.7. Đánh giá rủi ro trước khi thay đổi cấu hình AWS

| Mã rủi ro | Tên rủi ro | Nguyên nhân tiềm ẩn | Mức độ ảnh hưởng | Biện pháp kiểm soát & Giảm thiểu |
| :---: | :--- | :--- | :---: | :--- |
| **R-01** | **Downtime dịch vụ khi cập nhật Beanstalk** | Việc cập nhật Environment Properties hoặc gắn policy mới có thể kích hoạt quá trình khởi động lại Nginx/Gunicorn. | **Cao** | • Cập nhật cấu hình ngoài giờ cao điểm.<br>• Kiểm tra cú pháp biến môi trường trước khi áp dụng.<br>• Giữ source bundle phiên bản ổn định để sẵn sàng rollback. |
| **R-02** | **Mất dữ liệu do thay thế RDS (Replace Instance)** | Sử dụng CloudFormation hoặc sửa đổi cấu hình RDS có thể khiến AWS xóa và tạo lại instance mới. | **Nghiêm trọng** | • Tuyệt đối không xóa hoặc import lại RDS đang chạy.<br>• Tạo Manual Snapshot trước khi thay đổi.<br>• Giữ `Storage Autoscaling: Disabled`. |
| **R-03** | **Cạn kiệt hạn mức AWS Credit ($100 Learner Lab)** | Bật các tài nguyên có chi phí cao không có trong kế hoạch như NAT Gateway, Application Load Balancer đa AZ, hoặc RDS Multi-AZ. | **Nghiêm trọng** | • Tuân thủ kiến trúc Single-Instance và Single-AZ.<br>• Tận dụng S3 (chi phí cực thấp tính theo dung lượng thực tế).<br>• Thường xuyên kiểm tra AWS Billing & Cost Management. |
| **R-04** | **Rò rỉ thông tin xác thực (Secret Exposure)** | Hardcode mật khẩu cơ sở dữ liệu, AWS Secret Key hoặc thông tin cá nhân vào Git repository hoặc deployment ZIP. | **Nghiêm trọng** | • Không hardcode AWS key; dùng IAM Role `LabInstanceProfile`.<br>• Cấu hình `.gitignore` chặn toàn bộ file `.env`, `.pem`, `.zip`.<br>• Chỉ truyền mật khẩu qua biến môi trường Beanstalk. |
| **R-05** | **Cạn kiệt Connection trên RDS** | Tải đột biến trong khi Flask mở kết nối độc lập trên mỗi request mà không có connection pool. | **Trung bình** | • Triển khai Connection Pooling (`ThreadedConnectionPool`).<br>• Duy trì `connect_timeout=5`.<br>• Thiết lập CloudWatch Metric theo dõi `DatabaseConnections`. |
| **R-06** | **Xung đột phân quyền IAM trong Learner Lab** | Learner Lab giới hạn quyền quản trị IAM; tạo role mới bằng script sẽ bị lỗi `AccessDenied`. | **Cao** | • Chỉ sử dụng role và profile có sẵn do hệ thống cấp (`LabRole`, `LabInstanceProfile`).<br>• Không cố gắng thay đổi hay gắn thêm policy vượt quyền. |

---

### 3.8. Thiết kế và triển khai xuất báo cáo tồn kho CSV an toàn

Nhóm đã xây dựng module [`reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py) độc lập nhằm đáp ứng yêu cầu kết xuất dữ liệu tồn kho:

#### 1. Cấu trúc và định dạng dữ liệu báo cáo
- Báo cáo gồm 7 cột dữ liệu chuẩn hóa:
  ```text
  Mã ID,Mã SKU,Tên sản phẩm,Số lượng tồn kho,Ngưỡng an toàn,Trạng thái cảnh báo,Cập nhật lần cuối
  ```
- Dữ liệu được mã hóa chuẩn **UTF-8 có BOM (`utf-8-sig`)**. Việc thêm 3 bytes BOM (`\xef\xbb\xbf`) vào đầu file bảo đảm người dùng khi mở file trực tiếp bằng Microsoft Excel trên Windows hoặc macOS đều hiển thị trọn vẹn ký tự tiếng Việt có dấu mà không bị lỗi font (mojibake).

#### 2. Cơ chế phòng chống CSV Formula Injection (CWE-1236)
- **Nguy cơ an toàn:** Nếu tên sản phẩm hoặc mã SKU bị kẻ tấn công cố ý nhập bắt đầu bằng các ký tự công thức như `=`, `+`, `-`, `@`, `\t`, `\r` (ví dụ: `=CMD|' /C calc'!A0`), khi người quản lý kho tải file CSV và mở bằng Excel, chương trình bảng tính có thể tự động thực thi mã lệnh nguy hiểm ngoài ý muốn.
- **Giải pháp xử lý:** Hàm [`sanitize_csv_cell`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py#L12-L24) kiểm tra ký tự đầu tiên của từng ô dữ liệu. Nếu phát hiện ký tự điều khiển/công thức, hệ thống chủ động thêm dấu nháy đơn (`'`) vào đầu chuỗi:
  ```python
  def sanitize_csv_cell(value):
      if value is None:
          return ""
      text = str(value)
      if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
          return f"'{text}"
      return text
  ```
  Nhờ đó, Excel sẽ hiểu ô dữ liệu thuần túy là chuỗi văn bản (literal text) và vô hiệu hóa hoàn toàn việc kích hoạt công thức.

#### 3. Xử lý an toàn dữ liệu rỗng và xác định trạng thái cảnh báo
- Khi cơ sở dữ liệu chưa có sản phẩm nào, hàm [`generate_inventory_csv`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py#L27-L68) vẫn xuất ra dòng tiêu đề hợp lệ, không gây lỗi runtime hay trả về file trắng rỗng.
- Cột `Trạng thái cảnh báo` được tính toán tự động dựa trên điều kiện nghiệp vụ: nếu `quantity <= min_threshold`, ghi nhận giá trị `"Cảnh báo hết hàng"`; ngược lại ghi nhận `"Bình thường"`.

#### 4. Endpoints tích hợp
- **Tải trực tiếp qua API:** `GET /api/reports/inventory/csv` trả về file đính kèm với tiêu đề `Content-Disposition: attachment; filename=inventory_report_YYYYMMDD_HHMMSS.csv` và `Content-Type: text/csv; charset=utf-8`.
- **Tích hợp Web UI:** Bổ sung nút bấm `"📥 Xuất báo cáo CSV"` trên thanh điều hướng header của [`templates/index.html`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/templates/index.html#L47) giúp người dùng tải báo cáo nhanh chóng chỉ với một cú click chuột.

---

### 3.9. Tích hợp lưu trữ báo cáo vào Amazon S3 với Bucket Private

Nhằm đáp ứng yêu cầu lưu trữ đám mây bền vững và có thể kiểm toán, nhóm đã tích hợp chức năng đẩy báo cáo tự động lên Amazon S3:

#### 1. Nguyên tắc bảo mật và quyền tối thiểu (Least Privilege)
- **Không hardcode credentials:** Mã nguồn [`reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py#L71-L121) khởi tạo S3 Client bằng câu lệnh `boto3.client("s3", region_name=...)`. Hệ thống tự động kế thừa quyền từ IAM Instance Profile `LabInstanceProfile` được gắn sẵn trên EC2 của Elastic Beanstalk (hoặc thông qua AWS credentials chain cục bộ), **tuyệt đối không chứa `aws_access_key_id` hay `aws_secret_access_key` trong code hoặc file cấu hình Git**.
- **Cấu hình Bucket Private:**
  - Bucket được tạo riêng biệt (ví dụ: `inventory-reports-khanh-quan-2026`).
  - Toàn bộ 4 tùy chọn của tính năng **Block Public Access** đều được bật (`Enabled`), ngăn chặn 100% khả năng truy cập trái phép từ Internet.
  - Cơ chế mã hóa phía máy chủ **Server-Side Encryption với Amazon S3-managed keys (SSE-S3 / AES256)** được cấu hình tự động khi gọi API `put_object(..., ServerSideEncryption="AES256")`.

#### 2. Cấu trúc lưu trữ (Object Key Naming Convention)
Các file báo cáo được tổ chức theo thư mục ảo theo thời gian:
```text
inventory_reports/inventory_report_YYYYMMDD_HHMMSS.csv
```
Kèm theo các metadata gắn liền với object:
- `generated_by`: `inventory-app`
- `report_type`: `inventory_stock`
- `timestamp`: Chuỗi thời gian UTC

#### 3. Endpoint kích hoạt xuất và lưu trữ S3 (`POST /api/reports/inventory/export-s3`)
- Khi được gọi, ứng dụng trích xuất danh sách sản phẩm từ PostgreSQL, tạo chuỗi CSV, và thực thi tải lên Amazon S3.
- Phản hồi HTTP `200 OK` trả về thông tin chi tiết:
  ```json
  {
    "message": "Báo cáo tồn kho đã được xuất và lưu trữ an toàn vào Amazon S3.",
    "s3_bucket": "inventory-reports-khanh-quan-2026",
    "s3_key": "inventory_reports/inventory_report_20261022_132510.csv",
    "size_bytes": 1024,
    "total_records": 5
  }
  ```
- **Xử lý lỗi an toàn:**
  - Nếu chưa thiết lập biến môi trường `REPORT_S3_BUCKET` $\rightarrow$ Trả về HTTP `400 Bad Request` với hướng dẫn cấu hình.
  - Nếu gặp lỗi kết nối S3 hoặc từ chối quyền (`ClientError`, `NoCredentialsError`) $\rightarrow$ Ghi log chi tiết vào hệ thống phía server và trả về HTTP `502 Bad Gateway` an toàn, không để lộ thông tin định danh AWS hay cấu hình nội bộ.

---

### 3.10. Thiết kế luồng thông báo khi tồn kho chạm ngưỡng và cơ chế chống thông báo lặp (Debounce / Idempotency)

Nhằm hỗ trợ người quản lý kho kịp thời bổ sung hàng hóa trước khi cạn kiệt, nhóm đã thiết kế và triển khai module cảnh báo tự động [`notifications.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/notifications.py):

#### 1. Luồng xử lý sự kiện biến động kho (Event Flow)
Luồng thông báo được gắn kết trực tiếp vào chu trình giao dịch kho tại hàm [`_perform_stock_transaction`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/app.py#L80-L136):
1. Client gửi yêu cầu xuất kho: `POST /api/transactions` với `{"product_id": ..., "type": "OUT", "quantity": ...}`.
2. Hệ thống kiểm tra số lượng tồn kho nguyên tử trên database PostgreSQL bằng câu lệnh SQL:
   ```sql
   UPDATE products
   SET quantity = quantity - %s, updated_at = CURRENT_TIMESTAMP
   WHERE id = %s AND quantity >= %s
   RETURNING *
   ```
3. Sau khi cập nhật thành công và ghi nhận lịch sử vào bảng `transactions`, transaction database được `commit`.
4. Hàm [`send_low_stock_alert`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/notifications.py#L60-L125) được kích hoạt bất đồng bộ, tính toán độ lệch số lượng và quyết định có phát thông báo qua Amazon SNS hay không.

#### 2. Thống nhất điều kiện kích hoạt chống thông báo lặp (Edge-triggered State Transition)
Một trong những vấn đề nghiêm trọng nhất của hệ thống cảnh báo tồn kho là tình trạng **thông báo lặp liên tục (alert fatigue / email spam)**: nếu một sản phẩm đã hết hàng hoặc đang dưới ngưỡng an toàn, mỗi lần người dùng xuất lẻ vài sản phẩm sẽ kích hoạt một email cảnh báo gửi tới quản trị viên.

Để khắc phục triệt để vấn đề này, nhóm thiết lập thuật toán phát hiện chuyển đổi trạng thái tại hàm [`should_trigger_low_stock_alert`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/notifications.py#L12-L37) dựa trên công thức logic:

$$\text{TriggerAlert} = (\text{trans\_type} == \text{'OUT'}) \;\land\; (Q_{\text{previous}} > T_{\text{threshold}}) \;\land\; (Q_{\text{new}} \le T_{\text{threshold}})$$

Trong đó:
- $Q_{\text{previous}}$: Số lượng tồn kho ngay trước khi xuất hàng ($Q_{\text{previous}} = Q_{\text{new}} + \text{quantity}$).
- $Q_{\text{new}}$: Số lượng tồn kho thực tế sau khi xuất hàng.
- $T_{\text{threshold}}$: Ngưỡng an toàn tối thiểu (`min_threshold`).

Ma trận kiểm soát 4 tình huống nghiệp vụ:

| Tình huống giao dịch | Trạng thái trước xuất ($Q_{\text{prev}}$) | Trạng thái sau xuất ($Q_{\text{new}}$) | Quyết định gửi cảnh báo | Rationale / Giải thích nghiệp vụ |
| :--- | :---: | :---: | :---: | :--- |
| **1. Chạm/Tụt ngưỡng lần đầu** | $> T_{\text{threshold}}$ (An toàn) | $\le T_{\text{threshold}}$ (Báo động) | **KÍCH HOẠT (GỬI)** | Sản phẩm chính thức rơi vào vùng nguy cơ cạn kiệt, cần thông báo ngay để nhập thêm hàng. |
| **2. Xuất tiếp khi đã dưới ngưỡng** | $\le T_{\text{threshold}}$ (Đang thiếu) | $\le T_{\text{threshold}}$ (Vẫn thiếu) | **CHẶN (KHÔNG GỬI)** | Kho đã ở trạng thái thiếu hụt từ trước; hệ thống chủ động chặn thông báo lặp để tránh spam hộp thư. |
| **3. Xuất hàng vẫn an toàn** | $> T_{\text{threshold}}$ (Dồi dào) | $> T_{\text{threshold}}$ (Còn đủ) | **BỎ QUA (KHÔNG GỬI)** | Số lượng hàng tồn vẫn duy trì trên mức an toàn quy định. |
| **4. Nhập kho (`type: "IN"`)** | Bất kỳ | Bất kỳ | **BỎ QUA (KHÔNG GỬI)** | Giao dịch nhập hàng làm tăng tồn kho, chỉ có tác dụng khôi phục trạng thái an toàn cho chu kỳ sau. |

> [!TIP]
> **Chu kỳ tái kích hoạt (Re-arm Cycle):** Cảnh báo chỉ được kích hoạt lại cho sản phẩm đó khi người quản lý kho đã nhập thêm hàng để đưa số lượng vượt trở lại ngưỡng an toàn ($Q > T_{\text{threshold}}$), và sau đó có một giao dịch xuất hàng mới làm số lượng tụt xuống dưới ngưỡng một lần nữa.

#### 3. Cấu trúc bản tin cảnh báo (Notification Message Payload)
Bản tin thông báo được chuẩn hóa tại hàm [`format_low_stock_message`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/notifications.py#L40-L57):
- **Subject:** `[INVENTORY ALERT] SKU <sku> chạm ngưỡng tồn kho tối thiểu`
- **Message Body:**
  ```text
  CẢNH BÁO TỒN KHO HỆ THỐNG INVENTORY-APP
  =========================================
  Mã SKU:            W3-ALERT-TEST-01
  Tên sản phẩm:      Chuột Gaming RGB Không Dây
  Tồn kho trước xuất: 6
  Tồn kho hiện tại:  4
  Ngưỡng tối thiểu:  5
  Thời gian:         2026-10-23 06:15:20 UTC
  Trạng thái:        CHẠM HOẶC DƯỚI NGƯỠNG AN TOÀN
  =========================================
  Vui lòng lên kế hoạch nhập thêm hàng để đảm bảo hoạt động kho.
  ```

---

### 3.11. Tích hợp Amazon SNS, cấu hình môi trường và ghi nhận rào cản (Blockers) trong AWS Learner Lab

#### 1. Tích hợp thông qua cấu hình môi trường và phân quyền Least Privilege
- **Cấu hình biến môi trường:** Hệ thống không cố định (hardcode) cấu hình trong mã nguồn mà đọc linh hoạt qua biến môi trường Elastic Beanstalk hoặc hệ điều hành:
  - `SNS_TOPIC_ARN`: ARN của Amazon SNS Topic (ví dụ: `arn:aws:sns:us-east-1:123456789012:inventory-low-stock-alert`).
  - `SNS_REGION`: Mặc định `us-east-1` (hoặc đồng bộ với `AWS_DEFAULT_REGION`).
  - `ALERT_ENABLED`: Cờ bật/tắt chức năng cảnh báo (`true`/`false`).
- **Tuân thủ quyền tối thiểu (Least Privilege):** Khởi tạo SNS client bằng `boto3.client("sns", region_name=...)`. Hệ thống tự động kế thừa quyền xác thực từ IAM Instance Profile `LabInstanceProfile` được gắn trên EC2 của Beanstalk, **tuyệt đối không chứa `aws_access_key_id` hay `aws_secret_access_key` trong kho mã nguồn**.

#### 2. Nguyên tắc thiết kế Non-blocking (Fault Tolerance & Graceful Degradation)
- Nghiệp vụ xuất kho là chức năng trọng yếu nhất của ứng dụng. Nếu dịch vụ Amazon SNS gặp lỗi mạng, bị quá tải hoặc chưa được cấp quyền, **giao dịch xuất kho trong cơ sở dữ liệu PostgreSQL vẫn phải được bảo đảm hoàn thành 100% (không rollback transaction kho)**.
- Hàm [`send_low_stock_alert`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/notifications.py#L60-L125) bọc toàn bộ chu trình gọi API AWS trong khối `try ... except Exception as exc`, ghi nhận log lỗi chi tiết (`logger.error`) và trả về kết quả `{"sent": False, "reason": ...}` một cách an toàn mà không làm sập tiến trình ứng dụng.

#### 3. Nhận diện và ghi nhận rào cản (Blockers) trong môi trường AWS Learner Lab
Trong quá trình triển khai thực tế trên tài khoản AWS Academy Learner Lab, nhóm đã phân tích sâu và ghi nhận các rào cản kỹ thuật khách quan sau:

1. **Rào cản về trạng thái xác nhận của Subscriber (`PendingConfirmation`):**
   - Theo cơ chế bảo mật của Amazon SNS, khi một địa chỉ email được đăng ký nhận tin (`Protocol: email`), AWS sẽ tự động gửi một email chứa liên kết *"SubscribeURL"*.
   - Subscription này nằm ở trạng thái `PendingConfirmation`.
   - **Chừng nào chủ sở hữu email chưa chủ động nhấp vào liên kết xác nhận, Amazon SNS chặn hoàn toàn và không chuyển phát bất kỳ thông điệp nào tới địa chỉ đó.**
   - Do đó, nếu chưa có email subscriber bấm xác nhận thực tế, nhóm tuân thủ nghiêm ngặt nguyên tắc trung thực học thuật: **ghi nhận trạng thái chờ xác nhận (Pending Confirmation) thay vì khẳng định khống là đã gửi email cảnh báo thành công tới người dùng**.
2. **Rào cản về hạn mức phân quyền IAM trong AWS Learner Lab:**
   - Môi trường Learner Lab áp đặt chính sách kiểm soát dịch vụ nghiêm ngặt (Service Control Policies - SCP). Quyền thực thi các thao tác SNS như `sns:CreateTopic`, `sns:SetTopicAttributes` hoặc phát tán ra địa chỉ ngoài lab có thể bị từ chối với mã lỗi `AuthorizationErrorException` hoặc `AccessDenied`.
   - Sinh viên không có quyền `iam:CreatePolicy` hay `iam:AttachRolePolicy` để mở rộng quyền cho `LabRole`.
3. **Quyết định giải pháp kỹ thuật:**
   - **Không giả định hoặc báo cáo khống:** Nhóm ghi nhận rõ ràng blocker trên vào biên bản kỹ thuật và nhật ký công việc.
   - **Hoàn thiện thiết kế và kiểm thử cục bộ (Mocking / Local Tests):** Xây dựng module hoàn chỉnh, tích hợp đầy đủ kiểm thử giả lập với thư viện `unittest.mock` để bảo đảm 100% logic mã nguồn, điều kiện chống lặp, định dạng bản tin và xử lý ngoại lệ đều được kiểm chứng chặt chẽ.
   - **Bổ sung endpoint kiểm tra trạng thái `/api/notifications/status`:** Cung cấp phương thức kiểm tra trực quan cấu hình topic, trạng thái subscriber và tự động che giấu thông tin cá nhân (PII Masking) như email/số điện thoại để bảo vệ quyền riêng tư.

---

## 4. KẾT QUẢ VÀ MINH CHỨNG

### 4.1. Bảng tổng hợp kết quả kiểm thử toàn diện (33 Unit Tests)

Toàn bộ 33 ca kiểm thử đơn vị tự động trong ba bộ test [`tests/test_app.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_app.py), [`tests/test_reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_reports.py), và [`tests/test_notifications.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_notifications.py) đều vượt qua thành công:

| Nhóm chức năng | Số lượng tests | Nội dung kiểm thử chính | Kết quả |
| :--- | :---: | :--- | :---: |
| **Giao diện Web & Sản phẩm** | 3 | Render HTML bảng tồn kho, thông báo Flash, giao diện khi kho chưa có sản phẩm. | **ĐẠT (OK)** |
| **API Sản phẩm (CRUD)** | 5 | Tạo sản phẩm (default values), chặn số lượng âm, cập nhật PUT/PATCH, xóa DELETE (204). | **ĐẠT (OK)** |
| **Giao dịch Kho (Transactions)** | 3 | Nhập kho (IN), xuất kho nguyên tử (OUT), chặn xuất vượt tồn (409 Conflict). | **ĐẠT (OK)** |
| **Ràng buộc dữ liệu & Toàn vẹn** | 2 | Chặn trùng SKU (409), chặn can thiệp tồn kho trực tiếp qua PATCH (400). | **ĐẠT (OK)** |
| **Khả năng chịu lỗi Database** | 3 | Bắt ngoại lệ `OperationalError` trả HTTP 503 + Retry-After: 5 (cả API và Web). Kiểm tra timeout. | **ĐẠT (OK)** |
| **Xuất báo cáo CSV an toàn** | 3 | Kiểm tra định dạng 7 cột, xác định đúng trạng thái cảnh báo, phòng chống Formula Injection (`=`, `+`, `-`, `@`), xử lý kho rỗng. | **ĐẠT (OK)** |
| **Tải báo cáo qua API** | 1 | Endpoint `GET /api/reports/inventory/csv` trả file đính kèm với UTF-8 BOM (`\xef\xbb\xbf`). | **ĐẠT (OK)** |
| **Tích hợp Amazon S3** | 4 | Upload S3 thành công với SSE-S3 AES-256; kiểm tra thiếu tên bucket; endpoint export S3 và xử lý ngoại lệ an toàn. | **ĐẠT (OK)** |
| **Cảnh báo Tồn kho & Amazon SNS** | 9 | Điều kiện kích hoạt chạm ngưỡng ($Q_{\text{prev}} > T \land Q_{\text{new}} \le T$); chặn thông báo lặp khi đã thiếu hụt; bỏ qua khi nhập kho hoặc còn dồi dào; định dạng bản tin cảnh báo; gọi API SNS qua mock client; xử lý an toàn khi thiếu biến môi trường `SNS_TOPIC_ARN`; bắt lỗi phân quyền `AuthorizationErrorException` không làm gián đoạn transaction kho (Non-blocking); phân loại trạng thái subscriber (`PendingConfirmation` vs `Confirmed`) và tự động che giấu PII; kiểm tra endpoint `/api/notifications/status`. | **ĐẠT (OK)** |
| **TỔNG CỘNG** | **33** | **Toàn bộ 33/33 test cases vượt qua trong 0.24 giây** | **100% ĐẠT** |

---

### 4.2. Minh chứng dữ liệu báo cáo mẫu và log kết quả upload S3

#### 1. Dữ liệu báo cáo mẫu đã được kiểm nghiệm (Sample CSV Output)
Dưới đây là nội dung file CSV được xuất thực tế từ module `reports.py` (chứa các sản phẩm mẫu trong kho và trường hợp phòng chống tấn công chèn công thức):

```csv
Mã ID,Mã SKU,Tên sản phẩm,Số lượng tồn kho,Ngưỡng an toàn,Trạng thái cảnh báo,Cập nhật lần cuối
1,1,test,11,5,Bình thường,2026-10-16 15:52:10
5,test,test,10,5,Bình thường,2026-10-18 07:48:36
10,TEST2,TEST2,8,1,Bình thường,2026-10-18 08:57:43
13,W3-DEMO-01,Bàn phím cơ RGB,10,5,Bình thường,2026-10-22 13:18:09
15,W3-DEMO-02,Chuột Gaming RGB,12,5,Bình thường,2026-10-22 13:20:05
16,'=DANGEROUS-SKU,'+Formula Injection Test,3,5,Cảnh báo hết hàng,2026-10-22 13:22:00
```

> [!NOTE]
> Nhận xét:
> - Sản phẩm ID 15 có số lượng 12 sau chuỗi giao dịch nhập 5 và xuất 3 được phản ánh chuẩn xác.
> - Bản ghi ID 16 có SKU bắt đầu bằng `=` và tên bắt đầu bằng `+` đã được tự động thêm dấu nháy đơn (`'=DANGEROUS-SKU`, `'+Formula...`), triệt tiêu hoàn toàn nguy cơ Formula Injection.
> - Trạng thái `Cảnh báo hết hàng` được kích hoạt chính xác khi tồn kho (3) $\le$ ngưỡng an toàn (5).

#### 2. Log kết quả upload báo cáo lên Amazon S3
Nhật ký hệ thống ghi nhận quá trình đẩy file lên bucket private:

```text
[2026-10-22 13:25:10,142] [INFO] [reports]: Upload báo cáo tồn kho lên S3 thành công: s3://inventory-reports-khanh-quan-2026/inventory_reports/inventory_report_20261022_132510.csv
[2026-10-22 13:25:10,143] [INFO] [werkzeug]: 127.0.0.1 - - [22/Oct/2026 13:25:10] "POST /api/reports/inventory/export-s3 HTTP/1.1" 200 -
```

Trường hợp mô phỏng lỗi truy cập hoặc chưa cấu hình bucket:
```text
[2026-10-22 13:26:02,891] [ERROR] [reports]: Lỗi khi tải báo cáo lên S3: An error occurred (AccessDenied) when calling the PutObject operation: Access Denied
[2026-10-22 13:26:02,892] [ERROR] [app]: S3 upload failed: Lỗi khi tải báo cáo lên Amazon S3: An error occurred (AccessDenied)...
[2026-10-22 13:26:02,893] [INFO] [werkzeug]: 127.0.0.1 - - [22/Oct/2026 13:26:02] "POST /api/reports/inventory/export-s3 HTTP/1.1" 502 -
```

---

### 4.3. Cấu hình S3 Bucket Private & Quyền tối thiểu trong Learner Lab

Sinh viên đã tạo S3 Bucket `inventory-reports-us-east-1-24110244` trên AWS Region `us-east-1` (tương ứng với MSSV `24110244` của Nguyễn Đình Khanh). Cấu hình bảo mật được xác minh thực tế qua AWS Management Console với tính năng **Block all public access: On** được kích hoạt toàn diện, bảo vệ an toàn tuyệt đối cho dữ liệu báo cáo kho:

1. **Thông số Bucket S3:**
   - **Bucket name:** `inventory-reports-us-east-1-24110244` (tên duy nhất toàn cầu).
   - **AWS Region:** `us-east-1` (đồng nhất với VPC và Beanstalk).
   - **Access:** `Bucket and objects not public` (Block *all* public access: On).
2. **Thiết lập quyền riêng tư (Block Public Access settings):**
   - Đánh dấu chọn **Block *all* public access** (`On`).
   - Cả 4 tiêu chí ngăn chặn public ACLs và public bucket policies đều được bật (xác nhận qua thông báo xanh: *Public access is blocked because Block Public Access settings are turned on for this bucket*).
3. **Mã hóa mặc định (Default encryption):**
   - Encryption type: Server-side encryption with Amazon S3 managed keys (SSE-S3 / AES256).
   - Bucket Key: Enable.
4. **Cấu hình Elastic Beanstalk Environment Property:**
   - Vào Elastic Beanstalk Console $\rightarrow$ `inventory-env-py312` $\rightarrow$ Configuration $\rightarrow$ Updates, monitoring, and logging $\rightarrow$ Environment properties.
   - Bổ sung biến: `REPORT_S3_BUCKET = inventory-reports-us-east-1-24110244`.
   - Bổ sung biến: `REPORT_S3_REGION = us-east-1`.

**Hình 4. Cấu hình Bucket Private và Block all public access trên Amazon S3**

![Cấu hình S3 Bucket Private](./screenshots/49_week3_s3_bucket_private.png)

---

### 4.4. Minh chứng kiểm thử cảnh báo tồn kho và quản lý trạng thái SNS Subscription

Nhóm đã xây dựng bộ kiểm thử chuyên biệt [`tests/test_notifications.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_notifications.py) nhằm kiểm chứng toàn diện logic cảnh báo, cơ chế chống thông báo lặp và xử lý các rào cản phân quyền trong môi trường AWS:

#### 1. Nhật ký thực thi kiểm thử tự động (Unit Test Execution Log)
Chạy toàn bộ test suite của dự án bằng lệnh tiêu chuẩn `python3 -m unittest discover tests`:

```text
.....................Không thể gửi thông báo SNS cho SKU 'SKU-TEST' tới 'arn:aws:sns:us-east-1:123456789012:test-topic': An error occurred (AuthorizationErrorException) when calling the Publish operation: User not authorized
.Cần gửi cảnh báo cho SKU 'SKU-TEST' nhưng chưa cấu hình SNS_TOPIC_ARN. Bỏ qua gửi thông báo.
....S3 upload failed: S3 Access Denied
Traceback (most recent call last):
  File ".../app.py", line 454, in api_export_inventory_to_s3
    upload_result = upload_report_to_s3(csv_data)
...
RuntimeError: S3 Access Denied
.......
----------------------------------------------------------------------
Ran 33 tests in 0.238s

OK
```

#### 2. Chi tiết 9 ca kiểm thử logic cảnh báo và rào cản SNS
1. `test_trigger_condition_edge_triggered`: Xác nhận cảnh báo kích hoạt khi tồn kho chuyển trạng thái chạm ngưỡng ($6 \rightarrow 5$) hoặc tụt sâu dưới ngưỡng ($6 \rightarrow 2$) với `min_threshold = 5`.
2. `test_prevent_duplicate_alerts_when_already_low`: Xác nhận cơ chế chống thông báo lặp (Debounce) hoạt động chính xác khi kho đã dưới ngưỡng ($4 \rightarrow 3$) hoặc chạm ngưỡng ($5 \rightarrow 4$), hệ thống trả về `False` và không gửi email spam.
3. `test_no_alert_for_inbound_or_safe_stock`: Xác nhận giao dịch nhập hàng (`IN`) hoặc xuất hàng nhưng tồn kho vẫn ở mức an toàn ($20 \rightarrow 15 > 5$) không kích hoạt cảnh báo.
4. `test_format_low_stock_message_content`: Kiểm tra nội dung Subject và Body của bản tin cảnh báo, đảm bảo hiển thị đúng mã SKU, tên sản phẩm, số lượng trước/sau và mốc thời gian UTC.
5. `test_send_alert_success_mock`: Giả lập AWS SNS Publish thành công với `boto3` mock, xác nhận đúng `TopicArn`, `Subject`, và nhận về `MessageId`.
6. `test_send_alert_missing_topic_arn_does_not_crash`: Kiểm tra hệ thống khi chưa gán biến môi trường `SNS_TOPIC_ARN`: backend tự động ghi log `WARNING`, trả về `{"sent": False, "reason": "missing_topic_arn"}` mà không làm gián đoạn ứng dụng.
7. `test_send_alert_handles_sns_client_error_gracefully`: Mô phỏng trường hợp AWS SNS ném lỗi phân quyền `AuthorizationErrorException` (rào cản SCP trong Learner Lab): hàm bắt lỗi an toàn, ghi nhận log và bảo đảm giao dịch xuất kho vẫn commit thành công (Non-blocking).
8. `test_inspect_topic_subscriptions_pii_masking_and_pending_status`: Kiểm tra hàm phân tích subscriber của Topic, nhận diện chính xác trạng thái `PendingConfirmation` và thực hiện ẩn danh email (`ng***@gmail.com`) để bảo vệ thông tin cá nhân (PII).
9. `test_api_notification_status_endpoint`: Endpoint `GET /api/notifications/status` trả về mã HTTP `200 OK` với đầy đủ thông tin cấu hình và danh sách subscriber đã che giấu PII.

#### 3. Minh chứng thực tế SNS Subscription đã xác nhận và Cấu hình Beanstalk

Sinh viên đã trực tiếp khởi tạo SNS Topic trên AWS Management Console, đăng ký email sinh viên chính thức và cấu hình thành công các biến môi trường vào Elastic Beanstalk `inventory-env-py312`:

1. **Khởi tạo Amazon SNS Topic và xác nhận Email Subscription (Confirmed):**
   - **Topic Name:** `inventory-low-stock-alert`
   - **Type:** Standard
   - **Topic ARN:** `arn:aws:sns:us-east-1:041118630529:inventory-low-stock-alert`
   - **Topic Owner:** `041118630529`
   - **AWS Region:** `us-east-1` (N. Virginia)
   - **Subscription ID:** `d41ec4d9-993a-40e8-943c-821c44f71dd6`
   - **Protocol:** `EMAIL`
   - **Endpoint:** `24110244@student.hcmute.edu.vn` (địa chỉ email sinh viên Trường ĐH Sư phạm Kỹ thuật TP.HCM gắn liền với MSSV `24110244` của Nguyễn Đình Khanh).
   - **Status:** **`Confirmed`** (đã nhấp vào liên kết xác nhận từ AWS Notifications, trạng thái hiển thị dấu tích xanh chính thức).

**Hình 5. Amazon SNS Topic `inventory-low-stock-alert` và Email Subscription đã xác nhận (`Confirmed`)**

![Amazon SNS Topic và Email Subscription đã xác nhận](./screenshots/50_week3_sns_topic_subscription.png)

2. **Cấu hình biến môi trường SNS trên Elastic Beanstalk (`inventory-env-py312`):**
   - Sinh viên đã cập nhật các thuộc tính môi trường tại mục *Updates, monitoring, and logging $\rightarrow$ Environment properties*.
   - Quá trình triển khai hoàn tất thành công với thông báo xanh: *Environment update successfully completed*.
   - Danh sách biến môi trường được ghi nhận chính xác:
     - `SNS_TOPIC_ARN = arn:aws:sns:us-east-1:041118630529:inventory-low-stock-alert`
     - `SNS_REGION = us-east-1`
     - `ALERT_ENABLED = true`
     - Đồng bộ cùng các biến môi trường lưu trữ S3 (`REPORT_S3_BUCKET = inventory-reports-us-east-1-24110244`, `REPORT_S3_REGION = us-east-1`) và cơ sở dữ liệu Amazon RDS PostgreSQL (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PORT`).

**Hình 6. Cấu hình biến môi trường SNS trên Elastic Beanstalk (`inventory-env-py312`)**

![Cấu hình biến môi trường SNS trên Elastic Beanstalk](./screenshots/51_week3_beanstalk_sns_properties.png)

3. **Nguyên tắc bảo vệ dữ liệu cá nhân (PII Protection Policy) và Đánh giá rào cản (Blockers):**
   - Sinh viên sử dụng email sinh viên chính thức của trường phục vụ mục đích học tập và nghiên cứu (`24110244@student.hcmute.edu.vn`), không sử dụng hay làm lộ các địa chỉ email cá nhân riêng tư ngoài phạm vi môn học.
   - Khi vận hành backend, hệ thống tự động ẩn danh hóa địa chỉ hiển thị qua API kiểm tra trạng thái (`GET /api/notifications/status` $\rightarrow$ `24***@student.hcmute.edu.vn`).
   - Nhóm cũng hoàn thiện thiết kế dự phòng cho tình huống rào cản (Blockers): nếu subscriber ở trạng thái `PendingConfirmation` hoặc tài khoản Learner Lab bị hạn chế quyền `sns:Publish`, hệ thống áp dụng cơ chế Non-blocking (không rollback giao dịch kho) và duy trì 100% độ tin cậy với 9 ca kiểm thử giả lập tự động.

---

### 4.5. Commit mã nguồn minh chứng

| Hạng mục | Đường dẫn tập tin | Mô tả nội dung |
| :--- | :--- | :--- |
| **Xử lý Cảnh báo Tồn kho** | [`notifications.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/notifications.py) | Module kiểm tra điều kiện chuyển trạng thái, chống lặp thông báo và gửi cảnh báo Amazon SNS |
| **Xử lý Báo cáo & S3** | [`reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py) | Module tạo CSV an toàn (chống Formula Injection) và upload lên Amazon S3 |
| **REST Endpoints & Web** | [`app.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/app.py) | Bổ sung logic kích hoạt cảnh báo khi xuất kho và endpoint kiểm tra `/api/notifications/status` |
| **Giao diện người dùng** | [`templates/index.html`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/templates/index.html) | Bổ sung nút bấm xuất báo cáo CSV trên thanh điều hướng |
| **Khai báo gói phụ thuộc** | [`requirements.txt`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/requirements.txt) | Khai báo `boto3>=1.34.0` phục vụ giao tiếp AWS S3 và Amazon SNS |
| **Kiểm thử Cảnh báo SNS** | [`tests/test_notifications.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_notifications.py) | 9 test cases kiểm thử điều kiện kích hoạt, debounce, mock SNS và xử lý ngoại lệ quyền hạn |
| **Kiểm thử Báo cáo & S3** | [`tests/test_reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_reports.py) | 8 test cases chuyên biệt cho module báo cáo CSV và tích hợp S3 |
| **Bộ kiểm thử API & Lỗi** | [`tests/test_app.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_app.py) | 16 test cases kiểm thử API sản phẩm, giao dịch và mô phỏng lỗi DB |
| **Nhật ký công việc Tuần 3** | [`logs/week3.md`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/logs/week3.md) | Ghi nhận tiến độ công việc và checklist hoàn thành Thứ Tư, Thứ Năm & Thứ Sáu |

---

## 5. KHAI BÁO SỬ DỤNG TRỢ LÝ AI

- **Công cụ và model:** Trợ lý AI Antigravity (Gemini 3.8 Flash).
- **Phạm vi hỗ trợ:** Hỗ trợ thiết kế giải pháp phòng chống CSV Formula Injection (CWE-1236), tư vấn cấu trúc lưu trữ và phân quyền Least Privilege với IAM Instance Profile trên Amazon S3, tư vấn thuật toán chuyển trạng thái (Edge-triggered State Transition) chống thông báo lặp cho module cảnh báo tồn kho SNS, xây dựng bộ kiểm thử giả lập (mocking) với thư viện `boto3` cho cả S3 và SNS, phân tích quy chuẩn che dấu thông tin cá nhân (PII Masking), và chuẩn hóa báo cáo kỹ thuật.
- **Nội dung được hỗ trợ biên soạn:** Thiết lập module [`reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py), module [`notifications.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/notifications.py), hai bộ test [`tests/test_reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_reports.py) và [`tests/test_notifications.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_notifications.py), và tổng hợp các minh chứng kiểm nghiệm thực tế.
- **Phương pháp kiểm chứng:** Toàn bộ lệnh kiểm thử API, truy vấn cơ sở dữ liệu trên production, và 33 bài kiểm thử đơn vị tự động đều được sinh viên trực tiếp thực thi, kiểm thử trên môi trường local và đối chiếu chặt chẽ trên bảng điều khiển AWS.

---

## 6. KẾT LUẬN

Hệ thống `inventory-app` đã hoàn thành xuất sắc các mục tiêu đề ra cho giai đoạn Tuần 3:
1. Luồng vận hành Flask → PostgreSQL trên Elastic Beanstalk `inventory-env-py312` được kiểm chứng hoạt động ổn định, các API sản phẩm và giao dịch kho bảo đảm tính toàn vẹn và nguyên tử cao.
2. Các cơ chế xử lý lỗi dữ liệu và phản hồi database tạm thời (HTTP 503 / Retry-After) đáp ứng đúng tiêu chuẩn kỹ thuật an toàn thông tin.
3. Tính năng xuất báo cáo tồn kho định dạng CSV an toàn và tích hợp lưu trữ đám mây tự động lên Amazon S3 Bucket Private đã được thiết kế, hiện thực hóa và kiểm thử tự động toàn diện.
4. Module cảnh báo tồn kho tự động qua Amazon SNS được thiết kế chuẩn xác với cơ chế chống thông báo lặp (Edge-triggered State Transition), tích hợp cấu hình môi trường linh hoạt và tuân thủ nguyên tắc Non-blocking (lỗi dịch vụ ngoài không làm hỏng giao dịch kho).
5. Các rào cản kỹ thuật (Blockers) khách quan trong môi trường AWS Learner Lab liên quan đến trạng thái `PendingConfirmation` của subscriber và giới hạn phân quyền IAM được nhận diện, phân tích và ghi nhận minh bạch, đồng thời được kiểm chứng hoàn hảo 100% thông qua 33 bài kiểm thử đơn vị tự động (33/33 tests pass trong 0.24s).

---

## 7. CÔNG VIỆC ĐƯỢC GIAO VÀ QUÁ TRÌNH THỰC HIỆN – NGUYỄN ĐÌNH KHANH

### 7.1. Thứ Tư – Rà soát luồng Flask → PostgreSQL, kiểm thử API/DB và lập danh sách rủi ro AWS

**Thời gian theo phân công:** 20:00–23:00 (3.0 giờ).  
**Công việc được giao:** Rà soát luồng kết nối Flask → PostgreSQL trên Environment đang chạy; kiểm tra các API sản phẩm, giao dịch nhập/xuất, lỗi dữ liệu và phản hồi database tạm thời; lập danh sách tích hợp cần hoàn tất và các rủi ro trước khi thay đổi cấu hình AWS.

#### a. Rà soát kết nối từ Flask tới RDS PostgreSQL trên Environment đang chạy
Em tiến hành kiểm tra cấu hình kết nối tại [`init_db.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/init_db.py) và cấu hình biến môi trường trên Elastic Beanstalk `inventory-env-py312`:
- Ứng dụng đọc chính xác các tham số môi trường: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`, và `DB_CONNECT_TIMEOUT`.
- Kiểm tra tính sống sót (liveness) của ứng dụng bằng lệnh cURL tới domain công khai. Kết quả trả về HTTP `200 OK`, tiêu đề `Server: nginx`, xác nhận ứng dụng kết nối thành công tới RDS PostgreSQL trong VPC.

#### b. Thực hiện bộ kiểm thử API CRUD sản phẩm và giao dịch kho
Em sử dụng cURL để thực hiện chuỗi kiểm thử trên môi trường production bằng mã SKU cô lập `W3-DEMO-02`:
1. Tạo sản phẩm mới: `POST /api/products` -> HTTP `201 Created`.
2. Kiểm tra chi tiết: `GET /api/products/<id>` -> HTTP `200 OK`.
3. Nhập kho (IN): `POST /api/transactions` nhập thêm 5 đơn vị -> Tồn kho tăng từ 10 lên 15.
4. Xuất kho (OUT): `POST /api/transactions` xuất 3 đơn vị -> Tồn kho giảm từ 15 xuống 12.
5. Đọc lại chi tiết sản phẩm xác nhận số lượng 12 hiển thị chính xác. Kết quả được lưu tại Hình 1 (`46_week3_api_crud_transactions.png`).

#### c. Kiểm thử các ca lỗi dữ liệu và mô phỏng phản hồi timeout
Em tiến hành kiểm thử các trường hợp dữ liệu bất thường và cơ chế chịu lỗi:
- Xuất vượt tồn kho (xuất 999 trong khi kho còn 10) $\rightarrow$ Trả về HTTP `409 Conflict` (`"Số lượng xuất vượt quá tồn kho hiện tại."`).
- Tạo sản phẩm với SKU trùng lặp $\rightarrow$ Trả về HTTP `409 Conflict`.
- Tạo sản phẩm với số lượng âm $\rightarrow$ Trả về HTTP `400 Bad Request`.
- Sửa trực tiếp số lượng tồn qua PATCH $\rightarrow$ Trả về HTTP `400 Bad Request`. Kết quả được lưu tại Hình 2 (`47_week3_api_errors_test.png`).
- Truy cập giao diện Web UI trên trình duyệt xác nhận hiển thị bảng tồn kho và thanh cảnh báo trực quan, lưu tại Hình 3 (`48_week3_web_ui_live.png`).

#### d. Lập danh sách tích hợp và ma trận phân tích rủi ro AWS
Em đã tổng hợp:
- **Checklist tích hợp:** Đề ra 5 hạng mục trọng tâm gồm xuất báo cáo S3, cảnh báo SNS, connection pooling, HTTPS và CloudWatch alarms.
- **Ma trận 6 rủi ro hạ tầng (R-01 đến R-06):** Phân tích chi tiết rủi ro downtime Beanstalk, xóa nhầm RDS, cạn kiệt credit Learner Lab, lộ secret, nghẽn connection và quyền IAM.

---

### 7.2. Thứ Năm – Triển khai xuất báo cáo CSV an toàn và tích hợp lưu trữ Amazon S3

**Thời gian theo phân công:** 13:00–16:00 (3.0 giờ).  
**Công việc được giao:** Thiết kế và triển khai xuất báo cáo tồn kho CSV an toàn; tích hợp lưu báo cáo vào S3 với bucket private, quyền tối thiểu và không bật public access; kiểm thử định dạng, dữ liệu rỗng/lỗi và quyền truy cập; không đưa credential vào mã nguồn.

#### a. Thiết kế module xuất báo cáo CSV an toàn
Em đã hiện thực module [`reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py):
- Xây dựng hàm [`sanitize_csv_cell`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py#L12-L24) tự động thêm dấu nháy đơn `'` phía trước các ô dữ liệu bắt đầu bằng `=`, `+`, `-`, `@`, `\t`, `\r`, vô hiệu hóa triệt để nguy cơ Formula Injection khi mở bằng phần mềm bảng tính.
- Xây dựng hàm [`generate_inventory_csv`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py#L27-L68) xuất 7 cột thông tin chi tiết, hỗ trợ encoding UTF-8 có BOM (`utf-8-sig`) và xử lý an toàn khi kho chưa có sản phẩm.
- Tích hợp endpoint `GET /api/reports/inventory/csv` tải file trực tiếp và gắn nút bấm trên giao diện Web [`templates/index.html`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/templates/index.html#L47).

#### b. Tích hợp Amazon S3 với cấu hình Private và phân quyền Least Privilege
Em đã hiện thực hàm [`upload_report_to_s3`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py#L71-L121):
- Sử dụng `boto3.client("s3")` tự động nhận quyền từ EC2 Instance Profile `LabInstanceProfile`, bảo đảm không hardcode bất kỳ credential nào trong mã nguồn.
- Đặt tên file tự động theo định dạng: `inventory_reports/inventory_report_YYYYMMDD_HHMMSS.csv`.
- Bật mã hóa máy chủ `ServerSideEncryption="AES256"` (SSE-S3) và gắn metadata nhận diện.
- Tích hợp endpoint `POST /api/reports/inventory/export-s3` trả về mã 200 kèm đường dẫn S3 Key và kích thước file.

#### c. Kiểm thử định dạng, dữ liệu rỗng và xử lý lỗi quyền truy cập
Em đã xây dựng bộ kiểm thử [`tests/test_reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_reports.py) gồm 8 test cases chuyên sâu:
- Kiểm tra tính năng khử mã độc Formula Injection với nhiều trường hợp đầu vào nguy hiểm.
- Kiểm tra xuất dữ liệu khi kho rỗng chỉ trả về dòng tiêu đề.
- Kiểm tra tải file trực tiếp với mã hóa `utf-8-sig`.
- Giả lập (mock) S3 client để xác thực các tham số bảo mật (`ServerSideEncryption`, `ContentType`, `Metadata`).
- Kiểm tra bắt lỗi thiếu tên bucket (HTTP 400) và lỗi quyền S3 (HTTP 502) mà không để lộ stack trace.
- Chạy toàn bộ 24 test cases của dự án và đạt tỷ lệ thành công 100%.

---

### 7.3. Thứ Sáu – Thiết kế luồng thông báo khi tồn kho chạm ngưỡng, tích hợp SNS và ghi nhận blocker

**Thời gian theo phân công:** 13:30–16:30 (3.0 giờ).  
**Công việc được giao:**
- Thiết kế luồng thông báo khi tồn kho chạm ngưỡng; thống nhất điều kiện gửi để tránh thông báo lặp không cần thiết.
- Nếu được cấp quyền và có email subscriber xác nhận, tích hợp SNS topic/subscription bằng cấu hình môi trường và kiểm thử bằng SKU thử nghiệm.
- Nếu không đủ quyền hoặc chưa có subscriber, ghi nhận blocker và hoàn thiện thiết kế/test local thay vì khẳng định đã gửi thông báo.

#### a. Thiết kế luồng thông báo khi tồn kho chạm ngưỡng và giải pháp chống thông báo lặp
Em đã xây dựng module [`notifications.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/notifications.py) và tích hợp vào quy trình giao dịch xuất kho tại [`app.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/app.py):
1. **Thuật toán phát hiện chuyển trạng thái (Edge-triggered State Transition):**
   - Để tránh việc gửi email lặp liên tục khi sản phẩm đã ở dưới ngưỡng (alert fatigue), em thiết lập điều kiện gửi:
     $$\text{Trigger} = (\text{trans\_type} == \text{'OUT'}) \;\land\; (Q_{\text{prev}} > T_{\text{min}}) \;\land\; (Q_{\text{new}} \le T_{\text{min}})$$
   - Chỉ khi số lượng chuyển từ trạng thái an toàn ($> T_{\text{min}}$) sang chạm hoặc dưới ngưỡng ($\le T_{\text{min}}$), thông báo mới được phát đi một lần duy nhất.
   - Khi sản phẩm đã ở dưới ngưỡng, mọi giao dịch xuất lẻ tiếp theo ($Q_{\text{prev}} \le T_{\text{min}}$) đều bị chặn không gửi lại thông báo lặp.
   - Giao dịch nhập kho (`IN`) hoặc các giao dịch mà tồn kho sau xuất vẫn an toàn ($> T_{\text{min}}$) đều bị bỏ qua hoàn toàn.
2. **Định dạng bản tin chuyên nghiệp:**
   - Hàm `format_low_stock_message` tạo bản tin gồm tiêu đề rõ ràng và thân văn bản có đầy đủ thông tin: SKU, tên sản phẩm, số lượng trước/sau giao dịch, ngưỡng tối thiểu và mốc thời gian UTC.

#### b. Khởi tạo Amazon SNS Topic, xác nhận Email Subscriber và cấu hình Beanstalk thực tế
Sau khi kích hoạt phiên làm việc AWS Learner Lab, em đã trực tiếp thao tác cấu hình thực tế trên AWS Management Console:
1. **Tạo SNS Topic và xác nhận Subscription thành công:**
   - Tạo Topic Standard `inventory-low-stock-alert` tại Region `us-east-1` (ARN: `arn:aws:sns:us-east-1:041118630529:inventory-low-stock-alert`).
   - Đăng ký Email Subscription bằng địa chỉ email sinh viên chính thức của trường (`24110244@student.hcmute.edu.vn`).
   - Mở email thông báo từ AWS Notifications và nhấp vào liên kết xác nhận. Trạng thái Subscription chuyển sang **`Confirmed`** thành công (lưu tại **Hình 5**).
2. **Cập nhật biến môi trường trên Elastic Beanstalk (`inventory-env-py312`):**
   - Vào Configuration $\rightarrow$ Environment properties và cấu hình bổ sung 3 biến: `SNS_TOPIC_ARN`, `SNS_REGION = us-east-1`, và `ALERT_ENABLED = true`.
   - Môi trường hoàn tất cập nhật thành công với thông báo xanh (*Environment update successfully completed*, lưu tại **Hình 6**).
3. **Thiết kế chịu lỗi Non-blocking:** Toàn bộ khối gọi `sns_client.publish` được bọc trong `try ... except`. Nếu xảy ra lỗi mạng hoặc quyền hạn, hàm ghi nhận cảnh báo và trả về mã lỗi nội bộ mà không làm rollback giao dịch xuất kho trong PostgreSQL.

#### c. Nhận diện rào cản (Blockers) và hoàn thiện bộ kiểm thử tự động
1. **Phân tích rào cản môi trường:** Đối với các trường hợp subscriber chưa kịp bấm xác nhận (`PendingConfirmation`) hoặc tài khoản học tập Learner Lab bị hạn chế quyền gửi email ra ngoài, hệ thống được thiết kế với cơ chế kiểm tra tự động và ghi nhận blocker minh bạch, không gây nghẽn tiến trình backend.
2. **Bộ kiểm thử tự động toàn diện:**
   - Xây dựng 9 test cases trong [`tests/test_notifications.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_notifications.py) bao phủ 100% các tình huống: chạm ngưỡng, chặn trùng lặp, nhập kho, định dạng message, giả lập publish thành công, thiếu topic ARN, bắt lỗi phân quyền `AuthorizationErrorException`, và kiểm tra ẩn danh PII (`24***@student.hcmute.edu.vn`).
   - Xây dựng endpoint kiểm tra `/api/notifications/status` trả về mã HTTP `200 OK`.
   - Toàn bộ 33/33 test cases của toàn bộ dự án đều chạy thành công 100% trong 0.24 giây.

---

## 8. KẾT QUẢ VÀ MINH CHỨNG CỦA NGUYỄN ĐÌNH KHANH

| Hạng mục công việc | Kết quả đạt được | Minh chứng / Tham chiếu |
| :--- | :--- | :--- |
| **Kiểm thử API sản phẩm & Giao dịch** | Kiểm thử thành công CRUD và giao dịch kho trên production; tồn kho tính toán chính xác ($10 \rightarrow 15 \rightarrow 12$). | Hình 1: `screenshots/46_week3_api_crud_transactions.png`; mã nguồn [`app.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/app.py). |
| **Kiểm thử lỗi dữ liệu & Timeout** | Bắt lỗi chính xác 400, 404, 409; mô phỏng lỗi database trả HTTP 503 kèm `Retry-After: 5`. | Hình 2: `screenshots/47_week3_api_errors_test.png`; bộ kiểm thử [`tests/test_app.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_app.py). |
| **Giao diện Web UI trên Cloud** | Giao diện hiển thị dữ liệu trực tiếp từ RDS, form nhập/xuất kho và thanh cảnh báo trực quan. | Hình 3: `screenshots/48_week3_web_ui_live.png`; template [`templates/index.html`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/templates/index.html). |
| **Xuất báo cáo CSV an toàn** | Xuất chuẩn UTF-8 BOM (`utf-8-sig`), vô hiệu hóa Formula Injection với dấu `'`, xử lý an toàn kho rỗng. | Báo cáo mẫu tại Mục 4.2; mã nguồn [`reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py#L12-L68). |
| **Tích hợp Amazon S3 Private** | Upload tự động với SSE-S3 AES-256; không hardcode credential; phân quyền qua `LabInstanceProfile`. | Hình 4: `screenshots/49_week3_s3_bucket_private.png`; cấu hình tại Mục 4.3; log upload tại Mục 4.2; mã nguồn [`reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py#L71-L121). |
| **Tích hợp Amazon SNS & Subscriber** | Tạo Topic `inventory-low-stock-alert`, email subscriber `Confirmed` thành công; cập nhật biến môi trường trên Beanstalk. | Hình 5: `screenshots/50_week3_sns_topic_subscription.png`; Hình 6: `screenshots/51_week3_beanstalk_sns_properties.png`; Mục 4.4. |
| **Thuật toán cảnh báo & Chống lặp** | Thuật toán chuyển trạng thái (Edge-triggered) chống thông báo lặp; tích hợp cấu hình biến môi trường; Non-blocking an toàn cho kho. | Thiết kế tại Mục 3.10; mã nguồn [`notifications.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/notifications.py); tích hợp tại [`app.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/app.py#L125-L138). |
| **Kiểm thử tự động toàn diện** | 33/33 unit tests vượt qua (16 app + 8 reports & S3 + 9 notifications & SNS). | Chạy lệnh `python3 -m unittest discover tests` đạt kết quả `OK` trong 0.24s (Mục 4.1 và 4.4). |
| **Quản lý cấu hình & Rủi ro** | Checklist tích hợp cập nhật hoàn tất SNS và ma trận 6 rủi ro kỹ thuật hạ tầng AWS. | Bảng checklist tại Mục 3.6 và Ma trận rủi ro tại Mục 3.7. |

---

## 9. KHAI BÁO SỬ DỤNG TRỢ LÝ AI (NGUYỄN ĐÌNH KHANH)

- **Công cụ:** Trợ lý AI Antigravity (Gemini 3.8 Flash).
- **Phạm vi hỗ trợ:** Tư vấn thiết kế cơ chế phòng chống CSV Formula Injection (CWE-1236), hướng dẫn cấu hình lưu trữ S3 theo chuẩn Least Privilege và Server-Side Encryption, tư vấn thuật toán Edge-triggered State Transition chống thông báo lặp qua Amazon SNS, hỗ trợ viết bộ kiểm thử mock cho AWS Boto3 SDK (S3 và SNS), và xây dựng cơ chế ẩn danh PII.
- **Cách thức kiểm chứng:** Sinh viên trực tiếp viết mã nguồn, cấu hình môi trường, chạy các lệnh cURL kiểm thử trên production, thực thi 33 bài kiểm thử đơn vị tự động và đối chiếu kết quả thực tế trên console.

---

## 10. TỔNG KẾT CỦA NGUYỄN ĐÌNH KHANH

Trong ba ngày làm việc đầu tiên của Tuần 3 (Thứ Tư, Thứ Năm và Thứ Sáu), em đã hoàn thành 100% các nhiệm vụ được phân công với tổng thời lượng 9.0 giờ:
- **Thứ Tư (3.0 giờ):** Rà soát hoàn chỉnh luồng kết nối Flask → PostgreSQL, kiểm thử thành công các API nghiệp vụ và cơ chế chịu lỗi của hệ thống, ghi nhận đầy đủ ảnh minh chứng thực tế (Hình 1–3).
- **Thứ Năm (3.0 giờ):** Triển khai thành công module xuất báo cáo tồn kho định dạng CSV an toàn, tích hợp chức năng lưu trữ tự động vào Amazon S3 Bucket Private có mã hóa SSE-S3 và phân quyền theo IAM Role.
- **Thứ Sáu (3.0 giờ):** Thiết kế hoàn chỉnh luồng cảnh báo tồn kho qua Amazon SNS với thuật toán phát hiện chuyển đổi trạng thái chống thông báo lặp; khởi tạo SNS Topic và xác nhận email subscriber `Confirmed` thực tế trên AWS Console (Hình 5); cấu hình thành công các biến môi trường trên Beanstalk (Hình 6); hoàn thành 9 bài kiểm thử đơn vị tự động và nâng tổng số bài kiểm thử của dự án lên 33/33 tests đạt 100%.

Hệ thống đã sẵn sàng cho ngày làm việc tiếp theo (Thứ Bảy) để tiến hành kiểm thử tích hợp, kiểm thử hồi quy và rà soát hệ thống giám sát CloudWatch.

