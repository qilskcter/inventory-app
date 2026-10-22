# BÁO CÁO KỸ THUẬT VÀ KẾT QUẢ TRIỂN KHAI - TUẦN 3
## RÀ SOÁT TÍCH HỢP FLASK - RDS, KIỂM THỬ HỆ THỐNG VÀ TRIỂN KHAI BÁO CÁO S3 PRIVATE

**Dự án:** Hệ thống quản lý kho hàng và cảnh báo tồn kho (`inventory-app`)  
**Môn học:** Điện toán đám mây (Cloud Computing)  
**Sinh viên thực hiện:**
- Nguyễn Đình Khanh (MSSV: `24110244`) - Nhóm trưởng / Backend & Cloud Deployment
- Võ Minh Quân (MSSV: `24110312`) - Thành viên / Database & Infrastructure Setup  
**Giảng viên hướng dẫn:** ThS. Huỳnh Xuân Phụng  
**AWS Region:** `us-east-1` (N. Virginia)

---

> **Phạm vi báo cáo:** Báo cáo ghi nhận kết quả rà soát chi tiết luồng kết nối Flask → Amazon RDS PostgreSQL trên Elastic Beanstalk Environment đang hoạt động (`inventory-env-py312`), kiểm thử toàn diện các endpoint RESTful API sản phẩm và giao dịch kho, kiểm tra cơ chế xử lý lỗi dữ liệu và phản hồi lỗi database tạm thời (HTTP 503 / Retry-After) với ảnh minh chứng thực tế (Hình 1–3). Đồng thời, tài liệu ghi nhận thiết kế và triển khai module xuất báo cáo tồn kho định dạng CSV an toàn (phòng chống CSV Formula Injection, hỗ trợ dữ liệu rỗng) và tích hợp lưu trữ tự động vào Amazon S3 Private Bucket tuân thủ nguyên tắc Least Privilege (không hardcode credential, dùng IAM Role `LabInstanceProfile`, mã hóa SSE-S3 AES-256).

[Nhật ký công việc tuần 3](../../logs/week3.md)

---

## 1. MỤC TIÊU

Trong giai đoạn đầu của Tuần 3, nhóm tập trung rà soát tính ổn định của kiến trúc ứng dụng phân tầng đã triển khai trên AWS ở Tuần 2, đồng thời mở rộng năng lực tích hợp dịch vụ lưu trữ đám mây Amazon S3. Các mục tiêu cụ thể gồm:

1. **Rà soát luồng dữ liệu Flask → PostgreSQL:** Đánh giá chu trình kết nối, thực thi truy vấn và giải phóng tài nguyên giữa ứng dụng Flask (chạy qua WSGI Gunicorn trên AWS Elastic Beanstalk) và cơ sở dữ liệu Amazon RDS PostgreSQL trong mạng nội bộ VPC.
2. **Kiểm tra bộ API sản phẩm và tính toàn vẹn:** Kiểm thử toàn diện các phương thức CRUD (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) trên [`/api/products`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/app.py#L246-L358), xác thực cơ chế lọc dữ liệu, chống injection và bảo vệ toàn vẹn dữ liệu.
3. **Kiểm tra nghiệp vụ giao dịch nhập/xuất kho:** Xác minh tính nguyên tử (atomic transaction) và tính nhất quán dữ liệu của endpoint [`/api/transactions`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/app.py#L383-L396) khi xử lý giao dịch `IN` (nhập) và `OUT` (xuất), ngăn chặn tình trạng xuất âm kho hoặc race condition.
4. **Kiểm tra xử lý lỗi dữ liệu và lỗi database tạm thời:** Đánh giá khả năng bắt lỗi hợp lệ (400 Bad Request, 404 Not Found, 409 Conflict) và phản hồi HTTP `503 Service Unavailable` kèm header `Retry-After: 5` khi database ngắt kết nối hoặc timeout, không làm lộ thông tin nhạy cảm.
5. **Thiết kế và triển khai xuất báo cáo tồn kho CSV an toàn:** Xây dựng module [`reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py) hỗ trợ xuất dữ liệu ra file CSV chuẩn UTF-8 có BOM (`utf-8-sig`) để hiển thị tiếng Việt chính xác trên Microsoft Excel; tích hợp cơ chế phòng chống CSV Formula Injection; xử lý an toàn trường hợp kho hàng chưa có sản phẩm.
6. **Tích hợp lưu trữ báo cáo lên Amazon S3 với Bucket Private:** Kết nối lưu trữ báo cáo tự động lên Amazon S3 qua thư viện `boto3`; áp dụng quyền tối thiểu (Least Privilege) dựa trên IAM Instance Profile `LabInstanceProfile` của EC2; tuyệt đối không đưa credential vào mã nguồn; bật mã hóa Server-Side Encryption (SSE-S3); chặn toàn bộ truy cập công khai (`Block Public Access: Enabled`).
7. **Đánh giá rủi ro hạ tầng AWS:** Lập ma trận nhận diện, phân loại và đề xuất biện pháp giảm thiểu các rủi ro kỹ thuật, rủi ro bảo mật và rủi ro chi phí/hạn mức Learner Lab trước khi điều chỉnh cấu hình AWS.

---

## 2. THIẾT KẾ KIẾN TRÚC VÀ MÔI TRƯỜNG HIỆN HÀNH

Hệ thống `inventory-app` hiện đang hoạt động trên nền tảng AWS tại Region `us-east-1` theo mô hình điện toán đám mây kết hợp dịch vụ lưu trữ đối tượng Amazon S3:

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
|  | - Web App: Flask 3.x (app.py, reports.py)                         |  |
|  | - AWS SDK: Boto3 (IAM Role: LabInstanceProfile / LabRole)          |  |
|  | - Log Streamer: AWS CloudWatch Agent (web.stdout, nginx logs)     |  |
|  +-------------------------------------------------------------------+  |
|               |                                       |                 |
|               | TCP Port 5432                         | HTTPS (API S3)  |
|               | (SSL/TLS Internal VPC)                | (IAM Role Auth) |
|               v                                       v                 |
|  [ Private DB Subnets ] (inventory-db-sg)       +---------------------+ |
|  Amazon RDS PostgreSQL (inventory-db)           | Amazon S3 (Private) | |
|  +---------------------------------------+      | - Bucket: Private   | |
|  | Engine: PostgreSQL 18.3               |      | - Block Public: ON  | |
|  | DB: inventory_db (tables: products,   |      | - Encrypt: SSE-S3   | |
|  |                    transactions)      |      | - Prefix:           | |
|  | Public Access: No                     |      |   inventory_reports/| |
|  +---------------------------------------+      +---------------------+ |
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
- [ ] **2. Tích hợp cảnh báo tự động qua Amazon SNS:**
  - Tạo SNS Topic `inventory-low-stock-alert` và cấu hình email subscription nhận cảnh báo.
  - Xây dựng logic debounce/idempotency trong Flask để tránh gửi thông báo lặp liên tục khi xuất hàng.
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

## 4. KẾT QUẢ VÀ MINH CHỨNG

### 4.1. Bảng tổng hợp kết quả kiểm thử toàn diện (24 Unit Tests)

Toàn bộ 24 ca kiểm thử đơn vị tự động trong [`tests/test_app.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_app.py) và [`tests/test_reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_reports.py) đều vượt qua thành công:

| Nhóm chức năng | Số lượng tests | Nội dung kiểm thử chính | Kết quả |
| :--- | :---: | :--- | :---: |
| **Giao diện Web & Sản phẩm** | 3 | Render HTML bảng tồn kho, thông báo Flash, giao diện khi kho chưa có sản phẩm. | **ĐẠT (OK)** |
| **API Sản phẩm (CRUD)** | 5 | Tạo sản phẩm (default values), chặn số lượng âm, cập nhật PUT/PATCH, xóa DELETE (204). | **ĐẠT (OK)** |
| **Giao dịch Kho (Transactions)** | 3 | Nhập kho (IN), xuất kho nguyên tử (OUT), chặn xuất vượt tồn (409 Conflict). | **ĐẠT (OK)** |
| **Ràng buộc dữ liệu & Toàn vẹn** | 2 | Chặn trùng SKU (409), chặn can thiệp tồn kho trực tiếp qua PATCH (400). | **ĐẠT (OK)** |
| **Khả năng chịu lỗi Database** | 3 | Bắt ngoại lệ `OperationalError` trả HTTP 503 + Retry-After: 5 (cả API và giao diện Web). Kiểm tra cấu hình `DB_CONNECT_TIMEOUT`. | **ĐẠT (OK)** |
| **Xuất báo cáo CSV an toàn** | 3 | Kiểm tra định dạng 7 cột, xác định đúng trạng thái cảnh báo, phòng chống Formula Injection (`=`, `+`, `-`, `@`), xử lý dữ liệu kho rỗng. | **ĐẠT (OK)** |
| **Tải báo cáo qua API** | 1 | Endpoint `GET /api/reports/inventory/csv` trả file đính kèm với UTF-8 BOM (`\xef\xbb\xbf`). | **ĐẠT (OK)** |
| **Tích hợp Amazon S3** | 4 | Upload S3 thành công với SSE-S3 AES-256; kiểm tra báo lỗi khi thiếu tên bucket; endpoint `POST /api/reports/inventory/export-s3` thành công và xử lý ngoại lệ an toàn khi S3 lỗi. | **ĐẠT (OK)** |
| **TỔNG CỘNG** | **24** | **Toàn bộ 24/24 test cases vượt qua trong 0.21 giây** | **100% ĐẠT** |

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

### 4.4. Commit mã nguồn minh chứng

| Hạng mục | Đường dẫn tập tin | Mô tả nội dung |
| :--- | :--- | :--- |
| **Xử lý Báo cáo & S3** | [`reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py) | Module tạo CSV an toàn (chống Formula Injection) và upload lên Amazon S3 |
| **REST Endpoints & Web** | [`app.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/app.py) | Bổ sung endpoint xuất CSV trực tiếp và endpoint xuất đẩy lên S3 |
| **Giao diện người dùng** | [`templates/index.html`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/templates/index.html) | Bổ sung nút bấm xuất báo cáo CSV trên thanh điều hướng |
| **Khai báo gói phụ thuộc** | [`requirements.txt`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/requirements.txt) | Bổ sung `boto3>=1.34.0` phục vụ giao tiếp AWS S3 |
| **Kiểm thử Báo cáo & S3** | [`tests/test_reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_reports.py) | 8 test cases chuyên biệt cho module báo cáo CSV và tích hợp S3 |
| **Bộ kiểm thử API & Lỗi** | [`tests/test_app.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_app.py) | 16 test cases kiểm thử API sản phẩm, giao dịch và mô phỏng lỗi DB |
| **Nhật ký công việc Tuần 3** | [`logs/week3.md`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/logs/week3.md) | Ghi nhận tiến độ công việc và checklist hoàn thành Thứ Tư & Thứ Năm |

---

## 5. KHAI BÁO SỬ DỤNG TRỢ LÝ AI

- **Công cụ và model:** Trợ lý AI Antigravity (Gemini 3.8 Flash).
- **Phạm vi hỗ trợ:** Hỗ trợ thiết kế giải pháp phòng chống CSV Formula Injection (CWE-1236), tư vấn cấu trúc lưu trữ và phân quyền Least Privilege với IAM Instance Profile trên Amazon S3, xây dựng bộ kiểm thử giả lập (mocking) cho thư viện `boto3`, và chuẩn hóa báo cáo kỹ thuật.
- **Nội dung được hỗ trợ biên soạn:** Thiết lập module [`reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py), bộ test [`tests/test_reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_reports.py), và tổng hợp các minh chứng kiểm nghiệm thực tế.
- **Phương pháp kiểm chứng:** Toàn bộ lệnh kiểm thử API, truy vấn cơ sở dữ liệu trên production, và 24 bài kiểm thử đơn vị tự động đều được sinh viên thực thi và kiểm chứng thành công 100% trên môi trường thực tế.

---

## 6. KẾT LUẬN

Hệ thống `inventory-app` đã hoàn thành xuất sắc các mục tiêu đề ra cho giai đoạn đầu Tuần 3:
1. Luồng vận hành Flask → PostgreSQL trên Elastic Beanstalk `inventory-env-py312` được kiểm chứng hoạt động ổn định, các API sản phẩm và giao dịch kho bảo đảm tính toàn vẹn và nguyên tử cao.
2. Các cơ chế xử lý lỗi dữ liệu và phản hồi database tạm thời (HTTP 503 / Retry-After) đáp ứng đúng tiêu chuẩn kỹ thuật an toàn thông tin.
3. Tính năng xuất báo cáo tồn kho định dạng CSV an toàn và tích hợp lưu trữ đám mây tự động lên Amazon S3 Bucket Private đã được thiết kế, hiện thực hóa và kiểm thử tự động toàn diện (24/24 tests pass).
4. Hệ thống tuân thủ chặt chẽ nguyên tắc bảo mật Least Privilege, không để lộ bất kỳ thông tin xác thực nào trong mã nguồn và sẵn sàng cho các bước tích hợp cảnh báo Amazon SNS tiếp theo.

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

**Kết quả Thứ Năm:** Hoàn thành toàn diện module xuất báo cáo CSV an toàn, tích hợp lưu trữ Amazon S3 private theo chuẩn Least Privilege và kiểm thử tự động 100% các trường hợp.

---

## 8. KẾT QUẢ VÀ MINH CHỨNG CỦA NGUYỄN ĐÌNH KHANH

| Hạng mục công việc | Kết quả đạt được | Minh chứng / Tham chiếu |
| :--- | :--- | :--- |
| **Kiểm thử API sản phẩm & Giao dịch** | Kiểm thử thành công CRUD và giao dịch kho trên production; tồn kho tính toán chính xác ($10 \rightarrow 15 \rightarrow 12$). | Hình 1: `screenshots/46_week3_api_crud_transactions.png`; mã nguồn [`app.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/app.py). |
| **Kiểm thử lỗi dữ liệu & Timeout** | Bắt lỗi chính xác 400, 404, 409; mô phỏng lỗi database trả HTTP 503 kèm `Retry-After: 5`. | Hình 2: `screenshots/47_week3_api_errors_test.png`; bộ kiểm thử [`tests/test_app.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/tests/test_app.py). |
| **Giao diện Web UI trên Cloud** | Giao diện hiển thị dữ liệu trực tiếp từ RDS, form nhập/xuất kho và thanh cảnh báo trực quan. | Hình 3: `screenshots/48_week3_web_ui_live.png`; template [`templates/index.html`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/templates/index.html). |
| **Xuất báo cáo CSV an toàn** | Xuất chuẩn UTF-8 BOM (`utf-8-sig`), vô hiệu hóa Formula Injection với dấu `'`, xử lý an toàn kho rỗng. | Báo cáo mẫu tại Mục 4.2; mã nguồn [`reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py#L12-L68). |
| **Tích hợp Amazon S3 Private** | Upload tự động với SSE-S3 AES-256; không hardcode credential; phân quyền qua `LabInstanceProfile`. | Hình 4: `screenshots/49_week3_s3_bucket_private.png`; cấu hình tại Mục 4.3; log upload tại Mục 4.2; mã nguồn [`reports.py`](file:///Users/nguyendinhkhanh/Documents/GitHub/inventory-app/reports.py#L71-L121). |
| **Kiểm thử tự động toàn diện** | 24/24 unit tests vượt qua (16 tests app + 8 tests reports & S3). | Chạy lệnh `python3 -m unittest discover tests` đạt kết quả `OK` trong 0.21s. |
| **Quản lý cấu hình & Rủi ro** | Checklist 5 hạng mục tích hợp và ma trận 6 rủi ro kỹ thuật hạ tầng AWS. | Bảng checklist tại Mục 3.6 và Ma trận rủi ro tại Mục 3.7. |

---

## 9. KHAI BÁO SỬ DỤNG TRỢ LÝ AI (NGUYỄN ĐÌNH KHANH)

- **Công cụ:** Trợ lý AI Antigravity (Gemini 3.8 Flash).
- **Phạm vi hỗ trợ:** Tư vấn thiết kế cơ chế phòng chống CSV Formula Injection (CWE-1236), hướng dẫn cấu hình lưu trữ S3 theo chuẩn Least Privilege và Server-Side Encryption, hỗ trợ viết bộ kiểm thử mock cho AWS Boto3 SDK.
- **Cách thức kiểm chứng:** Sinh viên trực tiếp viết mã nguồn, cấu hình môi trường, chạy các lệnh cURL kiểm thử trên production, thực thi bộ test tự động và đối chiếu kết quả thực tế trên console.

---

## 10. TỔNG KẾT CỦA NGUYỄN ĐÌNH KHANH

Trong hai ngày làm việc đầu tiên của Tuần 3 (Thứ Tư và Thứ Năm), em đã hoàn thành 100% các nhiệm vụ được phân công với tổng thời lượng 6.0 giờ:
- **Thứ Tư (3.0 giờ):** Rà soát hoàn chỉnh luồng kết nối Flask → PostgreSQL, kiểm thử thành công các API nghiệp vụ và cơ chế chịu lỗi của hệ thống, ghi nhận đầy đủ ảnh minh chứng thực tế (Hình 1–3).
- **Thứ Năm (3.0 giờ):** Triển khai thành công module xuất báo cáo tồn kho định dạng CSV an toàn, tích hợp chức năng lưu trữ tự động vào Amazon S3 Bucket Private có mã hóa SSE-S3 và phân quyền theo IAM Role. Toàn bộ 24/24 ca kiểm thử đơn vị tự động đều đạt kết quả tuyệt đối.

Hệ thống đã sẵn sàng cho ngày làm việc tiếp theo (Thứ Sáu) để triển khai tích hợp dịch vụ cảnh báo tự động Amazon SNS khi tồn kho chạm ngưỡng an toàn.
