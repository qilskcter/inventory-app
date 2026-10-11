# ==============================================================================
# Script PowerShell khởi tạo và cấu hình Security Groups cho dự án inventory-app
# Thực hiện: Võ Minh Quân (MSSV: 24110312) - Tuần 1 (Thứ Bảy)
# Môi trường: AWS Learner Lab - Region: us-east-1
# ==============================================================================

$Region = "us-east-1"
$ProjectTag = "inventory-app"
$OwnerTag = "Khanh-Quan"

Write-Host "=== [1/4] Kiểm tra Identity AWS Learner Lab ===" -ForegroundColor Cyan
aws sts get-caller-identity --output table --region $Region --no-cli-pager

Write-Host "`n=== [2/4] Tìm kiếm VPC ID của 'inventory-vpc' ===" -ForegroundColor Cyan
$VpcId = aws ec2 describe-vpcs `
  --filters "Name=tag:Name,Values=inventory-vpc" `
  --query "Vpcs[0].VpcId" `
  --output text `
  --region $Region

if (-not $VpcId -or $VpcId -eq "None") {
    Write-Host "LỖI: Không tìm thấy VPC có Name=inventory-vpc trong region $Region!" -ForegroundColor Red
    exit 1
}
Write-Host "Đã tìm thấy VPC ID: $VpcId" -ForegroundColor Green

Write-Host "`n=== [3/4] Khởi tạo & Cấu hình Security Group cho Web Tier (inventory-web-sg) ===" -ForegroundColor Cyan
$WebSgId = aws ec2 describe-security-groups `
  --filters "Name=group-name,Values=inventory-web-sg" "Name=vpc-id,Values=$VpcId" `
  --query "SecurityGroups[0].GroupId" `
  --output text `
  --region $Region 2>$null

if (-not $WebSgId -or $WebSgId -eq "None") {
    Write-Host "Đang tạo mới inventory-web-sg..."
    $WebSgId = aws ec2 create-security-group `
      --group-name inventory-web-sg `
      --description "Security Group cho Web Tier (Flask App / Elastic Beanstalk)" `
      --vpc-id $VpcId `
      --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=inventory-web-sg},{Key=Project,Value=$ProjectTag},{Key=Owner,Value=$OwnerTag}]" `
      --query "GroupId" `
      --output text `
      --region $Region
    Write-Host "Đã tạo inventory-web-sg: $WebSgId" -ForegroundColor Green
} else {
    Write-Host "inventory-web-sg đã tồn tại: $WebSgId" -ForegroundColor Yellow
}

Write-Host "Cấu hình Inbound Rules cho inventory-web-sg (Port 80, 5000, 443)..."
aws ec2 authorize-security-group-ingress --group-id $WebSgId --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $Region 2>$null
aws ec2 authorize-security-group-ingress --group-id $WebSgId --protocol tcp --port 5000 --cidr 0.0.0.0/0 --region $Region 2>$null
aws ec2 authorize-security-group-ingress --group-id $WebSgId --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $Region 2>$null

Write-Host "`n=== [4/4] Khởi tạo & Cấu hình Security Group cho Database Tier (inventory-db-sg) ===" -ForegroundColor Cyan
$DbSgId = aws ec2 describe-security-groups `
  --filters "Name=group-name,Values=inventory-db-sg" "Name=vpc-id,Values=$VpcId" `
  --query "SecurityGroups[0].GroupId" `
  --output text `
  --region $Region 2>$null

if (-not $DbSgId -or $DbSgId -eq "None") {
    Write-Host "Đang tạo mới inventory-db-sg..."
    $DbSgId = aws ec2 create-security-group `
      --group-name inventory-db-sg `
      --description "Security Group cho RDS PostgreSQL Database Tier" `
      --vpc-id $VpcId `
      --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=inventory-db-sg},{Key=Project,Value=$ProjectTag},{Key=Owner,Value=$OwnerTag}]" `
      --query "GroupId" `
      --output text `
      --region $Region
    Write-Host "Đã tạo inventory-db-sg: $DbSgId" -ForegroundColor Green
} else {
    Write-Host "inventory-db-sg đã tồn tại: $DbSgId" -ForegroundColor Yellow
}

Write-Host "Cấu hình Security Group Chaining: Port 5432 chỉ cho phép Source từ $WebSgId..."
aws ec2 authorize-security-group-ingress --group-id $DbSgId --protocol tcp --port 5432 --source-group $WebSgId --region $Region 2>$null

Write-Host "`n=== [Xác minh] Kiểm tra IAM Instance Profile (LabInstanceProfile) ===" -ForegroundColor Cyan
aws iam get-instance-profile --instance-profile-name LabInstanceProfile --region $Region --output table --no-cli-pager

Write-Host "`n==============================================================================" -ForegroundColor Green
Write-Host "HOÀN TẤT CẤU HÌNH HẠ TẦNG BẢO MẬT TUẦN 1!" -ForegroundColor Green
Write-Host "VPC ID:        $VpcId"
Write-Host "Web SG ID:     $WebSgId (Port 80, 5000, 443 từ 0.0.0.0/0)"
Write-Host "DB SG ID:      $DbSgId (Port 5432 chỉ từ $WebSgId)"
Write-Host "Tagging:       Project=$ProjectTag | Owner=$OwnerTag"
Write-Host "InstanceProfile: LabInstanceProfile sẵn sàng cho Beanstalk/EC2 ở Tuần 2"
Write-Host "==============================================================================" -ForegroundColor Green
