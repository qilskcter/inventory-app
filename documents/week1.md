
        subgraph PublicZone ["Public Subnets (Có kết nối Internet)"]
            subgraph PubSubnet1 ["public-subnet-1 (10.0.1.0/24) | us-east-1a"]
                WebApp1["Web App / Beanstalk\n(Flask Port 80/5000)"]
            end
            subgraph PubSubnet2 ["public-subnet-2 (10.0.2.0/24) | us-east-1b"]
                WebApp2["Web App Backup Tier\n(Mở rộng dự phòng)"]
            end
        end

        subgraph SecurityGroupWeb ["Security Group: inventory-web-sg"]
            WebApp1
            WebApp2
        end

        subgraph PrivateZone ["Private Subnets (Cô lập hoàn toàn khỏi Internet)"]
            subgraph PrivSubnet1 ["private-db-subnet-1 (10.0.11.0/24) | us-east-1a"]
                RDSMaster[("Amazon RDS PostgreSQL\nMaster Instance\n(Port 5432)")]
            end
            subgraph PrivSubnet2 ["private-db-subnet-2 (10.0.12.0/24) | us-east-1b"]
                RDSStandby[("RDS DB Subnet Group\n(AZ Standby Area)")]
            end
        end

        subgraph SecurityGroupDB ["Security Group: inventory-db-sg"]
            RDSMaster
            RDSStandby
        end
    end

    Internet <==>|Inbound HTTP :80, :5000| IGW
    IGW <==> PublicZone

    SecurityGroupWeb ==>|Chỉ cho phép TCP :5432\ntruy cập nội bộ| SecurityGroupDB

```

---

### 5.6. Ma trận Phân luồng Lưu lượng Mạng (Network Traffic Flow Matrix)

| Chiều giao tiếp | Nguồn (Source) | Đích (Destination) | Cổng & Giao thức | Trạng thái | Đánh giá & Cơ chế Bảo vệ |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Internet ➔ Web** | `0.0.0.0/0` | `inventory-web-sg` | TCP `80`, `5000` | **Cho phép** (ALLOW) | Người dùng truy cập dịch vụ quản lý kho bình thường. |
| **Internet ➔ Database** | `0.0.0.0/0` | `inventory-db-sg` | Bất kỳ cổng nào | **CHẶN** (DENY) | RDS nằm ở Private Subnet, không có Public IP và không có Route ra IGW. |
| **Web ➔ Database** | `inventory-web-sg` | `inventory-db-sg` | TCP `5432` | **Cho phép** (ALLOW) | Web App đọc/ghi danh mục sản phẩm và lịch sử giao dịch kho. |
| **Nguồn lạ trong VPC ➔ DB** | Dải IP khác / SG khác | `inventory-db-sg` | TCP `5432` | **CHẶN** (DENY) | `inventory-db-sg` chỉ cấp quyền cho nguồn có nhãn `inventory-web-sg`. |
| **Web Tier ➔ AWS Services** | `inventory-web-sg` | S3, SNS, EventBridge | TCP `443` (HTTPS) | **Cho phép** (ALLOW) | Tải ảnh lên S3 Bucket và gửi email cảnh báo tồn kho qua SNS Topic. |

---

### 5.7. Báo cáo Rà soát AI & Tuân thủ Quy định Gắn thẻ (Tagging)

* **Hỗ trợ từ Trợ lý AI (Amazon Q Developer):**
  * Đã kiểm tra tính hợp lệ của quy tắc Security Group Chaining, xác nhận việc liên kết `Source = inventory-web-sg` giúp loại bỏ hoàn toàn việc phải cập nhật lại IP động của EC2/Beanstalk mỗi khi khởi động lại máy chủ.
  * Xác nhận thiết kế chia subnet `/24` hoàn toàn không bị chồng lấn (No overlapping CIDRs) và đáp ứng đúng quy định tối thiểu 2 AZs cho RDS PostgreSQL trên AWS.
* **Quy chuẩn Tagging bắt buộc được chuẩn hóa cho toàn bộ tài nguyên mạng:**
  * Tag `Project`: `inventory-app`
  * Tag `Owner`: `Khanh-Quan`
* **Mức độ hoàn thành:** Bản thiết kế chi tiết đã hoàn tất vào Thứ Năm (14:00 - 17:00, 3.0h) và sẵn sàng 100% để tiến hành khởi tạo thực tế trên AWS Management Console vào Thứ Sáu.
