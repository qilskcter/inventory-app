# NHẬT KÝ CÔNG VIỆC (WORKLOG) - TUẦN 3

---

## I. THÔNG TIN CHUNG
* **Tên dự án:** Hệ thống quản lý kho hàng và cảnh báo tồn kho
* **Phân nhóm môn học:** Domain Apps - Đợt 1, 2026–2027
* **Giảng viên hướng dẫn:** ThS. Huỳnh Xuân Phụng
* **Thành viên nhóm:**
  1. **Nguyễn Đình Khanh** - MSSV: `24110244` (Nhóm trưởng / Backend & Cloud Deployment)
  2. **Võ Minh Quân** - MSSV: `24110312` (Database, Security & Infrastructure)
* **AWS Region:** `us-east-1` (N. Virginia)
* **Môi trường hiện có:** Elastic Beanstalk `inventory-env-py312`, Amazon RDS PostgreSQL `inventory-db`

> Nhật ký này là kế hoạch dự kiến cho Tuần 3. Chỉ đánh dấu hoàn thành và ghi kết quả sau khi đã thực hiện, kiểm thử và lưu minh chứng tương ứng. Không ghi mật khẩu, access key, token hoặc thông tin xác thực vào repository hay ảnh chụp.

---

## II. MỤC TIÊU TUẦN 3: TÍCH HỢP, BẢO MẬT VÀ GIÁM SÁT

1. Hoàn thiện và kiểm thử tích hợp ứng dụng với RDS, rà soát luồng xử lý sản phẩm và giao dịch nhập/xuất.
2. Rà soát bảo mật cấu hình AWS: Security Groups, IAM instance profile, environment properties và việc quản lý bí mật.
3. Bổ sung giám sát CloudWatch phù hợp: xác nhận log ứng dụng/access/error, theo dõi metrics và thiết lập cảnh báo trong phạm vi quyền, chi phí cho phép.
4. Đánh giá khả năng tự động hóa bằng IaC. Nếu Learner Lab cho phép, xây dựng và kiểm tra template CloudFormation cho tài nguyên mới hoặc tài nguyên thử nghiệm; không cập nhật/thay thế RDS hay Environment đang dùng nếu chưa có kế hoạch và phê duyệt.
5. Kiểm thử hồi quy, ghi nhận kết quả và hoàn thiện tài liệu/minh chứng.

---

## III. BẢNG PHÂN CÔNG VÀ THỜI GIAN DỰ KIẾN (TỪ THỨ TƯ ĐẾN CHỦ NHẬT)

### 1. Nguyễn Đình Khanh (MSSV: 24110244)
* **Vai trò:** Backend, tích hợp ứng dụng và kiểm thử

| Ngày | Thời gian | Nội dung công việc dự kiến | Công cụ | Số giờ | Kết quả / minh chứng dự kiến |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **Thứ Tư** | 20:00–23:00 | • Rà soát luồng Flask → PostgreSQL trên Environment đang chạy.<br>• Kiểm tra các API sản phẩm, giao dịch nhập/xuất, lỗi dữ liệu và phản hồi database tạm thời.<br>• Lập danh sách tích hợp cần hoàn tất và các rủi ro trước khi thay đổi cấu hình AWS. | Flask, PostgreSQL, cURL, unit tests | 3.0h | Checklist tích hợp, kết quả kiểm thử hiện trạng và danh sách vấn đề cần xử lý. |
| **Thứ Năm** | 13:00–16:00 | • Thiết kế và triển khai xuất báo cáo tồn kho CSV an toàn (nếu nằm trong phạm vi tuần).<br>• Tích hợp lưu báo cáo vào S3 với bucket private, quyền tối thiểu và không bật public access.<br>• Kiểm thử định dạng, dữ liệu rỗng/lỗi và quyền truy cập; không đưa credential vào mã nguồn. | Python, boto3 (nếu được duyệt), S3, unit tests | 3.0h | Báo cáo mẫu được kiểm thử; log kết quả upload và ảnh cấu hình bucket private, nếu phần tích hợp được thực hiện. |
| **Thứ Sáu** | 13:30–16:30 | • Thiết kế luồng thông báo khi tồn kho chạm ngưỡng; thống nhất điều kiện gửi để tránh thông báo lặp không cần thiết.<br>• Nếu được cấp quyền và có email subscriber xác nhận, tích hợp SNS topic/subscription bằng cấu hình môi trường và kiểm thử bằng SKU thử nghiệm.<br>• Nếu không đủ quyền hoặc chưa có subscriber, ghi nhận blocker và hoàn thiện thiết kế/test local thay vì khẳng định đã gửi thông báo. | Flask, AWS SNS, AWS Console/SDK, tests | 3.0h | Kết quả kiểm thử cảnh báo; ảnh SNS subscription đã xác nhận (nếu có), không chụp địa chỉ/thông tin cá nhân không cần thiết. |
| **Thứ Bảy** | 09:00–11:30 | • Kiểm thử tích hợp và hồi quy trên staging hoặc trong cửa sổ được thống nhất.<br>• Xác nhận API và giao diện vẫn hoạt động sau thay đổi; rà soát log lỗi và phản hồi 5xx.<br>• Không tạo/xóa dữ liệu sản xuất tùy tiện; dùng SKU riêng và dọn dữ liệu thử nghiệm chỉ khi đã được xác nhận. | cURL, browser, CloudWatch Logs, tests | 2.5h | Bảng test case với request/response và ảnh kết quả; danh sách dữ liệu thử nghiệm được xử lý an toàn. |
| **Chủ Nhật** | 14:00–16:30 | • Rà soát code, dependency, cấu hình môi trường và tài liệu tích hợp.<br>• Tổng hợp minh chứng, cập nhật nhật ký và báo cáo; ghi rõ chức năng đã làm, chưa làm và giới hạn lab.<br>• Lập đề xuất công việc tuần 4. | Git, Markdown, AWS Console | 2.5h | Tài liệu cập nhật, diff được rà soát và kế hoạch tuần tiếp theo. |

* **Tổng số giờ dự kiến của Nguyễn Đình Khanh:** **14.0 giờ**.

### 2. Võ Minh Quân (MSSV: 24110312)
* **Vai trò:** Bảo mật, giám sát và hạ tầng

| Ngày | Thời gian | Nội dung công việc dự kiến | Công cụ | Số giờ | Kết quả / minh chứng dự kiến |
| :--- | :---: | :--- | :--- | :---: | :--- |
| **Thứ Tư** | 20:00–23:00 | • Rà soát inbound/outbound rules của `inventory-web-sg` và `inventory-db-sg`, xác nhận PostgreSQL chỉ nhận từ Web SG.<br>• Kiểm tra profile/role thực tế gắn với Beanstalk và quyền cần thiết; không tự sửa role do Learner Lab quản lý nếu chưa được phép.<br>• Kiểm tra trạng thái xoay vòng mật khẩu DB đã bị lộ trước đó; cập nhật an toàn nếu được chủ sở hữu cho phép. | AWS Console, IAM, VPC, RDS | 3.0h | Bảng rà soát quyền và Security Group; ghi nhận thay đổi hoặc blocker, không ghi secret. |
| **Thứ Năm** | 14:00–17:00 | • Xác nhận CloudWatch nhận `web.stdout.log`, Nginx access/error và log Beanstalk; đối chiếu retention.<br>• Theo dõi metrics RDS/Environment trong khoảng thời gian xác định.<br>• Đánh giá và cấu hình cảnh báo chi phí thấp, ví dụ lỗi 5xx hoặc Health không tốt, nếu metric, quyền và chi phí cho phép. | CloudWatch Logs, Metrics, Alarms | 3.0h | Ảnh log/metrics và cấu hình cảnh báo (nếu được triển khai); ghi rõ khoảng thời gian quan sát và giới hạn. |
| **Thứ Sáu** | 08:30–11:30 | • Đánh giá TLS/HTTPS cho endpoint ứng dụng và xác định yêu cầu chứng chỉ/domain/Load Balancer.<br>• Không bật Load Balancer hoặc tạo tài nguyên có chi phí phát sinh nếu chưa được nhóm/giảng viên đồng ý.<br>• Rà soát environment properties để đảm bảo không lưu bí mật trong Git, bundle hoặc log. | Elastic Beanstalk, ACM, IAM, AWS Console | 3.0h | Đề xuất HTTPS khả thi hoặc ghi nhận giới hạn lab; checklist quản lý secret. |
| **Thứ Bảy** | 14:00–16:30 | • Đánh giá khả năng dùng CloudFormation trong Learner Lab và phạm vi tài nguyên có thể tạo.<br>• Nếu được phép, viết/validate template cho tài nguyên mới hoặc môi trường thử nghiệm (ví dụ SNS/S3/logging); kiểm tra trước thay đổi và tránh import/replace RDS hiện hữu.<br>• Nếu bị giới hạn quyền, lưu kết quả đánh giá và sơ đồ thủ công thay cho triển khai stack. | CloudFormation, AWS CLI/Console, YAML | 2.5h | Template được validate hoặc biên bản giới hạn/quyết định chưa triển khai; không áp dụng stack có nguy cơ gây downtime. |
| **Chủ Nhật** | 09:00–11:30 | • Kiểm tra Tags, quyền, logs, metrics và chi phí tài nguyên sau các thay đổi được duyệt.<br>• Chụp ảnh minh chứng đã loại bỏ secret/PII không cần thiết.<br>• Tổng hợp phần bảo mật/giám sát và đề xuất xử lý tồn đọng. | AWS Console, CloudWatch, Markdown | 2.5h | Minh chứng đã rà soát, bảng tồn đọng và khuyến nghị tuần 4. |

* **Tổng số giờ dự kiến của Võ Minh Quân:** **14.0 giờ**.

---

## IV. DANH SÁCH CÔNG VIỆC CẦN LÀM

### Giai đoạn 1: Tích hợp ứng dụng
- [x] Kiểm tra API và giao diện kết nối Environment hiện tại tới đúng RDS/database.
- [x] Kiểm thử nhập/xuất kho, ngưỡng tồn, giao dịch đồng thời và các mã lỗi dự kiến.
- [x] Đánh giá xuất báo cáo CSV và tích hợp S3 private; chỉ đánh dấu hoàn thành sau khi upload/read được đối tượng thử nghiệm.
- [ ] Đánh giá/cài đặt SNS cảnh báo tồn kho; xác nhận subscription trước khi gửi thông báo.

### Giai đoạn 2: Bảo mật
- [ ] Xác nhận không có mật khẩu, token, access key hoặc dữ liệu nhạy cảm trong Git, ZIP deploy, log và ảnh minh chứng.
- [ ] Rà soát và xử lý việc thay mật khẩu DB đã lộ; cập nhật Beanstalk properties, xác nhận Health `Ok` và kết nối DB thành công.
- [ ] Xác nhận `inventory-db-sg` chỉ cho phép PostgreSQL từ Security Group Web; không mở DB cho `0.0.0.0/0`.
- [ ] Rà soát instance profile/role theo least privilege; không thay đổi IAM lab nếu chưa được cấp quyền.
- [ ] Đánh giá phương án HTTPS và chi phí/điều kiện chứng chỉ; chỉ triển khai sau khi được chấp thuận.

### Giai đoạn 3: CloudWatch và giám sát
- [ ] Xác nhận log groups của Beanstalk có log mới; kiểm tra ứng dụng, access và error logs.
- [ ] Rà soát retention và lifecycle log groups.
- [ ] Ghi lại metrics RDS/Environment theo khoảng thời gian và không suy rộng từ một lần quan sát.
- [ ] Đánh giá hoặc tạo alarm phù hợp, xác nhận trạng thái alarm và hành động thông báo nếu có.

### Giai đoạn 4: Tự động hóa / IaC (nếu khả thi)
- [ ] Kiểm tra quyền CloudFormation và quy định Learner Lab trước khi tạo stack.
- [ ] Chọn phạm vi an toàn: tài nguyên mới hoặc môi trường thử nghiệm, không thay thế RDS/Environment hiện hữu.
- [ ] Validate template, xem trước thay đổi và kiểm tra kết quả sau triển khai.
- [ ] Nếu không đủ quyền/thời gian, ghi rõ lý do chưa triển khai và lưu thiết kế IaC dự kiến; không khai báo là đã tự động hóa.

### Giai đoạn 5: Hồi quy và hoàn thiện
- [ ] Chạy unit tests và kiểm thử API/Web sau thay đổi.
- [ ] Kiểm tra Environment Health, database connection và CloudWatch sau deployment.
- [ ] Hoàn thiện ảnh minh chứng trong `documents/week_3/screenshots/`, che thông tin nhạy cảm.
- [ ] Cập nhật work log/báo cáo với kết quả thực tế, thời gian thực tế và công việc còn tồn đọng.

---

## V. QUY ƯỚC MINH CHỨNG

Ảnh Tuần 3 dự kiến lưu trong `documents/week_3/screenshots/`. Chỉ thêm ảnh sau khi thao tác thực tế; tên dưới đây là gợi ý:

| Tên file gợi ý | Nội dung |
| :--- | :--- |
| `46_week3_integration_test.png` | API/UI sau kiểm thử tích hợp, không để lộ dữ liệu cá nhân. |
| `47_week3_security_groups.png` | Inbound rule của Web/DB SG thể hiện giới hạn nguồn kết nối. |
| `48_week3_cloudwatch_logs.png` | Log groups và log events mới, không lộ IP nếu không cần. |
| `49_week3_cloudwatch_metrics_alarm.png` | Metrics/alarm và khoảng thời gian quan sát. |
| `50_week3_iac_validation.png` | Kết quả validate template hoặc bằng chứng đánh giá quyền/giới hạn khi không thể triển khai. |

Không chụp hoặc commit mật khẩu, access key, token, giá trị environment secret, email cá nhân hay nội dung log không liên quan.

---

## VI. NGUYÊN TẮC AN TOÀN VÀ QUẢN LÝ CHI PHÍ

* Giữ Region `us-east-1`, tuân theo giới hạn Learner Lab và dùng role/profile được cấp.
* Duy trì RDS private; không mở cổng PostgreSQL ra Internet để thử nghiệm.
* Không chạy IaC trực tiếp lên tài nguyên hiện hữu nếu Change Set cho thấy replacement/deletion hoặc có nguy cơ mất dữ liệu.
* Dùng dữ liệu thử nghiệm riêng; xác nhận trước khi xóa bất kỳ bản ghi nào đang tồn tại.
* Không tạo Load Balancer, NAT Gateway, alarm có phí hoặc tài nguyên dài hạn nếu chưa kiểm tra chi phí và được nhóm chấp thuận.
* Sau khi hoàn thành, rà soát tài nguyên thử nghiệm và dừng/xóa chỉ những tài nguyên đã được nhóm xác nhận có thể dọn.

---

## VII. ĐÁNH GIÁ VÀ BÀN GIAO CUỐI TUẦN

Phần này được cập nhật sau khi hoàn thành Tuần 3:

* **Tích hợp hoàn tất:** Chưa cập nhật.
* **Bảo mật đã rà soát/xử lý:** Chưa cập nhật.
* **CloudWatch Logs/Metrics/Alarms:** Chưa cập nhật.
* **IaC:** Chưa cập nhật; triển khai phụ thuộc quyền và giới hạn Learner Lab.
* **Kiểm thử và minh chứng:** Chưa cập nhật.
* **Việc chuyển sang Tuần 4:** Chưa cập nhật.
