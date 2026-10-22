import csv
import io
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

REPORT_S3_BUCKET = os.environ.get("REPORT_S3_BUCKET")
REPORT_S3_REGION = os.environ.get("REPORT_S3_REGION") or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def sanitize_csv_cell(value):
    """Phòng chống CSV Formula Injection (Excel / Google Sheets execution).

    Nếu ô bắt đầu bằng '=', '+', '-', '@', '\t', '\r', thêm dấu nháy đơn "'" ở đầu
    để ngăn chặn trình xử lý bảng tính thực thi công thức độc hại.
    """
    if value is None:
        return ""
    text = str(value)
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{text}"
    return text


def generate_inventory_csv(products):
    """Tạo chuỗi CSV từ danh sách sản phẩm.

    Hỗ trợ xử lý dữ liệu chuẩn UTF-8, phòng chống Formula Injection,
    và xử lý an toàn khi kho rỗng (chỉ xuất dòng tiêu đề).
    """
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    headers = [
        "Mã ID",
        "Mã SKU",
        "Tên sản phẩm",
        "Số lượng tồn kho",
        "Ngưỡng an toàn",
        "Trạng thái cảnh báo",
        "Cập nhật lần cuối",
    ]
    writer.writerow(headers)

    for p in products:
        p_id = p.get("id") if isinstance(p, dict) else p["id"]
        sku = p.get("sku") if isinstance(p, dict) else p["sku"]
        name = p.get("name") if isinstance(p, dict) else p["name"]
        quantity = p.get("quantity") if isinstance(p, dict) else p["quantity"]
        min_threshold = p.get("min_threshold") if isinstance(p, dict) else p["min_threshold"]
        updated_at = p.get("updated_at") if isinstance(p, dict) else p["updated_at"]

        status = "Cảnh báo hết hàng" if quantity <= min_threshold else "Bình thường"

        writer.writerow([
            sanitize_csv_cell(p_id),
            sanitize_csv_cell(sku),
            sanitize_csv_cell(name),
            sanitize_csv_cell(quantity),
            sanitize_csv_cell(min_threshold),
            sanitize_csv_cell(status),
            sanitize_csv_cell(updated_at),
        ])

    return output.getvalue()


def upload_report_to_s3(csv_content, bucket_name=None, region_name=None, s3_client=None):
    """Lưu trữ báo cáo CSV vào Amazon S3 bucket private.

    - ServerSideEncryption='AES256' (SSE-S3).
    - Không hardcode credentials; tận dụng IAM Instance Profile (LabInstanceProfile/LabRole).
    - Tự động sinh S3 key theo cấu trúc: inventory_reports/inventory_report_YYYYMMDD_HHMMSS.csv
    """
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    bucket = bucket_name or os.environ.get("REPORT_S3_BUCKET")
    if not bucket:
        raise ValueError("Chưa cấu hình tên S3 Bucket (biến môi trường REPORT_S3_BUCKET).")

    region = region_name or os.environ.get("REPORT_S3_REGION") or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

    if s3_client is None:
        s3_client = boto3.client("s3", region_name=region)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    s3_key = f"inventory_reports/inventory_report_{timestamp}.csv"

    # Chuyển đổi chuỗi sang bytes có BOM utf-8-sig để Excel hiển thị tiếng Việt không lỗi font
    body_bytes = csv_content.encode("utf-8-sig")

    try:
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=body_bytes,
            ContentType="text/csv; charset=utf-8",
            ServerSideEncryption="AES256",
            Metadata={
                "generated_by": "inventory-app",
                "report_type": "inventory_stock",
                "timestamp": timestamp,
            },
        )
        logger.info("Upload báo cáo tồn kho lên S3 thành công: s3://%s/%s", bucket, s3_key)
        return {
            "bucket": bucket,
            "key": s3_key,
            "size_bytes": len(body_bytes),
            "timestamp": timestamp,
        }
    except (BotoCoreError, ClientError) as error:
        logger.exception("Lỗi khi tải báo cáo lên S3: %s", error)
        raise RuntimeError(f"Lỗi khi tải báo cáo lên Amazon S3: {error}") from error
