# NHẬT KÝ CÔNG VIỆC (WORKLOG) - TUẦN 1

---

## I. THÔNG TIN CHUNG
* **Tên đề tài:** Xây dựng hệ thống quản lý nhập/xuất kho, cảnh báo tồn kho thấp và báo cáo định kỳ
* **Sản phẩm dự kiến toàn khóa:**
  * **Backend:** Web App chạy trên AWS Elastic Beanstalk (hoặc AWS Lambda) kết nối Amazon RDS PostgreSQL.
  * **Cảnh báo tự động:** AWS Lambda định kỳ kiểm tra mức tồn kho sản phẩm $\rightarrow$ Kích hoạt gửi thông báo qua AWS SNS Topic.
  * **Báo cáo định kỳ:** Tự động tổng hợp báo cáo dạng PDF/CSV hằng tuần lưu trữ an toàn trên Amazon S3.
  * **Hạ tầng dưới dạng mã (IaC):** AWS CloudFormation template tự động hóa triển khai toàn bộ tài nguyên.
* **Môn học:** Cloud Computing (Điện toán đám mây - Đợt 1, 2026 - 2027)
* **Giảng viên hướng dẫn (GVHD):** ThS. Huỳnh Xuân Phụng
* **Thành viên nhóm (Tối đa 2 SV):**
  1. **Nguyễn Đình Khanh** - MSSV: `24110244` (Nhóm trưởng / Phụ trách Backend, Database & Cloud Services)
  2. **Võ Minh Quân** - MSSV: `24110312` (Thành viên / Phụ trách Network, Security & Infrastructure Setup)

---

## II. MỤC TIÊU TUẦN 1
Bám sát lộ trình Kế hoạch 4 tuần của đồ án môn học:
* **Mục tiêu cốt lõi Tuần 1:**
  1. Tìm hiểu các dịch vụ AWS bắt buộc: AWS Elastic Beanstalk / Lambda, Amazon RDS PostgreSQL, Amazon S3, Amazon EventBridge, AWS SNS, AWS CloudFormation.
  2. Thiết kế kiến trúc tổng thể hệ thống (Cloud Architecture Diagram) và mô hình Cơ sở dữ liệu quan hệ (ERD).
  3. Dựng hạ tầng mạng nền tảng trên AWS Learner Lab: VPC, Subnets (Public/Private), Internet Gateway, Route Tables, Security Groups.
  4. Tuân thủ quy định AWS Learner Lab: Region `us-east-1`, sử dụng `LabRole` / `LabInstanceProfile`, gắn Tag chuẩn (`Project=inventory-app`, `Owner=Khanh-Quan`).
  5. Xây dựng môi trường ứng dụng nền tảng (Flask API CRUD sản phẩm, nhập/xuất kho) và tạo S3 Bucket lưu trữ báo cáo.

---

## III. BẢNG PHÂN CÔNG CÔNG VIỆC VÀ THỜI GIAN CHI TIẾT (TỪ THỨ TƯ ĐẾN CHỦ NHẬT)

### 1. Phân công cho Sinh viên 1: Nguyễn Đình Khanh (MSSV: 24110244)
* **Vai trò:** Backend & Cloud Services Foundation

| Ngày | Thời gian | Nội dung công việc chi tiết | Công cụ / AI hỗ trợ | Số giờ | Kết quả / Minh chứng đạt được |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **Thứ Tư** | 20:00 - 23:00 | • Nghiên cứu tài liệu các dịch vụ AWS yêu cầu: Elastic Beanstalk, RDS PostgreSQL, S3, EventBridge, SNS, CloudFormation.<br>• Phác thảo sơ đồ kiến trúc đám mây tổng thể (Cloud Architecture Diagram) kết nối Web App, RDS, Lambda, SNS và S3. | AI hỗ trợ (ChatGPT / Claude) gợi ý mô hình kiến trúc chuẩn AWS Best Practices cho hệ thống kho | 3.0h | Sơ đồ phác thảo kiến trúc hệ thống Quản lý kho Cloud-native và luồng xử lý dữ liệu. |
| **Thứ Năm** | 13:30 - 16:30 | • Thiết kế cấu trúc CSDL PostgreSQL gồm 2 bảng: `products` (SKU, name, quantity, min_threshold) và `transactions` (product_id, type IN/OUT, quantity, created_at).<br>• Cài đặt môi trường Python Flask local & viết script DDL khởi tạo database `inventory_db`. | AI hỗ trợ (Amazon Q / ChatGPT) rà soát thiết kế quan hệ bảng và sinh mã DDL SQL chuẩn PostgreSQL | 3.0h | Khởi tạo thành công database `inventory_db` trên PostgreSQL local. |
| **Thứ Sáu** | 13:00 - 16:00 | • Xây dựng mã nguồn Backend (Flask API) xử lý logic nghiệp vụ: Quản lý sản phẩm (CRUD), Nhập/Xuất kho kiểm tra số lượng tồn thời gian thực.<br>• Thiết kế giao diện Web HTML5/Bootstrap 5 (`templates/index.html`) trực quan, hiển thị cảnh báo khi tồn kho chạm ngưỡng. | AI hỗ trợ (Antigravity / Claude) tối ưu thuật toán kiểm tra tồn kho và validation dữ liệu đầu vào | 3.0h | Ứng dụng Flask chạy ổn định tại `http://127.0.0.1:5000` với đầy đủ nghiệp vụ kho hàng. |
| **Thứ Bảy** | 09:00 - 11:30 | • Đăng nhập AWS Learner Lab (`us-east-1`), xác minh quyền hạn tài khoản với `LabRole`.<br>• Khởi tạo Amazon S3 Bucket lưu trữ báo cáo PDF/CSV định kỳ: `inventory-reports-us-east-1-24110244`.<br>• Cấu hình thuộc tính Bucket: Block Public Access, gán Tag bắt buộc `Project=inventory-app`, `Owner=Khanh-Quan`. | Thao tác trên AWS Management Console (`us-east-1`) | 2.5h | S3 Bucket sẵn sàng tiếp nhận file báo cáo định kỳ; có ảnh chụp minh chứng Console. |
| **Chủ Nhật** | 14:00 - 16:30 | • Soạn thảo tài liệu `README.md` hướng dẫn chạy ứng dụng và tài liệu kiến trúc Tuần 1.<br>• Rà soát mã nguồn, commit và push toàn bộ source code sạch lên GitHub repository.<br>• Họp nhóm tổng kết kết quả Tuần 1 và lập kế hoạch Tuần 2. | Git, GitHub, Markdown | 2.5h | • Repository GitHub được cập nhật đầy đủ mã nguồn & tài liệu.<br>• Biên bản họp nhóm Tuần 1. |


* **Tổng số giờ làm việc của Nguyễn Đình Khanh:** **14.0 giờ**.

---

### 2. Phân công cho Sinh viên 2: Võ Minh Quân (MSSV: 24110312)
* **Vai trò:** Network, Security & Infrastructure Setup

| Ngày | Thời gian | Nội dung công việc chi tiết | Công cụ / AI hỗ trợ | Số giờ | Kết quả / Minh chứng đạt được |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **Thứ Tư** | 20:00 - 23:00 | • Nghiên cứu các quy định & giới hạn bắt buộc của AWS Learner Lab: Hạn mức $50 budget, Region `us-east-1`, quy định dùng `LabRole`/`LabInstanceProfile`, giới hạn EC2 ($\le 9$ instances, $\le 32$ vCPU), EBS $\le 50$ GB (gp2/gp3).<br>• Thống nhất với SV1 về sơ đồ phân vùng mạng nền tảng (VPC & Subnets). | AI hỗ trợ (ChatGPT) tóm tắt các điểm cần lưu ý về hạn mức tài nguyên AWS Learner Lab | 3.0h | Bảng tổng hợp chi tiết giới hạn hạ tầng & danh mục dịch vụ AWS tuân thủ quy định phòng lab. |
| **Thứ Năm** | 14:00 - 17:00 | • Quy hoạch địa chỉ IP (CIDR Block) cho `inventory-vpc` (`10.0.0.0/16`).<br>• Thiết kế cấu trúc Multi-AZ (2 Public Subnets cho Web/Beanstalk, 2 Private Subnets cho RDS PostgreSQL Subnet Group).<br>• Thiết kế ma trận Security Groups 2-Tier: `inventory-web-sg` (mở 80, 5000) và `inventory-db-sg` (chỉ nhận traffic port 5432 từ Web SG). | AI hỗ trợ (Amazon Q) kiểm tra tính hợp lệ của quy tắc Security Group và định tuyến CIDR | 3.0h | Bản thiết kế chi tiết kiến trúc mạng VPC, Subnet, Route Table và Security Groups. |
| **Thứ Sáu** | 08:30 - 11:30 | • Triển khai thực tế trên AWS Learner Lab Console (`us-east-1`): Khởi tạo VPC `inventory-vpc`, Internet Gateway `inventory-igw`, cấu hình Route Tables và Subnet associations.<br>• Gán nhãn Tagging bắt buộc: `Project=inventory-app`, `Owner=Khanh-Quan`. | AWS Management Console & AWS CLI | 3.0h | Hạ tầng mạng VPC và 4 Subnets hoạt động chuẩn xác trên AWS Learner Lab. |
| **Thứ Bảy** | 14:00 - 16:30 | • Cấu hình và kiểm thử Security Groups: Tạo `inventory-web-sg` và `inventory-db-sg`, gắn rule tham chiếu SG ID bảo mật giữa Web Tier và DB Tier.<br>• Kiểm tra và xác minh quyền đính kèm IAM Instance Profile (`LabInstanceProfile`) phục vụ việc cấp quyền cho EC2/Beanstalk truy cập AWS S3/RDS sau này. | AWS Console & AWS CLI | 2.5h | Bảng Security Group được cấu hình chặt chẽ, kiểm tra tính tương thích với `LabInstanceProfile`. |
| **Chủ Nhật** | 09:00 - 11:30 | • Kiểm tra dọn dẹp, dừng các dịch vụ thử nghiệm nhằm bảo toàn budget $50 của Learner Lab.<br>• Chụp ảnh minh chứng Console và AWS CLI (thể hiện rõ Account ID, Region `us-east-1`, thời gian).<br>• Tổng hợp dữ liệu kỹ thuật hạ tầng vào báo cáo Tuần 1. | AWS CLI, Screenshot tool | 2.5h | • Bộ ảnh minh chứng Console/CLI đạt chuẩn yêu cầu GVHD.<br>• Báo cáo hạ tầng mạng hoàn thiện. |

* **Tổng số giờ làm việc của Võ Minh Quân:** **14.0 giờ**.

---

## IV. BÁO CÁO SỬ DỤNG TRỢ LÝ AI (AI ASSISTANCE REPORT)
Tuân thủ quy định cho phép sử dụng LLM/AI của giảng viên hướng dẫn, nhóm đã áp dụng các công cụ AI (**ChatGPT**, **Claude**, **Amazon Q Developer**, **Antigravity**) như sau:

| Nhiệm vụ / Hạng mục | Công cụ AI | Mục đích & Phạm vi hỗ trợ | Mức độ SV làm chủ & Giải trình |
| :--- | :---: | :--- | :--- |
| **Kiến trúc hệ thống** | Claude / ChatGPT | Tham khảo Best Practice kiến trúc kết hợp Web App, RDS, Lambda, SNS và S3. | SV tự phác thảo sơ đồ, lựa chọn dịch vụ phù hợp với ngân sách Learner Lab và giải thích được luồng dữ liệu. |
| **Thiết kế CSDL & Schema** | Amazon Q Developer | Gợi ý cú pháp DDL SQL tạo bảng `products`, `transactions` và ràng buộc khóa ngoại. | SV hiểu rõ quan hệ 1-N, cơ chế kiểm tra tồn kho và trực tiếp thực thi trên PostgreSQL. |
| **Backend Flask & Web UI** | Antigravity / Claude | Sinh mã boilerplate khung xử lý route, form nhập/xuất và flash message giao diện. | SV trực tiếp kiểm thử, viết logic nghiệp vụ kiểm tra xuất vượt tồn kho và cảnh báo mức tối thiểu. |
| **Hạ tầng Mạng & Security** | ChatGPT / Amazon Q | Kiểm tra tính đúng đắn của dải CIDR Subnet và cú pháp tham chiếu Source SG. | SV trực tiếp thao tác tạo VPC, Subnet, Route Table trên AWS Console và gán Tagging bằng tay. |

---

## V. TUÂN THỦ QUY ĐỊNH AWS LEARNER LAB
* **Region hoạt động:** Cố định **`us-east-1` (N. Virginia)** cho toàn bộ tài nguyên của nhóm.
* **Quyền IAM:** Sử dụng nghiêm ngặt **`LabRole`** và **`LabInstanceProfile`** sẵn có, không tạo IAM User / IAM Role mới.
* **Quy chuẩn Tagging (Bắt buộc):** tài nguyên đã khởi tạo (VPC, Subnets, Internet Gateway, Security Groups, S3 Bucket) đều được gắn 2 Tag:
  * `Project`: `inventory-app`
  * `Owner`: `Khanh-Quan`
* **Hạn mức tài nguyên & Quản lý ngân sách:**
  * Giới hạn EC2: Tuân thủ $\le 9$ instance và $\le 32$ vCPU (dự kiến tuần 2 dùng loại `t2.micro` / `t3.micro`).
  * Giới hạn EBS: Định mức $\le 50$ GB (gp2/gp3).
  * RDS Database: Lựa chọn `db.t3.micro`, Storage 20GB gp2/gp3, Single-AZ để tối ưu chi phí.
  * Bảo toàn Budget: Thực hiện kiểm tra, Stop/Delete các tài nguyên thử nghiệm sau mỗi buổi làm việc để duy trì chi phí tối thiểu trên ngân sách $50.

---

## VI. ĐÁNH GIÁ KẾT QUẢ TUẦN 1 VÀ KẾ HOẠCH TUẦN 2

### 1. Đánh giá kết quả Tuần 1:
* **Mức độ hoàn thành:** Hoàn thành công việc đặt ra cho Tuần 1.
* **Tổng số giờ làm việc:** **28.0 giờ** (Nguyễn Đình Khanh: 14.0h | Võ Minh Quân: 14.0h.
* **Kết quả bàn giao:**
  * Ứng dụng Flask CRUD và xử lý nhập/xuất kho chạy hoàn chỉnh trên local.
  * Hạ tầng VPC, Subnet Multi-AZ, Route Table và Security Groups 2-Tier dựng thành công trên AWS Learner Lab.
  * Bucket Amazon S3 `inventory-reports-us-east-1-24110244` được tạo sẵn sàng và gắn Tagging đầy đủ.
  * Toàn bộ mã nguồn, nhật ký công việc đã được đồng bộ lên GitHub.

### 2. Kế hoạch Tuần 2 (Triển khai các chức năng lõi trên AWS):
* **Triển khai CSDL Cloud:** Khởi tạo Amazon RDS PostgreSQL (`db.t3.micro`, Single-AZ) trong Private Subnets, cấu hình DB Subnet Group và liên kết `inventory-db-sg`.
* **Triển khai Web App Backend:** Đưa ứng dụng Flask lên AWS Elastic Beanstalk (hoặc EC2) trong Public Subnets, đính kèm `LabInstanceProfile` và kết nối với RDS PostgreSQL.
* **Kiểm thử chức năng lõi:** Kiểm thử toàn bộ API nhập/xuất kho trên môi trường Cloud thật, chuẩn bị tích hợp Lambda & SNS trong Tuần 3.
