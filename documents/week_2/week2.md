# BÁO CÁO KỸ THUẬT VÀ KẾT QUẢ TRIỂN KHAI - TUẦN 2
## CHUẨN BỊ HẠ TẦNG MẠNG VÀ MÔI TRƯỜNG ỨNG DỤNG

**Dự án:** Hệ thống quản lý kho hàng và cảnh báo tồn kho (`inventory-app`)  
**Môn học:** Điện toán đám mây (Cloud Computing)  
**Sinh viên thực hiện:**
- Nguyễn Đình Khanh (MSSV: 24110244)
- Võ Minh Quân (MSSV: 24110312)  
**Giảng viên hướng dẫn:** ThS. Huỳnh Xuân Phụng  
**AWS Region:** `us-east-1` (N. Virginia)

---

> **Phạm vi báo cáo:** Báo cáo ghi nhận việc chuẩn bị mạng và khởi tạo schema trên Amazon RDS, triển khai ứng dụng Flask lên AWS Elastic Beanstalk, cấu hình kết nối giữa tầng Web và Database, và kiểm thử Web/API. Kết quả được trình bày theo các ảnh minh chứng có trong thư mục `screenshots`.

[Nhật ký công việc tuần 2](../../logs/week2.md)

---

## 1. MỤC TIÊU

Tuần 2, nhóm chuẩn bị hạ tầng mạng cho tầng cơ sở dữ liệu và thiết lập môi trường chạy ứng dụng. Các mục tiêu cụ thể gồm:

1. Tạo DB Subnet Group `inventory-db-subnet-group` trong VPC dự án, kết hợp hai private subnets ở hai Availability Zones.
2. Rà soát Route Tables đang áp dụng cho các private subnets.
3. Rà soát quy tắc bảo mật của `inventory-db-sg` để kiểm soát nguồn được phép kết nối tới Database.
4. Tìm hiểu và thiết lập Elastic Beanstalk Application và Environment cho ứng dụng trong VPC `inventory-vpc`.
5. Cấu hình `LabInstanceProfile` và Security Group `inventory-web-sg` cho EC2 instance do Elastic Beanstalk quản lý.
6. Triển khai ứng dụng Flask lên Elastic Beanstalk và kiểm tra kết nối tới RDS qua giao diện Web và REST API.

---

## 2. THIẾT KẾ MẠNG

Các tài nguyên mạng thuộc VPC `inventory-vpc` (`10.0.0.0/16`). DB Subnet Group sử dụng hai private subnets sau:

| Private Subnet | CIDR Block | Availability Zone | Vai trò |
| :--- | :---: | :---: | :--- |
| `private-db-subnet-1` | `10.0.11.0/24` | `us-east-1a` | Subnet riêng thứ nhất dành cho lựa chọn mạng của RDS. |
| `private-db-subnet-2` | `10.0.12.0/24` | `us-east-1b` | Subnet riêng thứ hai, thuộc Availability Zone khác. |

DB Subnet Group tập hợp các subnet mà Amazon RDS có thể sử dụng khi cấu hình DB instance trong VPC. Việc có subnet ở hai Availability Zones đáp ứng yêu cầu phân bố subnet của nhóm; điều đó không tự tạo DB instance dự phòng và không đồng nghĩa đã bật Multi-AZ.

---

## 3. CÔNG VIỆC ĐÃ THỰC HIỆN

### 3.1. Khởi tạo DB Subnet Group

Nhóm đã tạo DB Subnet Group với thông tin sau:

| Thuộc tính | Kết quả |
| :--- | :--- |
| Tên DB Subnet Group | `inventory-db-subnet-group` |
| VPC | `inventory-vpc` (`10.0.0.0/16`) |
| Các subnet thành viên | `private-db-subnet-1`, `private-db-subnet-2` |
| Availability Zones | `us-east-1a`, `us-east-1b` |
| Trạng thái | Tạo thành công theo kết quả triển khai được cung cấp. |

DB Subnet Group đã sẵn sàng để được lựa chọn làm cấu hình mạng khi tạo Amazon RDS.

**Hình 1. DB Subnet Group `inventory-db-subnet-group`**

![DB Subnet Group inventory-db-subnet-group](./screenshots/11_rds_subnet_group.png)

### 3.2. Rà soát Route Tables

Nhóm đã kiểm tra Route Tables liên quan đến hai private subnets để rà soát việc liên kết subnet và định tuyến mạng theo thiết kế. Thông tin bàn giao xác nhận việc rà soát đã được thực hiện, nhưng không kèm Route Table ID hoặc chi tiết từng route. Vì vậy, báo cáo không ghi nhận các giá trị route cụ thể khi chưa có cấu hình hoặc ảnh chụp đối chiếu.

**Hình 2. Route Tables của các private subnets**

![Route Tables của private subnets](./screenshots/12_private_route_tables.png)

### 3.3. Rà soát `inventory-db-sg`

Nhóm đã rà soát quy tắc bảo mật của `inventory-db-sg` theo phạm vi công việc. Thông tin bàn giao chưa bao gồm chi tiết các rule inbound/outbound, protocol, port hoặc source thực tế; các giá trị này cần được đối chiếu với cấu hình AWS khi bổ sung minh chứng.

**Hình 3. Quy tắc bảo mật của `inventory-db-sg`**

![Quy tắc bảo mật inventory-db-sg](./screenshots/13_inventory_db_sg.png)

### 3.4. Thiết lập AWS Elastic Beanstalk

Nhóm đã tạo Elastic Beanstalk Application `inventory-app` và Environment ban đầu `inventory-env` trong VPC `inventory-vpc`. Environment này dùng Python 3.14 trên Amazon Linux 2023 và **Sample application** để kiểm tra khởi tạo; đây chưa phải ứng dụng của nhóm. Khi deploy ứng dụng, bước cài dependencies thất bại do `psycopg2-binary==2.9.9` không build được trên Python 3.14 trong môi trường Beanstalk. Nhóm chuyển sang tạo Environment mới `inventory-env-py312` sử dụng Python 3.12 trên Amazon Linux 2023 và triển khai source bundle của ứng dụng.

Environment `inventory-env-py312` khởi chạy thành công với Health `Ok` (Green), Running version `1.0`, và domain `inventory-env-py312.eba-vbehyxmh.us-east-1.elasticbeanstalk.com`. Environment chạy trong `inventory-vpc`, dùng Single instance, public subnets và public IP để phục vụ HTTP. Cấu hình quyền sử dụng Service role `LabRole` và EC2 Instance Profile `LabInstanceProfile`; EC2 được gắn `inventory-web-sg`. Security Group của RDS cho phép PostgreSQL TCP/5432 từ `inventory-web-sg`, không mở cổng database cho toàn Internet.

Ảnh minh chứng hạ tầng ban đầu:

**Hình 4. Environment `inventory-env` khởi chạy thành công**

![Environment inventory-env khởi chạy thành công](./screenshots/14_beanstalk_environment_health.png)

**Hình 5. Cấu hình mạng của Elastic Beanstalk Environment**

![Cấu hình mạng Environment trong inventory-vpc](./screenshots/16_beanstalk_networking.png)

**Hình 6. Chi tiết EC2 instance do Elastic Beanstalk quản lý**

![Chi tiết EC2 instance của inventory-env](./screenshots/17_beanstalk_ec2_instance.png)

**Hình 7. IAM role, Security Groups và inbound rules của EC2 instance**

![IAM role và Security Groups của EC2 instance](./screenshots/18_beanstalk_ec2_security.png)

### 3.5. Cấu hình kết nối và khởi tạo cấu trúc CSDL trên Amazon RDS

Theo thông tin triển khai được cung cấp, Amazon RDS PostgreSQL `inventory-db` đã được tạo trong Region `us-east-1`. Endpoint được bàn giao cho SV1 để cấu hình ứng dụng Web. Các thông số kết nối hiện có được tổng hợp trong bảng sau:

| Thông số | Giá trị |
| :--- | :--- |
| DB instance | `inventory-db` |
| Endpoint (`DB_HOST`) | `inventory-db.c92a24squlld.us-east-1.rds.amazonaws.com` |
| Port (`DB_PORT`) | `5432` |
| Database (`DB_NAME`) | `inventory_db` |
| Username (`DB_USER`) | `postgres` |
| Password (`DB_PASSWORD`) | Được quản lý riêng, không ghi trong báo cáo |

Schema PostgreSQL tại [schema.sql](../../database/schema.sql) định nghĩa hai bảng `products` và `transactions`, cùng các index hỗ trợ truy vấn. Script [init_db.py](../../init_db.py) được chuẩn bị để đọc schema và kết nối bằng các biến môi trường; script ưu tiên `DB_PASSWORD` và vẫn hỗ trợ `DB_PASS` để tương thích với cấu hình cũ.

Schema đã được thực thi từ EC2 `inventory-env` tới RDS bằng kết nối PostgreSQL có xác thực SSL (`sslmode=verify-full`). Kết quả thực thi cho thấy các câu lệnh tạo bảng và index hoàn tất. Khi chạy lại schema để kiểm tra, PostgreSQL trả về thông báo các quan hệ đã tồn tại và bỏ qua thao tác tạo trùng; đây là hành vi mong đợi do schema sử dụng `IF NOT EXISTS`.

Sau đó, nhóm truy vấn `information_schema.tables` và nhận được hai kết quả `products` và `transactions` trong schema `public`. Như vậy, việc tạo cấu trúc hai bảng trên database `inventory_db` đã được xác minh. Schema chỉ tạo bảng và index, không chèn dữ liệu sản phẩm mẫu. Ảnh chụp terminal ghi nhận lệnh thực thi và kết quả truy vấn được dùng làm minh chứng cho bước này.

**Hình 8. Kết quả khởi tạo schema và xác minh hai bảng trên RDS**

![Kết quả tạo và xác minh hai bảng trên RDS](./screenshots/19_rds_tables_created.png)

### 3.6. Triển khai ứng dụng và kiểm thử tích hợp

Nhóm đóng gói source bundle gồm `app.py`, `init_db.py`, `database/`, `templates/`, `requirements.txt` và `Procfile`, sau đó triển khai lên `inventory-env-py312`. Environment sử dụng biến môi trường để kết nối RDS; mật khẩu không được ghi trong báo cáo. Ứng dụng chạy qua Gunicorn theo `Procfile`.

Sau triển khai, trang Inventory App tải thành công và hiển thị sản phẩm kiểm thử `test` lấy từ kho dữ liệu. Nhóm thao tác nhập/xuất trên giao diện và kiểm tra dữ liệu tồn kho được cập nhật. Ảnh chụp giao diện ghi nhận một sản phẩm với số lượng tồn là 10 tại thời điểm chụp.

Nhóm kiểm tra endpoint `GET /api/products` trên domain Beanstalk. API trả HTTP `200 OK` và JSON chứa sản phẩm `test`; phản hồi tại thời điểm chụp ghi nhận số lượng là 11. Khác biệt số lượng giữa hai ảnh phản ánh thời điểm chụp sau các thao tác kiểm thử; cả hai minh chứng đều cho thấy ứng dụng đọc dữ liệu sản phẩm từ database.

**Hình 9. Environment `inventory-env-py312` hoạt động với Health `Ok`**

![Elastic Beanstalk inventory-env-py312 Health Ok](./screenshots/20_beanstalk_env_py312_green.png)

**Hình 10. Giao diện Inventory App hiển thị dữ liệu sản phẩm từ kho**

![Inventory App hiển thị sản phẩm đã lưu](./screenshots/21_inventory_web_rds_integration.png)

**Hình 11. Kiểm thử API `GET /api/products` trả HTTP 200**

![API GET products trả HTTP 200 và JSON sản phẩm](./screenshots/22_api_products_test.png)

---

## 4. KẾT QUẢ VÀ MINH CHỨNG

| Hạng mục | Kết quả | Minh chứng |
| :--- | :--- | :--- |
| `inventory-db-subnet-group` | Đã tạo thành công với hai private subnets thuộc `us-east-1a` và `us-east-1b`; sẵn sàng cung cấp hạ tầng mạng cho RDS. | Hình 1: `screenshots/11_rds_subnet_group.png`. |
| Amazon RDS `inventory-db` | RDS PostgreSQL đã được tạo; endpoint, port, database và username được tổng hợp tại Mục 3.5. | Endpoint được nhóm cung cấp; schema và hai bảng được xác minh trong Hình 8. |
| Khởi tạo schema trên RDS | Đã thực thi schema trên `inventory_db`; truy vấn xác nhận có đủ hai bảng `products` và `transactions` trong schema `public`. Chạy lại schema không tạo trùng bảng/index do có `IF NOT EXISTS`. | Hình 8: `screenshots/19_rds_tables_created.png`. |
| Route Tables | Đã rà soát theo yêu cầu công việc. | Hình 2: `screenshots/12_private_route_tables.png`. |
| `inventory-db-sg` | Đã rà soát theo yêu cầu công việc. | Hình 3: `screenshots/13_inventory_db_sg.png`. |
| Elastic Beanstalk `inventory-env-py312` | Ứng dụng đã được triển khai trên Python 3.12 / Amazon Linux 2023; Health `Ok` (Green), Running version `1.0`. | Hình 9: `screenshots/20_beanstalk_env_py312_green.png`. |
| Cấu hình VPC, subnet và IAM | Environment ở `inventory-vpc`, public subnets; sử dụng `LabRole`, `LabInstanceProfile` và `inventory-web-sg`. | Hình 5–7: `screenshots/16_beanstalk_networking.png`, `17_beanstalk_ec2_instance.png`, `18_beanstalk_ec2_security.png`. |
| Tích hợp Web với RDS | Giao diện tải và hiển thị sản phẩm kiểm thử; dữ liệu được đọc từ kho dữ liệu. | Hình 10: `screenshots/21_inventory_web_rds_integration.png`. |
| Kiểm thử REST API | `GET /api/products` trả HTTP `200 OK` và JSON sản phẩm. | Hình 11: `screenshots/22_api_products_test.png`. |

---

## 5. KHAI BÁO SỬ DỤNG TRỢ LÝ AI

- **Công cụ và model:** Trợ lý AI trong cuộc trao đổi này được sử dụng để biên soạn và rà soát nội dung báo cáo. Model cụ thể không được xác định trong thông tin phiên làm việc. AWS Console và AWS CLI là công cụ kỹ thuật, không phải công cụ AI.
- **Phạm vi hỗ trợ:** Hỗ trợ biên tập nội dung báo cáo về hạ tầng mạng, Amazon RDS, Elastic Beanstalk, triển khai ứng dụng và kiểm thử tích hợp; cập nhật script khởi tạo schema để ưu tiên biến `DB_PASSWORD`.
- **Nội dung được hỗ trợ biên soạn:** Cấu trúc lại báo cáo theo các phần mục tiêu, thiết kế mạng, công việc đã thực hiện, kết quả/minh chứng và kết luận.
- **Kiểm chứng:** AI không truy cập AWS account và không trực tiếp tạo hoặc thay đổi tài nguyên AWS. Việc chạy schema, triển khai Environment và kiểm thử ứng dụng do nhóm thực hiện; báo cáo dựa trên kết quả và ảnh minh chứng được lưu trong repository.
- **Minh chứng tham chiếu:** [Nhật ký công việc tuần 2](../../logs/week2.md).

---

## 6. KẾT LUẬN

Trong tuần 2, nhóm đã chuẩn bị DB Subnet Group và Security Group cho tầng dữ liệu, tạo RDS PostgreSQL `inventory-db`, thực thi schema và xác nhận hai bảng `products`, `transactions`. Ứng dụng Flask đã được triển khai trên Elastic Beanstalk Environment `inventory-env-py312` dùng Python 3.12; Environment đạt Health `Ok` (Green). Kiểm thử giao diện xác nhận sản phẩm được hiển thị từ database; API `GET /api/products` trả `200 OK` cùng dữ liệu JSON. Các minh chứng tương ứng được trình bày tại Hình 8–11. Environment ban đầu `inventory-env` đã dùng Sample application và không phải Environment đang chạy ứng dụng Flask.
