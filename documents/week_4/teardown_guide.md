# Hướng dẫn dọn tài nguyên sau nghiệm thu

## 1. Phạm vi và trách nhiệm

- Dự án: inventory-app.
- Region: us-east-1.
- Môi trường chung: AWS đang chạy ứng dụng của Nguyễn Đình Khanh.
- Võ Minh Quân: chuẩn bị hướng dẫn, đối chiếu tài nguyên và tổng hợp kết quả.
- Nguyễn Đình Khanh: phối hợp xác nhận và thao tác trong tài khoản AWS.
- Trạng thái tài liệu: kế hoạch; chưa thực hiện dọn tài nguyên.

Chỉ thực hiện sau khi nghiệm thu và cả hai thành viên xác nhận.
Không áp dụng tài liệu này để xóa tài nguyên trong tài khoản thực hành
riêng của Quân.

## 2. Kết quả đã xác minh

| Hạng mục | Kết quả |
|---|---|
| Beanstalk | inventory-env-py312 |
| RDS | inventory-db |
| Manual snapshot | inventory-db-final-snapshot |
| Trạng thái snapshot | Available |
| Thời gian tạo snapshot | 01/11/2026, 20:18 (UTC+7) |
| Kiểm thử khôi phục | Chưa thực hiện |
| CloudWatch alarms | CPU RDS > 80%; tỷ lệ HTTP 5xx > 1% |
| Retention log ứng dụng | 7 ngày |
| S3 Lifecycle | inventory_reports/ và tag cleanup=true; hết hạn current version sau 7 ngày |

Snapshot chỉ phản ánh dữ liệu tại thời điểm tạo.
Nếu có thay đổi cần giữ sau demo, tạo snapshot mới và đợi Available
trước khi xóa DB.

## 3. Điều kiện trước khi dọn

- [ ] Đã nghiệm thu và không còn cần chạy demo.
- [ ] Đã lưu mã nguồn, báo cáo, ảnh và video ngoài tài nguyên sắp xóa.
- [ ] Đã tải các báo cáo S3 cần giữ.
- [ ] Đã xác nhận đúng tài khoản, Region và từng tài nguyên.
- [ ] Đã lập danh sách tài nguyên và phụ thuộc.
- [ ] Đã xác nhận bản backup cần giữ và thời hạn lưu.
- [ ] Cả hai thành viên đồng ý danh sách cần dọn.

## 4. Thứ tự thực hiện dự kiến

### Bước 1 — Dừng sử dụng ứng dụng

Thông báo kết thúc demo, ngừng kiểm thử và ghi nhận dữ liệu cuối.
Tạo thêm backup nếu cần giữ các thay đổi mới.

### Bước 2 — Dọn Elastic Beanstalk

Xác nhận environment cần terminate.
Thực hiện qua Elastic Beanstalk; không tự xóa EC2 do environment quản lý.
Kiểm tra các tài nguyên còn lại sau khi terminate.

Environment inventory-env cũ chưa được kiểm kê đầy đủ.
Không tự đưa vào danh sách xóa khi chưa xác nhận mục đích sử dụng.

### Bước 3 — Dọn RDS

Chỉ xóa inventory-db khi đã xác nhận không còn ứng dụng sử dụng,
backup cần giữ ở trạng thái Available và được cả nhóm đồng ý.

Kiểm tra tùy chọn final snapshot và automated backups trước khi xác nhận.
Không xóa bản snapshot cần giữ.
Ghi lại tên backup, thời hạn giữ và người chịu trách nhiệm.

### Bước 4 — Dọn S3

Chỉ xóa object thử nghiệm đã được đối chiếu.
Giữ báo cáo và minh chứng cần nộp.

Lifecycle hiện chỉ áp dụng cho object có cả:
- Prefix inventory_reports/
- Tag cleanup=true

Không coi Lifecycle là bằng chứng mọi báo cáo sẽ tự được xóa.
Kiểm tra versioning trước khi quyết định dọn bucket.

### Bước 5 — Dọn tài nguyên giám sát và thông báo

Sau khi không còn cần theo dõi hệ thống:
- Xóa alarms đã xác nhận không còn sử dụng.
- Lưu log cần làm minh chứng trước khi xóa log groups.
- Chỉ xóa SNS topic/subscriptions khi không còn ứng dụng hay alarm sử dụng.

### Bước 6 — Rà soát tài nguyên còn lại

Kiểm tra EC2, EBS, Elastic IP, snapshots và tài nguyên mạng.
Chỉ xử lý tài nguyên đã xác định chủ sở hữu, mục đích và phụ thuộc.
Không sửa hoặc xóa role/policy do Learner Lab quản lý.

## 5. Biên bản thực hiện

Tại thời điểm lập tài liệu, nhóm chưa thực hiện dừng hoặc xóa
tài nguyên AWS. Hệ thống được giữ lại để kiểm thử, demo và nghiệm thu.

Snapshot inventory-db-final-snapshot đã đạt trạng thái Available.
Việc tạo snapshot là bước chuẩn bị backup, không phải thao tác dọn
tài nguyên và chưa chứng minh khả năng khôi phục.

Sau nghiệm thu, nhóm sẽ ghi từng thao tác thực tế vào bảng dưới đây:

| Tài nguyên | Hành động được thống nhất | Người thao tác | Người đối chiếu | Thời điểm | Kết quả / minh chứng |
|---|---|---|---|---|---|
| Chưa thực hiện | Chưa có thao tác dừng/xóa | — | — | — | Hệ thống được giữ để nghiệm thu |

## 6. Xác nhận của các thành viên

Tài liệu này là hướng dẫn dự kiến, chưa phải xác nhận cho phép
dừng hoặc xóa tài nguyên.

Trước khi thực hiện, hai thành viên phải thống nhất danh sách
tài nguyên, dữ liệu cần giữ, bản backup và thời điểm thực hiện.

| Thành viên | Trách nhiệm | Trạng thái xác nhận |
|---|---|---|
| Nguyễn Đình Khanh | Đối chiếu môi trường ứng dụng, phối hợp thao tác AWS | Chưa xác nhận thực hiện dọn tài nguyên |
| Võ Minh Quân | Chuẩn bị hướng dẫn, đối chiếu backup và tổng hợp biên bản | Chưa xác nhận thực hiện dọn tài nguyên |

Ngày, giờ thống nhất thực hiện: Chưa xác định.

Sau khi hoàn tất, cả hai thành viên kiểm tra kết quả tại Mục 5
và bổ sung xác nhận thực tế.
