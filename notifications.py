import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
SNS_REGION = os.environ.get("SNS_REGION") or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
ALERT_ENABLED = os.environ.get("ALERT_ENABLED", "true").lower() in ("true", "1", "yes")


def should_trigger_low_stock_alert(previous_quantity, new_quantity, min_threshold, trans_type="OUT"):
    """Xác định điều kiện gửi cảnh báo tồn kho chạm ngưỡng (Edge-triggered / State-transition).

    Điều kiện gửi:
    1. Giao dịch phải là xuất kho ('OUT').
    2. Tồn kho trước giao dịch lớn hơn ngưỡng an toàn (previous_quantity > min_threshold).
    3. Tồn kho sau giao dịch chạm hoặc rơi xuống dưới ngưỡng an toàn (new_quantity <= min_threshold).

    Quy tắc chống thông báo lặp (Debounce/Idempotency):
    - Nếu sản phẩm đã ở dưới ngưỡng (previous_quantity <= min_threshold) và tiếp tục bị xuất bớt,
      hệ thống KHÔNG gửi thông báo lặp lại để tránh làm ngập hộp thư của người quản lý kho.
    - Chỉ khi sản phẩm được nhập hàng trở lại mức an toàn (> min_threshold) rồi sau đó xuất tụt
      xuống ngưỡng, cảnh báo mới được kích hoạt lại.
    """
    if trans_type != "OUT":
        return False

    if min_threshold is None:
        return False

    return (previous_quantity > min_threshold) and (new_quantity <= min_threshold)


def format_low_stock_message(product, previous_quantity, new_quantity):
    """Định dạng tiêu đề và nội dung thông báo cảnh báo gửi qua Amazon SNS.

    Tuân thủ nguyên tắc không để lộ thông tin xác thực, định dạng rõ ràng, chuyên nghiệp.
    """
    sku = product.get("sku", "N/A")
    name = product.get("name", "N/A")
    min_threshold = product.get("min_threshold", 0)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    subject = f"[INVENTORY ALERT] SKU {sku} chạm ngưỡng tồn kho tối thiểu"

    message = (
        f"CẢNH BÁO TỒN KHO HỆ THỐNG INVENTORY-APP\n"
        f"=========================================\n"
        f"Mã SKU:            {sku}\n"
        f"Tên sản phẩm:      {name}\n"
        f"Tồn kho trước xuất: {previous_quantity}\n"
        f"Tồn kho hiện tại:  {new_quantity}\n"
        f"Ngưỡng tối thiểu:  {min_threshold}\n"
        f"Thời gian:         {now_str}\n"
        f"Trạng thái:        CHẠM HOẶC DƯỚI NGƯỠNG AN TOÀN\n"
        f"=========================================\n"
        f"Vui lòng lên kế hoạch nhập thêm hàng để đảm bảo hoạt động kho."
    )

    return {"subject": subject, "message": message}


def send_low_stock_alert(
    product,
    previous_quantity,
    new_quantity,
    trans_type="OUT",
    topic_arn=None,
    region_name=None,
    sns_client=None,
):
    """Thực thi kiểm tra điều kiện và phát cảnh báo qua Amazon SNS Topic nếu hợp lệ.

    - Không hardcode credentials; sử dụng IAM Role (LabInstanceProfile/LabRole).
    - Thất bại khi gửi SNS (thiếu quyền, network timeout, chưa cấu hình ARN) không làm ảnh hưởng
      hay làm rollback giao dịch kho (Non-blocking & Graceful Failure).
    """
    if not ALERT_ENABLED:
        logger.info("Chức năng cảnh báo tồn kho đang bị vô hiệu hóa bởi ALERT_ENABLED=false.")
        return {"sent": False, "reason": "alert_disabled"}

    if not should_trigger_low_stock_alert(previous_quantity, new_quantity, product.get("min_threshold"), trans_type):
        return {"sent": False, "reason": "condition_not_met"}

    target_arn = topic_arn or os.environ.get("SNS_TOPIC_ARN")
    if not target_arn:
        logger.warning(
            "Cần gửi cảnh báo cho SKU '%s' nhưng chưa cấu hình SNS_TOPIC_ARN. Bỏ qua gửi thông báo.",
            product.get("sku"),
        )
        return {"sent": False, "reason": "missing_topic_arn"}

    region = region_name or os.environ.get("SNS_REGION") or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

    payload = format_low_stock_message(product, previous_quantity, new_quantity)

    try:
        if sns_client is None:
            import boto3
            sns_client = boto3.client("sns", region_name=region)

        response = sns_client.publish(
            TopicArn=target_arn,
            Subject=payload["subject"],
            Message=payload["message"],
        )
        message_id = response.get("MessageId")
        logger.info(
            "Gửi cảnh báo tồn kho thành công cho SKU '%s' qua SNS Topic '%s' (MessageId: %s)",
            product.get("sku"),
            target_arn,
            message_id,
        )
        return {"sent": True, "message_id": message_id}
    except Exception as exc:
        logger.error(
            "Không thể gửi thông báo SNS cho SKU '%s' tới '%s': %s",
            product.get("sku"),
            target_arn,
            str(exc),
        )
        return {"sent": False, "reason": "sns_error", "error": str(exc)}


def inspect_topic_subscriptions(topic_arn=None, region_name=None, sns_client=None):
    """Liệt kê và phân tích trạng thái các subscriber của SNS Topic.

    Xác định trạng thái 'PendingConfirmation' hoặc 'Confirmed',
    ẩn thông tin cá nhân (PII) như email/số điện thoại để đảm bảo an toàn.
    """
    target_arn = topic_arn or os.environ.get("SNS_TOPIC_ARN")
    if not target_arn:
        return {"configured": False, "subscriptions": [], "reason": "missing_topic_arn"}

    region = region_name or os.environ.get("SNS_REGION") or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

    try:
        if sns_client is None:
            import boto3
            sns_client = boto3.client("sns", region_name=region)

        response = sns_client.list_subscriptions_by_topic(TopicArn=target_arn)
        subs = []
        for sub in response.get("Subscriptions", []):
            endpoint = sub.get("Endpoint", "")
            # Che thông tin PII (Email: kh***@gmail.com)
            masked_endpoint = endpoint
            if "@" in endpoint:
                parts = endpoint.split("@")
                masked_user = parts[0][:2] + "***" if len(parts[0]) > 2 else "***"
                masked_endpoint = f"{masked_user}@{parts[1]}"

            sub_arn = sub.get("SubscriptionArn", "")
            is_pending = sub_arn == "PendingConfirmation" or not sub_arn.startswith("arn:aws:sns:")

            subs.append({
                "protocol": sub.get("Protocol"),
                "endpoint_masked": masked_endpoint,
                "status": "PendingConfirmation" if is_pending else "Confirmed",
                "subscription_arn": "PendingConfirmation" if is_pending else sub_arn,
            })
        return {"configured": True, "subscriptions": subs}
    except Exception as exc:
        logger.error("Lỗi khi kiểm tra subscriptions của topic '%s': %s", target_arn, str(exc))
        return {"configured": True, "subscriptions": [], "error": str(exc)}
