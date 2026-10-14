# BÁO CÁO KỸ THUẬT VÀ KẾT QUẢ TRIỂN KHAI - TUẦN 2
## CHUẨN BỊ HẠ TẦNG MẠNG CHO AMAZON RDS

**Dự án:** Hệ thống quản lý kho hàng và cảnh báo tồn kho (`inventory-app`)  
**Môn học:** Điện toán đám mây (Cloud Computing)  
**Sinh viên thực hiện:**
- Nguyễn Đình Khanh (MSSV: 24110244)
- Võ Minh Quân (MSSV: 24110312)  
**Giảng viên hướng dẫn:** ThS. Huỳnh Xuân Phụng  
**AWS Region:** `us-east-1` (N. Virginia)

---

> **Phạm vi báo cáo:** Báo cáo tập trung vào việc khởi tạo DB Subnet Group `inventory-db-subnet-group` từ hai private subnets ở hai Availability Zones, đồng thời rà soát Route Tables và quy tắc bảo mật của `inventory-db-sg`.

[Nhật ký công việc tuần 2](../../logs/week2.md)

---

## 1. MỤC TIÊU

Tuần 2, nhóm thực hiện công tác chuẩn bị mạng cho tầng cơ sở dữ liệu của hệ thống. Các mục tiêu cụ thể gồm:

1. Tạo DB Subnet Group `inventory-db-subnet-group` trong VPC dự án, kết hợp hai private subnets ở hai Availability Zones.
2. Rà soát Route Tables đang áp dụng cho các private subnets.
3. Rà soát quy tắc bảo mật của `inventory-db-sg` để kiểm soát nguồn được phép kết nối tới Database.

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

---

## 4. KẾT QUẢ VÀ MINH CHỨNG

| Hạng mục | Kết quả | Minh chứng |
| :--- | :--- | :--- |
| `inventory-db-subnet-group` | Đã tạo thành công với hai private subnets thuộc `us-east-1a` và `us-east-1b`; sẵn sàng cung cấp hạ tầng mạng cho RDS. | Chèn tại Hình 1; tên file đề xuất `11_rds_subnet_group.png`. |
| Route Tables | Đã rà soát theo yêu cầu công việc. | Chèn tại Hình 2; tên file đề xuất `12_private_route_tables.png`. |
| `inventory-db-sg` | Đã rà soát theo yêu cầu công việc. | Chèn tại Hình 3; tên file đề xuất `13_inventory_db_sg.png`. |

---

## 5. KHAI BÁO SỬ DỤNG TRỢ LÝ AI

- **Công cụ và model:** Trợ lý AI trong cuộc trao đổi này được sử dụng để biên soạn và rà soát nội dung báo cáo. Model cụ thể không được xác định trong thông tin phiên làm việc. AWS Console và AWS CLI là công cụ kỹ thuật, không phải công cụ AI.
- **Phạm vi hỗ trợ:** Hỗ trợ sắp xếp nội dung báo cáo về DB Subnet Group, Route Tables và `inventory-db-sg`; làm rõ vai trò của DB Subnet Group và cách trình bày kết quả, minh chứng.
- **Nội dung được hỗ trợ biên soạn:** Cấu trúc lại báo cáo theo các phần mục tiêu, thiết kế mạng, công việc đã thực hiện, kết quả/minh chứng và kết luận.
- **Kiểm chứng:** AI không truy cập AWS account và không trực tiếp tạo tài nguyên hoặc xác minh cấu hình. Trạng thái triển khai được ghi theo thông tin người dùng/worklog cung cấp; các chi tiết cấu hình chưa có ảnh hoặc đầu ra AWS cần được nhóm đối chiếu thực tế.
- **Minh chứng tham chiếu:** [Nhật ký công việc tuần 2](../../logs/week2.md).

---

## 6. KẾT LUẬN

DB Subnet Group `inventory-db-subnet-group` đã được tạo thành công, gồm `private-db-subnet-1` tại `us-east-1a` và `private-db-subnet-2` tại `us-east-1b`. Nhóm đã rà soát Route Tables và quy tắc bảo mật của `inventory-db-sg`. Kết quả này hoàn thành phần chuẩn bị mạng thuộc phạm vi báo cáo và sẵn sàng phục vụ bước cấu hình RDS tiếp theo. Để hồ sơ triển khai đầy đủ hơn, cần lưu minh chứng thể hiện chi tiết Route Tables và các rule thực tế của `inventory-db-sg`.
