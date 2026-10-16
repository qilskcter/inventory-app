# NHẬT KÝ CÔNG VIỆC (WORKLOG) - TUẦN 2

---

## I. THÔNG TIN CHUNG
* **Tên dự án:** Hệ thống quản lý kho hàng (inventory) với cảnh báo tồn kho
* **Phân nhóm môn học:** Domain Apps - Đợt 1 (2026 - 2027)
* **Giảng viên hướng dẫn (GVHD):** ThS. Huỳnh Xuân Phụng
* **Thành viên nhóm (Tối đa 2 SV):**
  1. **Nguyễn Đình Khanh** - MSSV: `24110244` (Nhóm trưởng / Backend & Cloud Deployment)
  2. **Võ Minh Quân** - MSSV: `24110312` (Thành viên / Database & Infrastructure Setup)

---

## II. MỤC TIÊU TUẦN 2: TRIỂN KHAI CÁC CHỨC NĂNG LÕI TRÊN AWS & KIỂM THỬ TỪNG THÀNH PHẦN
Theo lộ trình đồ án, mục tiêu cốt lõi của Tuần 2 là **"Triển khai các chức năng lõi trên AWS, kiểm thử từng thành phần"**:
1. **Triển khai các chức năng lõi lên AWS:**
   * **Tầng Cơ sở dữ liệu (Database Tier):** Đưa CSDL PostgreSQL lên **Amazon RDS** (`inventory-db`, class `db.t3.micro` trong Private Subnet), khởi tạo cấu trúc bảng `products` và `transactions`.
   * **Tầng Ứng dụng (Application Tier):** Đóng gói và triển khai mã nguồn Backend Flask lên **AWS Elastic Beanstalk** (hoặc EC2) trong Public Subnet.
   * **Chức năng nghiệp vụ lõi (Core Business Logic):** Đảm bảo toàn bộ nghiệp vụ Quản lý sản phẩm (CRUD), Giao dịch Nhập/Xuất kho (Inbound/Outbound) và logic Kiểm tra tồn kho an toàn hoạt động trực tiếp trên AWS Cloud.
2. **Kiểm thử chi tiết từng thành phần (Component & Integration Testing):**
   * **Kiểm thử thành phần Database:** Kiểm tra khả năng kết nối cổng 5432, nạp schema DDL và cô lập bảo mật mạng (chặn Internet, chỉ cho phép Web SG kết nối).
   * **Kiểm thử thành phần Web Server:** Kiểm tra Health Check Beanstalk (`Ok/Green`), cấu hình biến môi trường và log dịch vụ.
   * **Kiểm thử thành phần API:** Kiểm thử độc lập từng RESTful API Endpoint (`GET/POST /api/products`, `POST /api/transactions`) với các mã trạng thái HTTP (`200`, `201`, `400`, `404`, `409`).
   * **Kiểm thử thành phần Giao diện (Frontend UI):** Thao tác end-to-end trên trình duyệt qua URL công khai của AWS Beanstalk.
   * **Kiểm thử thành phần Giám sát:** Kiểm tra thu thập log và metrics qua **AWS CloudWatch**.

---

## III. BẢNG PHÂN CÔNG CÔNG VIỆC VÀ THỜI GIAN CHI TIẾT (TỪ THỨ TƯ ĐẾN CHỦ NHẬT)

### 1. Phân công cho Sinh viên 1: Nguyễn Đình Khanh (MSSV: 24110244)

| Ngày | Thời gian | Nội dung công việc chi tiết | Công cụ / AI hỗ trợ | Số giờ | Kết quả / Minh chứng đạt được |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **Thứ Tư** | 20:00 - 23:00 | • Chuẩn bị mã nguồn Flask để triển khai Production (chuẩn hóa `app.py`, cấu hình Gunicorn, `Procfile`, `.ebextensions`).<br>• Cấu hình mã nguồn đọc thông số kết nối CSDL từ Environment Variables (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`). | AI hỗ trợ (Antigravity / ChatGPT) gợi ý cấu trúc file cấu hình Elastic Beanstalk `.ebextensions` | 3.0h | Mã nguồn sẵn sàng đóng gói deploy, hỗ trợ linh hoạt giữa local và AWS Cloud. |
| **Thứ Năm** | 13:00 - 16:00 | • Tìm hiểu và thiết lập môi trường AWS Elastic Beanstalk (Application & Environment) trong `inventory-vpc`.<br>• Cấu hình gắn `LabInstanceProfile` và Security Group `inventory-web-sg` cho EC2 instance do Beanstalk quản lý. | AWS Console & EB CLI | 3.0h | Tạo thành công Beanstalk Environment (`inventory-env`) chạy nền tảng Python 3.x. |
| **Thứ Sáu** | 13:30 - 16:30 | • Đóng gói ứng dụng dạng ZIP và deploy lên Elastic Beanstalk.<br>• Cấu hình Environment Properties trên Beanstalk Console trỏ tới RDS Endpoint do SV2 cung cấp.<br>• Xử lý các lỗi khởi động ban đầu (502 Bad Gateway / WSGI config nếu có). | AI hỗ trợ phân tích file `web.stdout.log` và hướng dẫn fix lỗi cổng kết nối | 3.0h | Ứng dụng Flask hiển thị trạng thái Health: **Ok (Green)** trên AWS Beanstalk Console. |
| **Thứ Bảy** | 09:00 - 11:30 | • Kiểm thử toàn bộ API Endpoints (`/api/products`, `/api/transactions`) trên domain công khai Beanstalk bằng cURL/Postman.<br>• Kiểm thử thao tác trên Web UI: tạo sản phẩm mới, thực hiện giao dịch Inbound/Outbound và kiểm tra biến động tồn kho tức thời. | Postman & Web Browser | 2.5h | Toàn bộ chức năng quản lý kho chạy mượt mà trên môi trường AWS thực tế. |
| **Chủ Nhật** | 14:00 - 16:30 | • Cấu hình xem CloudWatch Logs (nhật ký truy cập và lỗi của Beanstalk).<br>• Kiểm tra và tối ưu hóa code xử lý ngoại lệ database connection timeout.<br>• Tổng hợp minh chứng, cập nhật `documents/week2.md` và push code lên GitHub. | Git, AWS CloudWatch Console | 2.5h | • Commit Git hoàn chỉnh.<br>• Nhật ký công việc và tài liệu kiểm thử Tuần 2 hoàn thiện. |

* **Tổng số giờ làm việc của Nguyễn Đình Khanh:** **14.0 giờ** (Đạt yêu cầu $\ge 8$ giờ/tuần)

---

### 2. Phân công cho Sinh viên 2: Võ Minh Quân (MSSV: 24110312)

| Ngày | Thời gian | Nội dung công việc chi tiết | Công cụ / AI hỗ trợ | Số giờ | Kết quả / Minh chứng đạt được |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **Thứ Tư** | 20:00 - 23:00 | • Khởi tạo DB Subnet Group (`inventory-db-subnet-group`) kết hợp 2 Private Subnets (`private-db-subnet-1`, `private-db-subnet-2`) trên 2 AZs (`us-east-1a`, `us-east-1b`).<br>• Kiểm tra lại routing table và quy tắc bảo mật của `inventory-db-sg`. | AWS Console (RDS & VPC) | 3.0h | DB Subnet Group được tạo thành công, sẵn sàng cung cấp hạ tầng mạng cho RDS. |
| **Thứ Năm** | 13:30 - 16:30 | • Khởi tạo Amazon RDS PostgreSQL instance (`inventory-db`): version 15/16, instance class `db.t3.micro`, 20GB gp3, Public Accessible: No.<br>• Gán `inventory-db-sg` và đính kèm Tag chuẩn: `Project=inventory-app`, `Owner=Khanh-Quan`. | AWS Console / AWS CLI | 3.0h | Database RDS PostgreSQL được tạo thành công ở trạng thái `Available`. |
| **Thứ Sáu** | 08:30 - 11:30 | • Khởi tạo dữ liệu ban đầu cho RDS: Chạy script `init_db.py` (hoặc EC2 Jumpbox/Bastion/Session Manager) để thực thi `schema.sql` tạo 2 bảng `products` và `transactions`.<br>• Cung cấp Endpoint, Port, Database Name cho SV1 cấu hình vào ứng dụng Web. | Python, `psycopg2` / AWS CLI | 3.0h | Cấu trúc CSDL và dữ liệu mẫu đã sẵn sàng trong RDS PostgreSQL trên AWS. |
| **Thứ Bảy** | 14:00 - 16:30 | • Kiểm tra xác thực tính cô lập an toàn mạng của RDS (chặn 100% kết nối từ ngoài Internet, chỉ chấp nhận kết nối từ `inventory-web-sg`).<br>• Theo dõi mức tiêu thụ tài nguyên RDS qua AWS CloudWatch Metrics (CPU Utilization, Free Storage Space, DB Connections). | AWS RDS Console, CloudWatch | 2.5h | Xác nhận kết nối DB an toàn theo mô hình Security Group Chaining, không bị lộ lọt. |
| **Chủ Nhật** | 09:00 - 11:30 | • Chụp toàn bộ ảnh chụp minh chứng có Account ID (`041118630529`) & Region `us-east-1`.<br>• Thực hiện quy trình tạm dừng RDS (`Stop DB Instance`) để bảo toàn AWS Credit khi không có tiết học.<br>• Hoàn thành phần báo cáo hạ tầng trong báo cáo đồ án Tuần 2. | AWS CLI & AWS Console | 2.5h | • 100% ảnh minh chứng RDS và VPC được lưu trữ.<br>• Báo cáo quản lý chi phí AWS đạt chuẩn. |

* **Tổng số giờ làm việc của Võ Minh Quân:** **14.0 giờ** (Đạt yêu cầu $\ge 8$ giờ/tuần)

---

## IV. DANH SÁCH CÔNG VIỆC CẦN LÀM CHI TIẾT (TASK CHECKLIST)

### Giai đoạn 1: Triển khai CSDL Amazon RDS PostgreSQL (Võ Minh Quân chủ trì)
- [x] **Tạo DB Subnet Group:**
  - Tên: `inventory-db-subnet-group`
  - VPC: `inventory-vpc`
  - Subnets: Chọn 2 Private Subnets ở 2 AZs khác nhau (`private-db-subnet-1`, `private-db-subnet-2`).
- [x] **Khởi tạo RDS Instance:** Amazon RDS PostgreSQL `inventory-db` đã được tạo; thông số kết nối được tổng hợp trong [báo cáo tuần 2](../documents/week_2/week2.md). Không ghi mật khẩu vào nhật ký.
- [x] **Nạp schema:** Thực thi `database/schema.sql` và truy vấn xác nhận hai bảng `products`, `transactions` trên `inventory_db` (ảnh `19_rds_tables_created.png`).
- [ ] **Nạp dữ liệu mẫu bằng script/seed:** Schema chỉ tạo bảng và index; sản phẩm kiểm thử được thêm qua ứng dụng Web, không phải seed data.

---

### Giai đoạn 2: Chuẩn bị & Đóng gói Ứng dụng Flask (Nguyễn Đình Khanh chủ trì)
- [x] **Cấu hình biến môi trường cho ứng dụng:**
  - Đảm bảo app đọc các biến:
    - `DB_HOST`: Endpoint của RDS
    - `DB_PORT`: `5432`
    - `DB_NAME`: `inventory_db`
    - `DB_USER`: `postgres`
    - `DB_PASSWORD`: Mật khẩu CSDL
  - Giữ fallback về localhost khi chạy local để thuận tiện dev.
- [x] **Tạo file cấu hình Elastic Beanstalk:**
  - `Procfile` (nếu dùng Beanstalk Amazon Linux 2023 / AL2):
    ```text
    web: gunicorn --bind 0.0.0.0:8000 app:app
    ```
  - Hoặc tạo alias entrypoint `application.py` trỏ tới `app` của `app.py`.
  - Cập nhật `requirements.txt` đảm bảo có `gunicorn`, `psycopg2-binary`, `Flask`.
- [x] **Tạo gói triển khai (Deployment ZIP):**
  - Nén toàn bộ mã nguồn (`app.py`, `database/`, `templates/`, `requirements.txt`, `Procfile`, v.v.) ngoại trừ `venv/`, `.git/`, `__pycache__/`.

---

### Giai đoạn 3: Triển khai Ứng dụng lên Elastic Beanstalk (Nguyễn Đình Khanh chủ trì)
- [x] **Khởi tạo Elastic Beanstalk Application & Environment:**
  - Tên ứng dụng: `inventory-app`
  - Tên môi trường đang chạy ứng dụng: `inventory-env-py312`
  - Platform: Python 3.12 trên Amazon Linux 2023
  - Application code: Upload gói ZIP đã chuẩn bị.
- [x] **Cấu hình Hạ tầng & Quyền hạn (Configuration Presets):**
  - **Service Role:** Dùng `LabRole` (bắt buộc trong Learner Lab).
  - **EC2 Instance Profile:** Chọn `LabInstanceProfile`.
  - **Network / VPC:** Chọn `inventory-vpc`.
    - Instance Subnet: Chọn `public-subnet-1` (hoặc cả `public-subnet-2`).
    - Gán Public IP cho instance: **Yes / Enabled**.
  - **Security Group:** Gán `inventory-web-sg`.
  - **Instance Type:** `t2.micro` hoặc `t3.micro`.
  - **Environment Type:** Single Instance (không tạo Load Balancer để tiết kiệm chi phí).
- [x] **Cấu hình Environment Properties (Biến môi trường):**
  - Thiết lập các key: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
  - Bấm Deploy và theo dõi quá trình build/launch instance.

---

### Giai đoạn 4: Kiểm thử End-to-End & Tích hợp (Cả hai thành viên)
- [x] **Kiểm tra trạng thái sức khỏe (Health Check):**
  - Trạng thái Beanstalk hiển thị màu Xanh lá (`Ok`).
- [x] **Kiểm thử Web Interface:**
  - URL Beanstalk: `http://inventory-env-py312.eba-vbehyxmh.us-east-1.elasticbeanstalk.com`
  - Kiểm tra load trang chủ `index.html`, danh sách sản phẩm hiển thị đầy đủ.
- [x] **Kiểm thử lưu sản phẩm và giao dịch tồn kho đã xác nhận:**
  - Thêm 1 sản phẩm mới qua Web UI.
  - Thực hiện giao dịch Nhập kho (Inbound) $\rightarrow$ số lượng tăng.
  - Thực hiện giao dịch Xuất kho (Outbound) $\rightarrow$ số lượng giảm.
  - Kiểm tra xuất kho vượt số lượng và ngưỡng cảnh báo tối thiểu chưa có minh chứng trong ảnh hiện lưu.
- [x] **Kiểm thử trực tiếp API ở mức GET:**
  - `GET /api/products` trả HTTP `200` và JSON sản phẩm; các mã `201`, `400`, `404`, `409` chưa được xác minh trong bộ minh chứng hiện có.

---

### Giai đoạn 5: Giám sát, Quản lý Chi phí & Minh chứng (Cả hai thành viên)
- [ ] **Kiểm tra CloudWatch Logs:**
  - Xem access log và error log của ứng dụng trực tiếp trên AWS CloudWatch.
- [ ] **Chụp ảnh minh chứng Tuần 2:**
  - Đảm bảo rõ Account ID (`041118630529`) và Region `us-east-1`.
  - Đầy đủ Tags `Project=inventory-app`, `Owner=Khanh-Quan`.
- [ ] **Dừng RDS Instance khi không sử dụng (Cost Optimization):**
  - Chọn RDS Instance $\rightarrow$ Actions $\rightarrow$ **Stop temporarily**.

---

## V. HƯỚNG DẪN THỰC HIỆN TỪNG BƯỚC (QUICK COMMANDS)

### 1. Lệnh tạo gói ZIP deploy Elastic Beanstalk
```bash
zip -r inventory-deployment.zip app.py init_db.py database/ templates/ requirements.txt Procfile -x "*.pyc" "__pycache__/*"
```

### 2. Kiểm tra thông số kết nối RDS từ máy trung gian trong VPC
```bash
# Kiểm tra port 5432 mở tới RDS
nc -zv <RDS_ENDPOINT> 5432

# Kiểm tra truy vấn CSDL
PGPASSWORD='<YOUR_PASSWORD>' psql -h <RDS_ENDPOINT> -U postgres -d inventory_db -c "SELECT * FROM products;"
```

### 3. Kiểm thử API qua cURL
```bash
# Liệt kê sản phẩm
curl -X GET http://<BEANSTALK_URL>/api/products

# Thêm sản phẩm
curl -X POST http://<BEANSTALK_URL>/api/products \
  -H "Content-Type: application/json" \
  -d '{"sku": "SKU-CLOUD-01", "name": "Bàn phím cơ Cloud", "min_threshold": 5}'

# Giao dịch nhập kho
curl -X POST http://<BEANSTALK_URL>/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "type": "IN", "quantity": 20}'
```

---

## VI. DANH SÁCH ẢNH MINH CHỨNG CẦN THU THẬP (TUẦN 2 SCREENSHOTS)

| Mã ảnh | Tên file hiện có | Nội dung minh chứng | Sinh viên thực hiện |
| :---: | :--- | :--- | :---: |
| 1 | `11_rds_subnet_group.png` | DB Subnet Group gắn với hai private subnets trên hai AZs | Võ Minh Quân |
| 2 | `12_private_route_tables.png` | Route Tables của các private subnets | Võ Minh Quân |
| 3 | `13_inventory_db_sg.png` | Security Group của RDS | Võ Minh Quân |
| 4 | `14_beanstalk_environment_health.png` | Environment Beanstalk ban đầu dùng Sample application | Nguyễn Đình Khanh |
| 5 | `16_beanstalk_networking.png` | Cấu hình mạng Beanstalk trong `inventory-vpc` | Nguyễn Đình Khanh |
| 6 | `17_beanstalk_ec2_instance.png` | EC2 instance do Beanstalk quản lý | Nguyễn Đình Khanh |
| 7 | `18_beanstalk_ec2_security.png` | IAM role, Security Groups và inbound rules của EC2 | Nguyễn Đình Khanh |
| 8 | `19_rds_tables_created.png` | Thực thi schema và xác minh hai bảng trên RDS | Võ Minh Quân |
| 9 | `20_beanstalk_env_py312_green.png` | Environment `inventory-env-py312` đạt Health `Ok` | Nguyễn Đình Khanh |
| 10 | `21_inventory_web_rds_integration.png` | Giao diện Web hiển thị sản phẩm đã lưu | Nguyễn Đình Khanh |
| 11 | `22_api_products_test.png` | `GET /api/products` trả HTTP `200` và JSON | Nguyễn Đình Khanh |

*Lưu ý: Ảnh 21–22 là ảnh ứng dụng/API, không phải AWS Console. Chưa có ảnh minh chứng CloudWatch Logs/Metrics hoặc thao tác dừng RDS trong thư mục hiện tại.*

---

## VII. BÁO CÁO SỬ DỤNG TRỢ LÝ AI (AI ASSISTANCE REPORT)
Nhóm tiếp tục duy trì việc sử dụng có trách nhiệm các công cụ AI (**Antigravity**, **ChatGPT**, **Claude**) trong Tuần 2:
* **Hỗ trợ cấu hình hạ tầng:** Hướng dẫn cấu trúc file `.ebextensions` và `Procfile` của Elastic Beanstalk trên nền Amazon Linux 2023.
* **Xử lý sự cố (Troubleshooting):** Hỗ trợ gỡ lỗi kết nối mạng giữa Beanstalk và RDS qua Security Groups, phân tích log lỗi Gunicorn.
* **Tối ưu hóa mã nguồn:** Viết script tự động nén mã nguồn và tự động hóa kiểm thử API bằng cURL.

---

## VIII. TUÂN THỦ QUY ĐỊNH AWS LEARNER LAB
* **Region:** Cố định 100% tài nguyên tại `us-east-1` (N. Virginia).
* **IAM Role & Instance Profile:** Sử dụng `LabRole` cho Elastic Beanstalk Service Role và `LabInstanceProfile` cho EC2 Instances. Tuyệt đối không tạo IAM User/Role mới.
* **Tagging bắt buộc:** 100% tài nguyên (RDS, DB Subnet Group, Beanstalk App/Env) đều đính kèm:
  * `Project`: `inventory-app`
  * `Owner`: `Khanh-Quan`
* **Chiến lược tiết kiệm Credit (Budget Control):**
  * Chỉ dùng Single Instance cho Beanstalk (không bật Load Balancer tốn phí).
  * Cấu hình RDS Single-AZ, instance `db.t3.micro`.
  * **Tạm dừng RDS Database** khi hết phiên làm việc.

---

## IX. ĐÁNH GIÁ MỤC TIÊU VÀ KẾ HOẠCH TUẦN 3
* **Kỳ vọng hoàn thành Tuần 2:** Hệ thống hoạt động 100% trên AWS Cloud với kiến trúc 2-Tier hoàn chỉnh (Web Beanstalk $\leftrightarrow$ RDS PostgreSQL).
* **Kế hoạch định hướng Tuần 3:**
  * **Tích hợp Lưu trữ & Báo cáo S3:** Viết hàm xuất báo cáo tồn kho định kỳ và tải trực tiếp lên S3 Bucket `inventory-reports-us-east-1-24110244`.
  * **Tích hợp Cảnh báo Tồn kho Tự động:** Kết nối **AWS SNS** để gửi thông báo SMS/Email ngay khi số lượng hàng trong kho $\le$ `min_threshold`.
  * **Tự động hóa với AWS Lambda & EventBridge:** Thiết lập Cron schedule kích hoạt hàm Lambda tự động kiểm tra tồn kho hàng ngày.
