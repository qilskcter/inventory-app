# BÁO CÁO KỸ THUẬT VÀ KẾT QUẢ TRIỂN KHAI - TUẦN 1

---

## I. TỔNG QUAN ĐỀ TÀI & KIẾN TRÚC HỆ THỐNG

### 1. Thông tin đồ án:
* **Tên đề tài:** Xây dựng hệ thống quản lý nhập/xuất kho, cảnh báo tồn kho thấp và báo cáo định kỳ
* **Môn học:** Cloud Computing (Điện toán đám mây - Đợt 1, 2026 - 2027)
* **Giảng viên hướng dẫn (GVHD):** ThS. Huỳnh Xuân Phụng
* **Nhóm thực hiện (2 sinh viên):**
  * **Nguyễn Đình Khanh** - MSSV: `24110244` (Nhóm trưởng / Phụ trách Backend & Database)
  * **Võ Minh Quân** - MSSV: `24110312` (Thành viên / Phụ trách Network & Infrastructure)

### 2. Mô hình kiến trúc tổng thể (Architecture Overview):
Hệ thống được thiết kế theo mô hình Cloud-Native 2-Tier kết hợp kiến trúc hướng sự kiện (Event-Driven Architecture):
1. **Web Tier:** Ứng dụng Flask Web App chạy trên AWS Elastic Beanstalk (hoặc EC2) đặt trong **Public Subnets**, phục vụ người dùng quản lý sản phẩm và thao tác nhập/xuất kho.
2. **Database Tier:** Cơ sở dữ liệu quan hệ **Amazon RDS PostgreSQL** (Single-AZ, `db.t3.micro`) nằm ẩn trong **Private Subnets**, chỉ cho phép truy cập từ Web Tier thông qua Security Group.
3. **Cảnh báo tồn kho tự động (Alerting):**
   * Cơ chế sự kiện thời gian thực / định kỳ: **Amazon EventBridge** kích hoạt **AWS Lambda function** quét các mặt hàng có số lượng $\le$ `min_threshold`.
   * Gửi cảnh báo: Lambda đẩy thông điệp cảnh báo qua **Amazon SNS Topic**, gửi email trực tiếp tới quản lý kho.
4. **Báo cáo định kỳ (Reporting):** AWS Lambda định kỳ hàng tuần tổng hợp dữ liệu giao dịch thành file **PDF / CSV** và lưu trữ an toàn trong **Amazon S3 Bucket**.
5. **Tự động hóa hạ tầng (IaC):** Toàn bộ tài nguyên (VPC, Subnets, SG, S3, RDS, Lambda, SNS, EventBridge) sẽ được mã hóa và triển khai tự động qua **AWS CloudFormation template**.

---

## II. BÁO CÁO CÔNG VIỆC CHI TIẾT - VÕ MINH QUÂN (MSSV: 24110312)

### 1. Phân tích & Tổng hợp Giới hạn của AWS Learner Lab:
Do dự án được triển khai trên môi trường học tập **AWS Academy Learner Lab**, nhóm đã rà soát nghiêm ngặt các điều kiện biên nhằm đảm bảo tài nguyên hoạt động liên tục mà không vi phạm chính sách lab:

| Tài nguyên / Giới hạn | Ràng buộc của Learner Lab | Giải pháp thiết kế cho dự án |
| :--- | :--- | :--- |
| **Ngân sách (Budget)** | Cấp tối đa **$100 USD** credit. Nếu cạn kiệt, tài khoản bị khoá vĩnh viễn và mất dữ liệu. | Tối ưu kích cỡ máy chủ, tắt/dừng các instance khi không thao tác, kiểm tra chi phí sau mỗi buổi lab. |
| **Vùng (Region)** | Chỉ cho phép `us-east-1` hoặc `us-west-2`. | Cố định 100% tài nguyên tại vùng **`us-east-1` (N. Virginia)**. |
| **IAM Permission** | Không thể tạo User/Role mới; không được sửa Policy. Bắt buộc dùng `LabRole`. | Toàn bộ ứng dụng và Lambda đều tận dụng **`LabRole`** và **`LabInstanceProfile`**. |
| **Quy định Tagging** | Bắt buộc gắn thẻ định danh để kiểm soát tài nguyên. | Mọi tài nguyên khởi tạo đều gắn: `Project=inventory-app`, `Owner=Khanh-Quan`. |
| **Compute (EC2)** | Giới hạn $\le 9$ instance và $\le 32$ vCPU; loại instance từ nano $\rightarrow$ large. | Chỉ sử dụng `t2.micro` hoặc `t3.micro` (1 vCPU, 1 GiB RAM). |
| **Lưu trữ (EBS)** | Tổng dung lượng EBS $\le 100$ GB (gp2 hoặc gp3). | Khởi tạo ổ đĩa hệ thống 20GB - 30GB gp3. |
| **Amazon RDS** | Hỗ trợ `db.t2.micro` / `db.t3.micro`. | Sử dụng RDS PostgreSQL `db.t3.micro` (Single-AZ, 20GB gp2/gp3). |

---

### 2. Thiết kế Hạ tầng Mạng & Bảo mật (Network & Security Design):

#### A. Sơ đồ phân vùng VPC và Subnets:
* **VPC Name:** `inventory-vpc`
* **CIDR Block:** `10.0.0.0/16`
* **Multi-AZ Configuration:** Phân bổ đều trên 2 Availability Zones (`us-east-1a` và `us-east-1b`) nhằm thỏa mãn yêu cầu DB Subnet Group của RDS:
  * `inventory-public-subnet-1`: `10.0.1.0/24` (AZ: `us-east-1a`) $\rightarrow$ Dành cho Web Tier (Public)
  * `inventory-public-subnet-2`: `10.0.2.0/24` (AZ: `us-east-1b`) $\rightarrow$ Dành cho Web Tier (Public)
  * `inventory-private-subnet-1`: `10.0.11.0/24` (AZ: `us-east-1a`) $\rightarrow$ Dành cho Database Tier (Private)
  * `inventory-private-subnet-2`: `10.0.12.0/24` (AZ: `us-east-1b`) $\rightarrow$ Dành cho Database Tier (Private)

#### B. Định tuyến (Route Tables) & Gateways:
* **Internet Gateway (IGW):** `inventory-igw` được đính kèm trực tiếp vào `inventory-vpc`.
* **Public Route Table (`inventory-public-rt`):**
  * Route: `0.0.0.0/0` trỏ tới `inventory-igw`.
  * Liên kết Subnet: Gắn với `inventory-public-subnet-1` và `inventory-public-subnet-2`.
* **Private Route Table (`inventory-private-rt`):**
  * Route: Chỉ chứa route nội bộ `10.0.0.0/16 local`, không có đường dẫn trực tiếp ra ngoài Internet nhằm bảo vệ an toàn cho RDS PostgreSQL.
  * Liên kết Subnet: Gắn với `inventory-private-subnet-1` và `inventory-private-subnet-2`.

#### C. Chiến lược kiểm soát truy cập (Security Groups 2-Tier):
1. **`inventory-web-sg` (Web Application Security Group):**
   * **Inbound:**
     * Port `80` (HTTP) từ `0.0.0.0/0` (Truy cập Web cho người dùng)
     * Port `5000` (Custom TCP) từ `0.0.0.0/0` (Kiểm thử Flask dev server)
   * **Outbound:** All Traffic (hoặc TCP port 5432 đến DB SG)
2. **`inventory-db-sg` (Database Security Group):**
   * **Inbound:**
     * Port `5432` (PostgreSQL) chỉ chấp nhận nguồn là Security Group ID của `inventory-web-sg` (`source: sg-xxxxxx`). Tuyệt đối không mở IP public hoặc `0.0.0.0/0`.
   * **Outbound:** Mặc định.

---

## III. BÁO CÁO CÔNG VIỆC CHI TIẾT - NGUYỄN ĐÌNH KHANH (MSSV: 24110244)

### 1. Thiết kế Cơ sở dữ liệu quan hệ (PostgreSQL Database Schema):
Cơ sở dữ liệu gồm 2 bảng nghiệp vụ cốt lõi:
1. **Bảng `products`:** Quản lý thông tin và số lượng mặt hàng
   * `id`: SERIAL PRIMARY KEY
   * `sku`: VARCHAR(50) UNIQUE NOT NULL (Mã sản phẩm)
   * `name`: VARCHAR(100) NOT NULL (Tên sản phẩm)
   * `quantity`: INT NOT NULL DEFAULT 0 (Số lượng tồn thực tế)
   * `min_threshold`: INT NOT NULL DEFAULT 5 (Định mức tồn tối thiểu để kích hoạt cảnh báo)
2. **Bảng `transactions`:** Lưu trữ toàn bộ lịch sử xuất/nhập kho
   * `id`: SERIAL PRIMARY KEY
   * `product_id`: INT REFERENCES products(id) (Khóa ngoại)
   * `type`: VARCHAR(10) NOT NULL ('IN' - Nhập kho, 'OUT' - Xuất kho)
   * `quantity`: INT NOT NULL (Số lượng giao dịch)
   * `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP (Thời gian thực hiện)

### 2. Xây dựng Ứng dụng Backend & Giao diện Local:
* Khởi tạo ứng dụng Flask (`app.py`), kết nối PostgreSQL qua thư viện `psycopg2-binary`.
* Cài đặt các API xử lý:
  * Xem danh sách hàng tồn (`/`).
  * Thêm mới mặt hàng với mức cảnh báo tối thiểu (`/add`).
  * Thực hiện giao dịch nhập/xuất kho (`/transaction`), có cơ chế ngăn chặn việc xuất hàng vượt quá số lượng tồn hiện có (`current_qty < trans_qty`).
  * Tự động hiển thị Flash Warning khi `quantity <= min_threshold`.

### 3. Khởi tạo Amazon S3 Bucket lưu trữ báo cáo:
* Tạo thành công S3 Bucket: `inventory-reports-us-east-1-24110244` tại vùng `us-east-1`.
* Cấu hình chế độ Private (Block all public access).
* Gán Tagging đầy đủ: `Project=inventory-app`, `Owner=Khanh-Quan`.

---

## IV. BẢNG TỔNG HỢP MINH CHỨNG & TIÊU CHÍ ĐÁNH GIÁ TUẦN 1

| Tiêu chí yêu cầu của GVHD | Hiện trạng triển khai của nhóm | Minh chứng kiểm tra |
| :--- | :--- | :--- |
| **Kế hoạch thời gian** | Đạt **28.0 giờ** toàn nhóm (Khanh: 14.0h, Quân: 14.0h $\ge 8$h/SV). | Chi tiết tại [logs/week1.md](file:///c:/Users/ASUS/Downloads/AWSS/inventory-app/logs/week1.md). |
| **Môi trường & Vùng** | Triển khai trên AWS Learner Lab tại vùng `us-east-1`. | Console / AWS CLI output Region `us-east-1`. |
| **Quyền IAM** | Sử dụng `LabRole` & `LabInstanceProfile`. | Không tạo mới bất kỳ IAM Role/User nào. |
| **Quy chuẩn Tagging** | 100% tài nguyên có `Project=inventory-app`, `Owner=Khanh-Quan`. | Thể hiện trên VPC, Subnet, SG, S3 Bucket. |
| **Minh chứng mã nguồn** | Toàn bộ mã nguồn, SQL script, tài liệu trên GitHub. | GitHub Repo: `qilskcter/inventory-app`. |
| **Báo cáo sử dụng AI** | Ghi rõ phạm vi hỗ trợ của ChatGPT, Claude, Amazon Q, Antigravity. | Trình bày tại Mục IV trong Worklog Tuần 1. |