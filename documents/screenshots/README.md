# HƯỚNG DẪN LƯU TRỮ ẢNH CHỤP MINH CHỨNG HẠ TẦNG AWS (TUẦN 1)

Thư mục này dùng để lưu trữ các ảnh chụp màn hình minh chứng thao tác thực tế trên **AWS Learner Lab** (Region `us-east-1`), phục vụ việc nộp đồ án và bảo vệ trước Giảng viên hướng dẫn.

> **Quy định môn học:** Mọi ảnh chụp màn hình phải hiển thị rõ:
> 1. Góc trên bên phải AWS Console có **AWS Account ID** (`041118630529`) hoặc User ARN.
> 2. Region đang hoạt động là **N. Virginia (`us-east-1`)**.
> 3. Tên tài nguyên đúng tiền tố `inventory-*` và có đầy đủ thẻ Tags (`Project: inventory-app`, `Owner: Khanh-Quan`).

---

### Danh sách ảnh minh chứng cần lưu trữ:

| Tên file đề xuất | Nội dung minh chứng | Dịch vụ AWS | Sinh viên thực hiện |
| :--- | :--- | :---: | :---: |
| `01_aws_sts_identity.png` | Xác minh Caller Identity & ARN sinh viên | AWS CLI / STS | Nguyễn Đình Khanh |
| `02_labrole_policies.png` | Danh sách 7 IAM Policies gắn với `LabRole` | AWS IAM | Nguyễn Đình Khanh |
| `03_s3_bucket_created.png` | S3 Bucket `inventory-reports-us-east-1-24110244` & Tagging | Amazon S3 | Nguyễn Đình Khanh |
| `04_vpc_created.png` | Chi tiết VPC `inventory-vpc` (`10.0.0.0/16`) & DNS settings | Amazon VPC | Võ Minh Quân |
| `05_subnets_list.png` | 4 Subnets (2 Public, 2 Private) trên 2 AZs (`us-east-1a`, `us-east-1b`) | Amazon VPC | Võ Minh Quân |
| `06_route_tables.png` | Bảng định tuyến Public RT (trỏ tới IGW) và Private RT (local only) | Amazon VPC | Võ Minh Quân |
| `07_internet_gateway.png` | Internet Gateway `inventory-igw` đã attach vào `inventory-vpc` | Amazon VPC | Võ Minh Quân |
| `08_security_group_web.png` | `inventory-web-sg` với Inbound Rules (Port 80, 5000, 443) | EC2 / Security Group | Võ Minh Quân |
| `09_security_group_db.png` | `inventory-db-sg` với Security Group Chaining (Port 5432 từ Web SG) | EC2 / Security Group | Võ Minh Quân |
| `10_lab_instance_profile.png` | Xác minh `LabInstanceProfile` liên kết với `LabRole` | AWS IAM | Võ Minh Quân |
