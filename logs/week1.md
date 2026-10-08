# NHẬT KÝ CÔNG VIỆC (WORKLOG) - TUẦN 1

---

## I. THÔNG TIN CHUNG
* **Tên dự án:** Hệ thống quản lý kho hàng (inventory) với cảnh báo tồn kho
* **Phân nhóm môn học:** Domain Apps - Đợt 1 (2026 - 2027)
* **Giảng viên hướng dẫn (GVHD):** ThS. Huỳnh Xuân Phụng
* **Thành viên nhóm (Tối đa 2 SV):**
  1. **Nguyễn Đình Khanh** - MSSV: `24110244` (Nhóm trưởng / Backend & Cloud Foundation)
  2. **Võ Minh Quân** - MSSV: `24110312` (Thành viên / Network & Infrastructure Setup)

---

## II. MỤC TIÊU TUẦN 1
Theo kế hoạch 4 tuần của đồ án, Tuần 1 tập trung vào các công việc nền tảng:
1. Tìm hiểu các dịch vụ AWS bắt buộc: AWS Elastic Beanstalk / Lambda, Amazon RDS PostgreSQL, Amazon S3, Amazon EventBridge, AWS SNS, AWS CloudFormation.
2. Thiết kế kiến trúc tổng thể hệ thống (Cloud Architecture Diagram) & mô hình Cơ sở dữ liệu.
3. Dựng hạ tầng nền tảng trên AWS Learner Lab (VPC, Subnets, Security Groups, IAM LabRole/LabInstanceProfile, S3 Bucket).
4. Thực hiện quy định bắt buộc về gắn Tag tài nguyên (`Project`, `Owner`) và chuẩn hóa môi trường phát triển local (Flask Backend + PostgreSQL local).

---

## III. BẢNG PHÂN CÔNG CÔNG VIỆC VÀ THỜI GIAN CHI TIẾT (TỪ THỨ TƯ ĐẾN CHỦ NHẬT)

### 1. Phân công cho Sinh viên 1: Nguyễn Đình Khanh (MSSV: 24110244)

| Ngày | Thời gian | Nội dung công việc chi tiết | Công cụ / AI hỗ trợ | Số giờ | Kết quả / Minh chứng đạt được |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **Thứ Tư** | 20:00 - 23:00 | • Nghiên cứu tài liệu các dịch vụ AWS: Elastic Beanstalk, RDS, S3, SNS, EventBridge.<br>• Phác thảo sơ đồ kiến trúc tổng thể hệ thống (Architecture Diagram) kết nối giữa các dịch vụ cloud. | AI hỗ trợ (ChatGPT / Claude) gợi ý mô hình kiến trúc chuẩn AWS Best Practices | 3.0h | Sơ đồ kiến trúc sơ bộ hệ thống Quản lý kho Cloud-native. |
| **Thứ Năm** | 12:30 - 15:00 | • Thiết kế cấu trúc CSDL PostgreSQL gồm 2 bảng chính: `products` (SKU, tên, tồn kho, min_threshold) và `transactions` (nhập/xuất).<br>• Cài đặt môi trường Python Flask & kết nối PostgreSQL local. | AI hỗ trợ (Amazon Q / ChatGPT) rà soát thiết kế ERD và sinh mã SQL schema DDL | 2.5h | Khởi tạo thành công database `inventory_db` trên PostgreSQL local. |
| **Thứ Sáu** | 13:00 - 16:00 | • Xây dựng mã nguồn Backend (Flask API) xử lý CRUD sản phẩm, logic Nhập/Xuất kho theo thời gian thực.<br>• Thiết kế giao diện HTML5/Bootstrap 5 (`templates/index.html`) hiển thị bảng tồn kho & nút nhập xuất. | AI hỗ trợ (Antigravity / Copilot) viết hàm helper xử lý validation dữ liệu | 3.0h | Ứng dụng chạy thành công tại `http://127.0.0.1:5000` với đầy đủ chức năng cốt lõi. |
| **Thứ Bảy** | 09:00 - 11:00 | • Đăng nhập AWS Learner Lab (`us-east-1`), xác minh quyền hạn của `LabRole`.<br>• Khởi tạo Amazon S3 Bucket lưu trữ báo cáo định kỳ: `inventory-reports-us-east-1-24110244`.<br>• Gắn Tag chuẩn cho S3: `Project=inventory-app`, `Owner=Khanh-Quan`. | Thao tác trực tiếp trên AWS Management Console | 2.0h | S3 Bucket được tạo thành công với cấu hình private và đúng Tagging quy định. |
| **Chủ Nhật** | 14:00 - 16:30 | • Tối ưu hóa mã nguồn, viết file `README.md` chi tiết và cấu trúc dự án chuẩn Git.<br>• Push toàn bộ source code Tuần 1 lên GitHub repository.<br>• Họp nhóm tổng kết kết quả Tuần 1. | Tự thực hiện & kiểm thử | 2.5h | • Git commit/push sạch sẽ.<br>• Ảnh chụp AWS Console S3 có Account ID & Region. |

* **Tổng số giờ làm việc của Nguyễn Đình Khanh:** **13.5 giờ** (Đạt yêu cầu $\ge 8$ giờ/tuần)

---

### 2. Phân công cho Sinh viên 2: Võ Minh Quân (MSSV: 24110312)

| Ngày | Thời gian | Nội dung công việc chi tiết | Công cụ / AI hỗ trợ | Số giờ | Kết quả / Minh chứng đạt được |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **Thứ Tư** | 20:00 - 23:00 | • Tìm hiểu các quy định & giới hạn của AWS Learner Lab (Region `us-east-1`/`us-west-2`, quy định dùng `LabRole`, giới hạn EC2/EBS, vCPU).<br>• Thống nhất với SV1 về sơ đồ phân vùng mạng (VPC & Subnets). | AI hỗ trợ (ChatGPT) tóm tắt các điểm cần lưu ý về hạn mức tài nguyên AWS Learner Lab | 3.0h | Bảng tổng hợp các giới hạn hạ tầng & danh sách dịch vụ AWS tuân thủ quy định. |
| **Thứ Năm** | 14:00 - 17:00 | • Quy hoạch địa chỉ IP (CIDR block) cho VPC (`10.0.0.0/16`).<br>• Thiết kế các Subnet (Public Subnet cho Web/App Tier, Private Subnet cho RDS Database Tier).<br>• Thiết kế quy tắc Security Groups (SG): Web SG (allow HTTP 80/5000), DB SG (allow PostgreSQL 5432 từ Web SG). | AI hỗ trợ (Amazon Q) kiểm tra tính hợp lệ của quy tắc Security Group | 3.0h | Tài liệu thiết kế chi tiết hạ tầng mạng VPC và Security Groups. |
| **Thứ Sáu** | 08:30 - 11:30 | • Triển khai thực tế trên AWS Learner Lab Console: Tạo VPC `inventory-vpc`, Internet Gateway, Route Tables.<br>• Gắn Tag chuẩn cho tất cả tài nguyên vừa tạo: `Project=inventory-app`, `Owner=Khanh-Quan`. | Thao tác trên AWS Management Console (`us-east-1`) | 3.0h | Hạ tầng VPC & Subnet sẵn sàng trên AWS với đầy đủ Tagging bắt buộc. |
| **Thứ Bảy** | 14:00 - 16:30 | • Cấu hình Security Groups thử nghiệm kết nối giao tiếp giữa Web Tier và Database Tier.<br>• Kiểm tra quyền gắn IAM Instance Profile (`LabInstanceProfile`) phục vụ việc đính kèm quyền cho EC2/Beanstalk sau này. | AI hỗ trợ giải thích các mã lỗi kết nối VPC / Security Group | 2.5h | Bảng Security Group được khởi tạo chính xác, cho phép truy cập theo đúng kịch bản bảo mật. |
| **Chủ Nhật** | 09:00 - 11:30 | • Kiểm tra dọn dẹp/dừng các tài nguyên không dùng đến để bảo tồn AWS Credit.<br>• Chụp ảnh minh chứng AWS CLI/Console (rõ Account ID, Region `us-east-1`, Timestamp).<br>• Tổng hợp thông tin nhật ký công việc hạ tầng vào báo cáo. | AWS CLI & AWS Console | 2.5h | • File lưu trữ ảnh minh chứng Console.<br>• Báo cáo hạ tầng mạng Tuần 1 hoàn chỉnh. |

* **Tổng số giờ làm việc của Võ Minh Quân:** **14.0 giờ** (Đạt yêu cầu $\ge 8$ giờ/tuần)

---

## IV. BÁO CÁO SỬ DỤNG TRỢ LÝ AI (AI ASSISTANCE REPORT)
Nhóm có sử dụng các công cụ LLM/AI (**ChatGPT**, **Claude**, **Amazon Q Developer**, **Antigravity**) trong quá trình nghiên cứu và thực hiện Tuần 1. Chi tiết như sau:

**Phần việc có AI hỗ trợ:**
   * **Tham khảo & Thiết kế:** Gợi ý sơ đồ kiến trúc đám mây chuẩn AWS cho bài toán quản lý kho kết hợp EventBridge & Lambda & SNS.
   * **Sinh mã nguồn (Code Generation):** Hỗ trợ sinh khung code DDL SQL cho PostgreSQL local và mã nguồn boilerplate Flask API.
   * **Gỡ lỗi & Cấu hình:** Hỗ trợ kiểm tra cú pháp Security Group CIDR và rà soát lỗi kết nối PostgreSQL.


---

## V. TUÂN THỦ QUY ĐỊNH AWS LEARNER LAB
* **Region sử dụng:** `us-east-1` (N. Virginia).
* **Quyền IAM:** Sử dụng `LabRole` và `LabInstanceProfile` có sẵn của tài khoản Learner Lab (Không tạo mới IAM User/Role).
* **Tagging:** 100% tài nguyên đã tạo (S3 Bucket, VPC, Subnets, Security Groups) đều được đính kèm Tag:
  * `Project`: `inventory-app`
  * `Owner`: `Khanh-Quan`
* **Quản lý tài nguyên & Chi phí:** Toàn bộ tài nguyên thử nghiệm đều được kiểm tra, dừng hoặc xóa sau buổi làm việc nhằm duy trì mức chi phí $0.00 / trong hạn mức cấp của bài lab.

---

## VI. ĐÁNH GIÁ KẾT QUẢ TUẦN 1 VÀ KẾ HOẠCH TUẦN 2

### 1. Đánh giá Tuần 1:
* **Mức độ hoàn thành:** **100%** kế hoạch Tuần 1.
* **Tổng số giờ toàn nhóm:** **27.5 giờ** (Nguyễn Đình Khanh: 13.5h | Võ Minh Quân: 14.0h).
* **Kết quả đạt được:**
  * App Flask + PostgreSQL local chạy ổn định, cho phép quản lý sản phẩm và nhập/xuất kho.
  * Đã dựng xong VPC, Subnets, Security Group và S3 Bucket trên AWS Learner Lab với đầy đủ Tagging.
  * Có đầy đủ minh chứng Git repo và screenshot Console.

### 2. Kế hoạch Tuần 2:
* **Triển khai CSDL Cloud:** Đưa cơ sở dữ liệu lên Amazon RDS PostgreSQL (`us-east-1`) trên AWS Learner Lab.
* **Triển khai Backend Cloud:** Triển khai ứng dụng Flask Backend lên AWS Elastic Beanstalk (hoặc EC2 / Lambda).
* **Kết nối & Kiểm thử:** Cấu hình ứng dụng kết nối với RDS PostgreSQL, kiểm thử các API quản lý kho hàng trên môi trường AWS thật.