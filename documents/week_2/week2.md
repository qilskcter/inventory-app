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

> **Phạm vi báo cáo:** Báo cáo ghi nhận việc chuẩn bị mạng cho Amazon RDS và tìm hiểu, thiết lập AWS Elastic Beanstalk trong VPC `inventory-vpc`. Phần Elastic Beanstalk tập trung vào Application, Environment và cấu hình Instance Profile, Security Group cho EC2 instance do Beanstalk quản lý.

[Nhật ký công việc tuần 2](../../logs/week2.md)

---

## 1. MỤC TIÊU

Tuần 2, nhóm chuẩn bị hạ tầng mạng cho tầng cơ sở dữ liệu và thiết lập môi trường chạy ứng dụng. Các mục tiêu cụ thể gồm:

1. Tạo DB Subnet Group `inventory-db-subnet-group` trong VPC dự án, kết hợp hai private subnets ở hai Availability Zones.
2. Rà soát Route Tables đang áp dụng cho các private subnets.
3. Rà soát quy tắc bảo mật của `inventory-db-sg` để kiểm soát nguồn được phép kết nối tới Database.
4. Tìm hiểu và thiết lập Elastic Beanstalk Application và Environment cho ứng dụng trong VPC `inventory-vpc`.
5. Cấu hình `LabInstanceProfile` và Security Group `inventory-web-sg` cho EC2 instance do Elastic Beanstalk quản lý.

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

Nhóm đã tạo Elastic Beanstalk Application `inventory-app` và Environment `inventory-env` trong VPC `inventory-vpc`. Environment dùng platform Python 3.14 trên Amazon Linux 2023 và triển khai **Sample application** để kiểm tra quá trình tạo môi trường; đây chưa phải phiên bản inventory-app của nhóm. Environment khởi chạy thành công với Health `Green`.

Environment được cấu hình sử dụng Instance Profile `LabInstanceProfile` và VPC `inventory-vpc`. EC2 instance thực tế có IAM role `LabRole`, Security Group `inventory-web-sg` cùng Security Group do Elastic Beanstalk tạo. Instance chạy ở subnet `10.0.2.0/24` (`us-east-1b`) và có public IP. Inbound rules được kiểm tra trên EC2: HTTP TCP/80 cho phép từ `0.0.0.0/0`; HTTPS TCP/443 cho phép từ `171.243.49.11/32`.

Lưu các ảnh minh chứng trong thư mục `documents/week_2/screenshots/` với tên và vị trí tương đối dưới đây:

**Hình 4. Environment `inventory-env` khởi chạy thành công**

![Environment inventory-env khởi chạy thành công](./screenshots/14_beanstalk_environment_health.png)

**Hình 5. Cấu hình mạng của Elastic Beanstalk Environment**

![Cấu hình mạng Environment trong inventory-vpc](./screenshots/16_beanstalk_networking.png)

**Hình 6. Chi tiết EC2 instance do Elastic Beanstalk quản lý**

![Chi tiết EC2 instance của inventory-env](./screenshots/17_beanstalk_ec2_instance.png)

**Hình 7. IAM role, Security Groups và inbound rules của EC2 instance**

![IAM role và Security Groups của EC2 instance](./screenshots/18_beanstalk_ec2_security.png)

---

## 4. KẾT QUẢ VÀ MINH CHỨNG

| Hạng mục | Kết quả | Minh chứng |
| :--- | :--- | :--- |
| `inventory-db-subnet-group` | Đã tạo thành công với hai private subnets thuộc `us-east-1a` và `us-east-1b`; sẵn sàng cung cấp hạ tầng mạng cho RDS. | Chèn tại Hình 1; tên file đề xuất `11_rds_subnet_group.png`. |
| Route Tables | Đã rà soát theo yêu cầu công việc. | Chèn tại Hình 2; tên file đề xuất `12_private_route_tables.png`. |
| `inventory-db-sg` | Đã rà soát theo yêu cầu công việc. | Chèn tại Hình 3; tên file đề xuất `13_inventory_db_sg.png`. |
| Elastic Beanstalk Application và Environment | `inventory-app` / `inventory-env` khởi chạy thành công với Health `Green`; đang dùng Sample application. | Hình 4: `screenshots/14_beanstalk_environment_health.png`. |
| VPC và subnet của Environment | Sử dụng `inventory-vpc`, hai subnet ứng dụng; EC2 instance được kiểm tra ở subnet `10.0.2.0/24` (`us-east-1b`). | Hình 5: `screenshots/16_beanstalk_networking.png`; Hình 6: `screenshots/17_beanstalk_ec2_instance.png`. |
| Instance Profile và Security Group của EC2 | Environment dùng `LabInstanceProfile`; EC2 instance có role `LabRole` và Security Group `inventory-web-sg` cùng Security Group do Beanstalk tạo. | Hình 7: `screenshots/18_beanstalk_ec2_security.png`. |

---

## 5. KHAI BÁO SỬ DỤNG TRỢ LÝ AI

- **Công cụ và model:** Trợ lý AI trong cuộc trao đổi này được sử dụng để biên soạn và rà soát nội dung báo cáo. Model cụ thể không được xác định trong thông tin phiên làm việc. AWS Console và AWS CLI là công cụ kỹ thuật, không phải công cụ AI.
- **Phạm vi hỗ trợ:** Hỗ trợ sắp xếp nội dung báo cáo về DB Subnet Group, Route Tables, `inventory-db-sg` và Elastic Beanstalk; làm rõ vai trò của các cấu hình và cách trình bày kết quả, minh chứng.
- **Nội dung được hỗ trợ biên soạn:** Cấu trúc lại báo cáo theo các phần mục tiêu, thiết kế mạng, công việc đã thực hiện, kết quả/minh chứng và kết luận.
- **Kiểm chứng:** AI không truy cập AWS account và không trực tiếp tạo tài nguyên; nội dung Elastic Beanstalk được biên soạn dựa trên thông tin và ảnh chụp màn hình do người dùng cung cấp. Các ảnh minh chứng cần được lưu vào những đường dẫn đã nêu trong `documents/week_2/screenshots/`.
- **Minh chứng tham chiếu:** [Nhật ký công việc tuần 2](../../logs/week2.md).

---

## 6. KẾT LUẬN

DB Subnet Group `inventory-db-subnet-group` đã được tạo thành công, gồm `private-db-subnet-1` tại `us-east-1a` và `private-db-subnet-2` tại `us-east-1b`. Nhóm đã rà soát Route Tables và quy tắc bảo mật của `inventory-db-sg`, đồng thời tạo Elastic Beanstalk Application `inventory-app` và Environment `inventory-env` trong `inventory-vpc`. Environment dùng `LabInstanceProfile`; EC2 instance thực tế có role `LabRole` và Security Group `inventory-web-sg`. Environment đang chạy Sample application với Health `Green`; ứng dụng inventory-app chưa được triển khai trong bước này. Báo cáo cần kèm các ảnh minh chứng được lưu trong `documents/week_2/screenshots/`.
