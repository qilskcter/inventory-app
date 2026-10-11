#!/usr/bin/env bash
# ==============================================================================
# Script khởi tạo và cấu hình Security Groups cho dự án inventory-app
# Thực hiện: Võ Minh Quân (MSSV: 24110312) - Tuần 1 (Thứ Bảy)
# Môi trường: AWS Learner Lab - Region: us-east-1
# ==============================================================================

set -euo pipefail

REGION="us-east-1"
PROJECT_TAG="inventory-app"
OWNER_TAG="Khanh-Quan"

echo "=== [1/4] Kiểm tra Identity AWS Learner Lab ==="
aws sts get-caller-identity --output table --region "$REGION" --no-cli-pager

echo ""
echo "=== [2/4] Tìm kiếm VPC ID của 'inventory-vpc' ==="
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=inventory-vpc" \
  --query "Vpcs[0].VpcId" \
  --output text \
  --region "$REGION")

if [ -z "$VPC_ID" ] || [ "$VPC_ID" == "None" ]; then
  echo "LỖI: Không tìm thấy VPC có Name=inventory-vpc trong region $REGION!"
  exit 1
fi
echo "Đã tìm thấy VPC ID: $VPC_ID"

echo ""
echo "=== [3/4] Khởi tạo & Cấu hình Security Group cho Web Tier (inventory-web-sg) ==="
# Kiểm tra nếu SG đã tồn tại
WEB_SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=inventory-web-sg" "Name=vpc-id,Values=$VPC_ID" \
  --query "SecurityGroups[0].GroupId" \
  --output text \
  --region "$REGION" 2>/dev/null || echo "None")

if [ -z "$WEB_SG_ID" ] || [ "$WEB_SG_ID" == "None" ]; then
  echo "Đang tạo mới inventory-web-sg..."
  WEB_SG_ID=$(aws ec2 create-security-group \
    --group-name inventory-web-sg \
    --description "Security Group cho Web Tier (Flask App / Elastic Beanstalk)" \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=inventory-web-sg},{Key=Project,Value=$PROJECT_TAG},{Key=Owner,Value=$OWNER_TAG}]" \
    --query "GroupId" \
    --output text \
    --region "$REGION")
  echo "Đã tạo inventory-web-sg: $WEB_SG_ID"
else
  echo "inventory-web-sg đã tồn tại: $WEB_SG_ID"
fi

echo "Cấu hình Inbound Rules cho inventory-web-sg (Port 80, 5000, 443)..."
aws ec2 authorize-security-group-ingress \
  --group-id "$WEB_SG_ID" \
  --protocol tcp --port 80 --cidr 0.0.0.0/0 \
  --region "$REGION" 2>/dev/null || echo "Port 80 đã được cấp phép."

aws ec2 authorize-security-group-ingress \
  --group-id "$WEB_SG_ID" \
  --protocol tcp --port 5000 --cidr 0.0.0.0/0 \
  --region "$REGION" 2>/dev/null || echo "Port 5000 đã được cấp phép."

aws ec2 authorize-security-group-ingress \
  --group-id "$WEB_SG_ID" \
  --protocol tcp --port 443 --cidr 0.0.0.0/0 \
  --region "$REGION" 2>/dev/null || echo "Port 443 đã được cấp phép."

echo ""
echo "=== [4/4] Khởi tạo & Cấu hình Security Group cho Database Tier (inventory-db-sg) ==="
DB_SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=inventory-db-sg" "Name=vpc-id,Values=$VPC_ID" \
  --query "SecurityGroups[0].GroupId" \
  --output text \
  --region "$REGION" 2>/dev/null || echo "None")

if [ -z "$DB_SG_ID" ] || [ "$DB_SG_ID" == "None" ]; then
  echo "Đang tạo mới inventory-db-sg..."
  DB_SG_ID=$(aws ec2 create-security-group \
    --group-name inventory-db-sg \
    --description "Security Group cho RDS PostgreSQL Database Tier" \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=inventory-db-sg},{Key=Project,Value=$PROJECT_TAG},{Key=Owner,Value=$OWNER_TAG}]" \
    --query "GroupId" \
    --output text \
    --region "$REGION")
  echo "Đã tạo inventory-db-sg: $DB_SG_ID"
else
  echo "inventory-db-sg đã tồn tại: $DB_SG_ID"
fi

echo "Cấu hình Security Group Chaining: Port 5432 chỉ cho phép Source từ $WEB_SG_ID..."
aws ec2 authorize-security-group-ingress \
  --group-id "$DB_SG_ID" \
  --protocol tcp --port 5432 \
  --source-group "$WEB_SG_ID" \
  --region "$REGION" 2>/dev/null || echo "Port 5432 từ $WEB_SG_ID đã được cấp phép."

echo ""
echo "=== [Xác minh] Kiểm tra IAM Instance Profile (LabInstanceProfile) ==="
aws iam get-instance-profile \
  --instance-profile-name LabInstanceProfile \
  --region "$REGION" \
  --output table \
  --no-cli-pager

echo ""
echo "=============================================================================="
echo "HOÀN TẤT CẤU HÌNH HẠ TẦNG BẢO MẬT TUẦN 1!"
echo "VPC ID:        $VPC_ID"
echo "Web SG ID:     $WEB_SG_ID (Port 80, 5000, 443 từ 0.0.0.0/0)"
echo "DB SG ID:      $DB_SG_ID (Port 5432 chỉ từ $WEB_SG_ID)"
echo "Tagging:       Project=$PROJECT_TAG | Owner=$OWNER_TAG"
echo "InstanceProfile: LabInstanceProfile sẵn sàng cho Beanstalk/EC2 ở Tuần 2"
echo "=============================================================================="
