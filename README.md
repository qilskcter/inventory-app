# Hệ thống Quản lý Kho hàng & Cảnh báo Tồn kho (Inventory Management System)

Ứng dụng quản lý kho hàng cloud-native được xây dựng cho đồ án môn học Điện toán đám mây (Cloud Computing), hỗ trợ quản lý sản phẩm, theo dõi lịch sử xuất/nhập kho và tự động cảnh báo khi tồn kho chạm ngưỡng tối thiểu.

---

## Tính năng chính
* **Quản lý sản phẩm (CRUD):** Thêm mới, cập nhật thông tin, theo dõi số lượng tồn kho và thiết lập định mức cảnh báo tối thiểu cho từng sản phẩm (SKU).
* **Quản lý Nhập/Xuất kho:** Ghi nhận các giao dịch nhập hàng (Inbound) và xuất hàng (Outbound) với cơ chế kiểm tra tồn kho theo thời gian thực để tránh tình trạng xuất quá số lượng hiện có.
* **Cảnh báo tồn kho thấp:** Tự động phát hiện và hiển thị cảnh báo (trực quan trên giao diện và tích hợp AWS SNS) khi số lượng sản phẩm tụt xuống dưới ngưỡng an toàn.
* **Nền tảng Cloud-Ready:** Thiết kế tương thích với các dịch vụ AWS (Elastic Beanstalk, RDS PostgreSQL, S3, EventBridge, SNS).

---

## Công nghệ sử dụng
* **Backend:** Python (Flask Framework)
* **Database:** PostgreSQL / Amazon RDS PostgreSQL
* **Frontend:** HTML5, Bootstrap 5, Jinja2 Templates
* **Cloud & DevOps (Dự kiến):** AWS Elastic Beanstalk, AWS Lambda, Amazon S3, Amazon EventBridge, AWS SNS, CloudFormation.

---

## Cấu trúc thư mục dự án
```text
inventory-app/
│
├── app.py                  # Mã nguồn chính của ứng dụng Flask & kết nối CSDL
├── init_db.py              # Script Python tự động đọc database/schema.sql và khởi tạo/cập nhật CSDL
├── database/               # Thư mục chứa cấu trúc CSDL
│   └── schema.sql          # Script SQL DDL chứa cấu trúc 2 bảng products & transactions
├── requirements.txt        # Danh sách các thư viện Python phụ thuộc
└── templates/              # Thư mục chứa giao diện HTML
    └── index.html          # Giao diện trang chủ quản lý kho & bảng dữ liệu
```

---

## Hướng dẫn Cài đặt & Chạy thử (Localhost)

### 1. Yêu cầu hệ thống

* Python 3.x đã được cài đặt trên máy tính.
* PostgreSQL đã được cài đặt và khởi động (hoặc có thông tin kết nối AWS RDS PostgreSQL).

### 2. Các bước thực hiện

1. **Clone repository này về máy:**
```bash
git clone https://github.com/TEN_USER_CUA_BAN/inventory-app.git
cd inventory-app
```

2. **Tạo và kích hoạt môi trường ảo (Virtual Environment):**
* *Trên macOS / Linux:*
```bash
python3 -m venv venv
source venv/bin/activate
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
Mở file `init_db.py` (hoặc đặt các biến môi trường `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`, `DB_PORT`) cho khớp với cấu hình PostgreSQL máy bạn:
```python
DB_HOST = "localhost"
DB_NAME = "inventory_db"   # Đảm bảo bạn đã tạo database này trên PostgreSQL
DB_USER = "postgres"
DB_PASS = "123456"         # Mật khẩu database của bạn
DB_PORT = "5432"
```

5. **Khởi tạo / Cập nhật Cơ sở dữ liệu (Database Setup & Update):**

Bạn có thể chọn 1 trong 2 cách sau để khởi tạo hoặc cập nhật cấu trúc CSDL từ `database/schema.sql`:

* **Cách 1: Dùng script Python (Khuyên dùng):**
```bash
python init_db.py
```

* **Cách 2: Chạy trực tiếp qua câu lệnh `psql`:**
```bash
psql -h localhost -U postgres -d inventory_db -f database/schema.sql
```

*(Lưu ý: Khi chạy ứng dụng `python app.py`, hệ thống cũng sẽ tự động gọi hàm khởi tạo CSDL từ `init_db.py` nếu các bảng chưa tồn tại).*

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
