# Hệ thống Quản lý Kho hàng & Cảnh báo Tồn kho (Inventory Management System)

Ứng dụng quản lý kho hàng cloud-native được xây dựng cho đồ án môn học Điện toán đám mây (Cloud Computing), hỗ trợ quản lý sản phẩm, theo dõi lịch sử xuất/nhập kho và tự động cảnh báo khi tồn kho chạm ngưỡng tối thiểu.

---
# Phân công công việc

| Tuần | Phân Công |
| --- | --- |
| Tuần 1 | [week1.md](./logs/week1.md) |
| Tuần 2 | [week2.md](./logs/week2.md) |
| Tuần 3 | [week3.md](./logs/week3.md) |
| Tuần 4 | [week4.md](./logs/week4.md) |
---

# Báo cáo tuần

| Tuần | Báo cáo |
| --- | --- |
| Tuần 1 | [week1.md](./documents/week_1/week1.md) |
| Tuần 2 | [week2.md](./documents/week_2/week2.md) |
| Tuần 3 | [week3.md](./documents/week_3/week3.md) |
| Tuần 4 | [week4.md](./documents/week_4/week4.md) |

---

## Tính năng chính
* **Quản lý sản phẩm (CRUD):** Thêm mới, cập nhật thông tin, theo dõi số lượng tồn kho và thiết lập định mức cảnh báo tối thiểu cho từng sản phẩm (SKU).
* **Quản lý Nhập/Xuất kho:** Ghi nhận các giao dịch nhập hàng (Inbound) và xuất hàng (Outbound) với cơ chế kiểm tra tồn kho theo thời gian thực để tránh tình trạng xuất quá số lượng hiện có.
* **Cảnh báo tồn kho thấp:** Tự động phát hiện và hiển thị cảnh báo (trực quan trên giao diện và tích hợp AWS SNS) khi số lượng sản phẩm tụt xuống dưới ngưỡng an toàn.
* **Triển khai AWS:** Ứng dụng Flask được triển khai trên AWS Elastic Beanstalk và sử dụng Amazon RDS for PostgreSQL để lưu dữ liệu.

## Flask JSON API

Các endpoint API dùng JSON; lỗi trả về theo định dạng `{"error": "..."}`. Tồn kho chỉ được thay đổi qua giao dịch nhập/xuất để giữ lịch sử giao dịch nhất quán.

| Method | Endpoint | Chức năng |
| --- | --- | --- |
| `GET` | `/api/products` | Liệt kê sản phẩm |
| `POST` | `/api/products` | Tạo sản phẩm (`sku`, `name`; `quantity` mặc định `0`, `min_threshold` mặc định `5`) |
| `GET` | `/api/products/<id>` | Xem sản phẩm |
| `PUT` | `/api/products/<id>` | Cập nhật `sku`, `name`, `min_threshold` |
| `PATCH` | `/api/products/<id>` | Cập nhật một hoặc nhiều trường trên |
| `DELETE` | `/api/products/<id>` | Xóa sản phẩm |
| `GET` | `/api/transactions` | Xem lịch sử nhập/xuất |
| `POST` | `/api/transactions` | Tạo giao dịch kho |

Ví dụ tạo giao dịch nhập kho:

```bash
curl -X POST http://127.0.0.1:5000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "type": "IN", "quantity": 10}'
```

Giao dịch xuất được cập nhật tồn kho bằng một câu lệnh SQL có điều kiện, nên không thể xuất vượt tồn ngay cả khi có yêu cầu đồng thời. Cả cập nhật tồn kho và ghi lịch sử đều commit trong cùng một database transaction. Thành công trả `201`; dữ liệu không hợp lệ trả `400`, không tìm thấy sản phẩm trả `404`, SKU trùng hoặc tồn kho không đủ trả `409`.

---

## Công nghệ sử dụng
* **Backend:** Python (Flask Framework)
* **Database:** PostgreSQL / Amazon RDS PostgreSQL
* **Frontend:** HTML5, Bootstrap 5, Jinja2 Templates
* **Cloud & DevOps:** AWS Elastic Beanstalk, Amazon RDS for PostgreSQL. AWS Lambda, Amazon S3, Amazon EventBridge, AWS SNS và CloudFormation là các dịch vụ dự kiến mở rộng, chưa thuộc luồng triển khai hiện tại.

## Bản triển khai AWS

Ứng dụng hiện được triển khai trong AWS Region `us-east-1` (N. Virginia):

| Thành phần | Cấu hình |
| --- | --- |
| Elastic Beanstalk Application | `inventory-app` |
| Environment đang chạy ứng dụng | `inventory-env-py312` |
| Platform | Python 3.12 trên 64-bit Amazon Linux 2023 |
| Environment type | Single instance |
| Database | Amazon RDS for PostgreSQL |
| Database name | `inventory_db` |
| RDS endpoint | `inventory-db.c92a24squlld.us-east-1.rds.amazonaws.com` |
| PostgreSQL port | `5432` |
| Public application URL | [inventory-env-py312.eba-vbehyxmh.us-east-1.elasticbeanstalk.com](http://inventory-env-py312.eba-vbehyxmh.us-east-1.elasticbeanstalk.com/) |

RDS được đặt trong VPC và ứng dụng kết nối qua Security Group; chỉ cấp quyền PostgreSQL TCP/5432 từ Security Group của tầng Web. Environment properties được cấu hình trên Elastic Beanstalk (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`); không lưu mật khẩu trong repository. URL minh họa hiện dùng HTTP, không truyền dữ liệu nhạy cảm qua môi trường này.

### CloudWatch Logs và lỗi kết nối database

Source bundle chứa `.ebextensions/01-cloudwatch-logs.config`, bật stream các log mặc định của Elastic Beanstalk lên CloudWatch Logs, lưu log 7 ngày và giữ lại log group khi terminate environment. Với Python trên Amazon Linux 2023, các log mặc định bao gồm `web.stdout.log`, Nginx access log và Nginx error log. Instance profile cần policy `AWSElasticBeanstalkWebTier` hoặc quyền CloudWatch Logs tương ứng.

Sau khi deploy cấu hình, xem log tại Elastic Beanstalk → chọn `inventory-env-py312` → **Logs**. Cấu hình trong repository chưa tự xác nhận rằng AWS environment đã áp dụng thành công; cần kiểm tra các log group/log stream trong Console sau deployment.

Kết nối PostgreSQL dùng `DB_CONNECT_TIMEOUT` tính bằng giây (mặc định 5, phải là số nguyên dương). Lỗi kết nối/vận hành database được ghi vào log ứng dụng và trả HTTP `503` cùng `Retry-After: 5`; chi tiết lỗi nội bộ không được gửi về client.

---

## Cấu trúc thư mục dự án
```text
inventory-app/
│
├── app.py                  # Mã nguồn chính của ứng dụng Flask & kết nối CSDL
├── init_db.py              # Script Python tự động đọc database/schema.sql và khởi tạo/cập nhật CSDL
├── database/               # Thư mục chứa cấu trúc CSDL
│   └── schema.sql          # Script SQL DDL chứa cấu trúc 2 bảng products & transactions
├── Procfile                # Lệnh khởi động Gunicorn trên Elastic Beanstalk
├── documents/              # Báo cáo chi tiết đồ án các tuần (week1.md)
├── logs/                   # Nhật ký phân công và tiến độ công việc (week1.md)
├── scripts/                # Kịch bản tự động hóa hạ tầng AWS (Security Groups, VPC, IAM)
├── templates/              # Thư mục chứa giao diện HTML (Bootstrap 5)
│   └── index.html          # Giao diện trang chủ quản lý kho & bảng dữ liệu
├── tests/                  # Bộ kiểm thử tự động (Unit Test & Integration Test)
│   └── test_app.py         # Kiểm thử các API và giao diện Flask
└── requirements.txt        # Danh sách các thư viện Python phụ thuộc
```

---

## Hướng dẫn Cài đặt & Chạy thử (Localhost)

### 1. Yêu cầu hệ thống

* Python 3.12 được khuyến nghị cho môi trường hiện tại.
* PostgreSQL đã được cài đặt và khởi động (hoặc có thông tin kết nối AWS RDS PostgreSQL).

### 2. Các bước thực hiện

1. **Clone repository này về máy:**
```bash
git clone https://github.com/TEN_USER_CUA_BAN/inventory-app.git
cd inventory-app
```

2. **Tạo và kích hoạt môi trường ảo (Virtual Environment):**
* *Trên macOS / Linux (Python 3.12):*
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

* *Trên Windows:*
```bash
python -m venv venv
venv\Scripts\activate
```

3. **Cài đặt các thư viện cần thiết:**
```bash
pip install -r requirements.txt
```

4. **Cấu hình kết nối cơ sở dữ liệu:**
Đặt các biến môi trường theo cấu hình PostgreSQL local. `DB_PASSWORD` là tên biến ưu tiên; `DB_PASS` vẫn được hỗ trợ để tương thích ngược. Trên macOS dùng zsh, nhập mật khẩu tương tác như sau:
```bash
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="inventory_db"
export DB_USER="postgres"
```

Không lưu mật khẩu thật trong mã nguồn.

Trong zsh, nhập mật khẩu mà không echo ra terminal rồi export:
```zsh
read -s "DB_PASSWORD?Local PostgreSQL password: "
export DB_PASSWORD
```

Không dùng mật khẩu RDS trừ khi đó cũng chính là mật khẩu của PostgreSQL local. Trên AWS, cấu hình các giá trị RDS trong Elastic Beanstalk Environment properties, không đưa chúng vào source bundle.

Ví dụ kiểm thử API trên local:
```bash
curl -i "http://127.0.0.1:5000/api/products"
```

Ví dụ gọi API trên AWS:
```bash
curl -i "http://inventory-env-py312.eba-vbehyxmh.us-east-1.elasticbeanstalk.com/api/products"
```

5. **Khởi tạo / Cập nhật Cơ sở dữ liệu (Database Setup & Update):**

Bạn có thể chọn 1 trong 2 cách sau để khởi tạo hoặc cập nhật cấu trúc CSDL từ `database/schema.sql`:

* **Cách 1: Dùng script Python (Khuyên dùng):**
```bash
python init_db.py
```
Script đọc `database/schema.sql`, tạo các bảng và index nếu chưa có, và trả lỗi khác 0 nếu không kết nối hoặc thực thi schema thất bại.

* **Cách 2: Chạy trực tiếp qua câu lệnh `psql`:**
```bash
psql -h localhost -U postgres -d inventory_db -f database/schema.sql
```

*(Lưu ý: Khi chạy ứng dụng bằng `python app.py`, hệ thống cũng gọi hàm khởi tạo schema. Các lệnh `CREATE ... IF NOT EXISTS` cho phép chạy lại mà không tạo trùng bảng/index.)*

6. **Chạy ứng dụng:**
```bash
python app.py
```

7. **Trải nghiệm:**
Mở trình duyệt web và truy cập vào địa chỉ: `http://127.0.0.1:5000`

---

## Thành viên nhóm / Tác giả

* **Họ tên sinh viên:** Nguyễn Đình Khanh (MSSV: 24110244), Võ Minh Quân (MSSV: 24110312)
* **Môn học:** Cloud Computing (Cloud - Dot 1 - 2026-2027)
* **Giảng viên hướng dẫn:** ThS. Huỳnh Xuân Phụng
