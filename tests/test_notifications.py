import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

import app as inventory_app
import notifications


class LowStockAlertLogicTests(unittest.TestCase):
    def setUp(self):
        inventory_app.app.config.update(TESTING=True)
        self.client = inventory_app.app.test_client()

    def test_trigger_condition_edge_triggered(self):
        # Tồn trước = 6, sau xuất = 5 (ngưỡng = 5) -> Kích hoạt (chạm ngưỡng)
        self.assertTrue(
            notifications.should_trigger_low_stock_alert(
                previous_quantity=6, new_quantity=5, min_threshold=5, trans_type="OUT"
            )
        )

        # Tồn trước = 6, sau xuất = 2 (ngưỡng = 5) -> Kích hoạt (rơi xuống dưới ngưỡng)
        self.assertTrue(
            notifications.should_trigger_low_stock_alert(
                previous_quantity=6, new_quantity=2, min_threshold=5, trans_type="OUT"
            )
        )

    def test_prevent_duplicate_alerts_when_already_low(self):
        # Đã dưới ngưỡng từ trước: trước = 4, sau xuất = 3 (ngưỡng = 5) -> KHÔNG gửi lặp
        self.assertFalse(
            notifications.should_trigger_low_stock_alert(
                previous_quantity=4, new_quantity=3, min_threshold=5, trans_type="OUT"
            )
        )

        # Đã chạm ngưỡng: trước = 5, sau xuất = 4 (ngưỡng = 5) -> KHÔNG gửi lặp
        self.assertFalse(
            notifications.should_trigger_low_stock_alert(
                previous_quantity=5, new_quantity=4, min_threshold=5, trans_type="OUT"
            )
        )

    def test_no_alert_for_inbound_or_safe_stock(self):
        # Nhập kho (IN) không bao giờ gửi cảnh báo hết hàng
        self.assertFalse(
            notifications.should_trigger_low_stock_alert(
                previous_quantity=3, new_quantity=10, min_threshold=5, trans_type="IN"
            )
        )

        # Xuất kho nhưng tồn kho vẫn an toàn (> threshold): trước = 20, sau = 15 (ngưỡng = 5) -> Không gửi
        self.assertFalse(
            notifications.should_trigger_low_stock_alert(
                previous_quantity=20, new_quantity=15, min_threshold=5, trans_type="OUT"
            )
        )

    def test_format_low_stock_message_content(self):
        sample_prod = {
            "id": 10,
            "sku": "SKU-ALERT-01",
            "name": "Cáp HDMI 2.1 Anker",
            "quantity": 3,
            "min_threshold": 5,
        }
        res = notifications.format_low_stock_message(sample_prod, previous_quantity=8, new_quantity=3)
        self.assertIn("SKU-ALERT-01", res["subject"])
        self.assertIn("SKU-ALERT-01", res["message"])
        self.assertIn("Cáp HDMI 2.1 Anker", res["message"])
        self.assertIn("Tồn kho trước xuất: 8", res["message"])
        self.assertIn("Tồn kho hiện tại:  3", res["message"])
        self.assertIn("Ngưỡng tối thiểu:  5", res["message"])

    def test_send_alert_success_mock(self):
        sample_prod = {
            "sku": "SKU-TEST-SNS",
            "name": "Bàn phím Test",
            "min_threshold": 5,
        }
        mock_sns = MagicMock()
        mock_sns.publish.return_value = {"MessageId": "mock-msg-uuid-12345"}

        result = notifications.send_low_stock_alert(
            product=sample_prod,
            previous_quantity=10,
            new_quantity=4,
            trans_type="OUT",
            topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            region_name="us-east-1",
            sns_client=mock_sns,
        )

        self.assertTrue(result["sent"])
        self.assertEqual(result["message_id"], "mock-msg-uuid-12345")
        mock_sns.publish.assert_called_once()
        call_kwargs = mock_sns.publish.call_args[1]
        self.assertEqual(call_kwargs["TopicArn"], "arn:aws:sns:us-east-1:123456789012:test-topic")
        self.assertIn("SKU-TEST-SNS", call_kwargs["Subject"])

    def test_send_alert_missing_topic_arn_does_not_crash(self):
        sample_prod = {"sku": "SKU-TEST", "min_threshold": 5}
        with patch.dict("os.environ", {}, clear=True):
            result = notifications.send_low_stock_alert(
                product=sample_prod,
                previous_quantity=10,
                new_quantity=3,
                trans_type="OUT",
                topic_arn=None,
            )
            self.assertFalse(result["sent"])
            self.assertEqual(result["reason"], "missing_topic_arn")

    def test_send_alert_handles_sns_client_error_gracefully(self):
        sample_prod = {"sku": "SKU-TEST", "min_threshold": 5}
        mock_sns = MagicMock()
        mock_sns.publish.side_effect = ClientError(
            {"Error": {"Code": "AuthorizationErrorException", "Message": "User not authorized"}},
            "Publish",
        )

        result = notifications.send_low_stock_alert(
            product=sample_prod,
            previous_quantity=10,
            new_quantity=2,
            trans_type="OUT",
            topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            sns_client=mock_sns,
        )

        self.assertFalse(result["sent"])
        self.assertEqual(result["reason"], "sns_error")
        self.assertIn("AuthorizationErrorException", result["error"])

    def test_inspect_topic_subscriptions_pii_masking_and_pending_status(self):
        mock_sns = MagicMock()
        mock_sns.list_subscriptions_by_topic.return_value = {
            "Subscriptions": [
                {
                    "Protocol": "email",
                    "Endpoint": "nguyendinhkhanh@gmail.com",
                    "SubscriptionArn": "PendingConfirmation",
                },
                {
                    "Protocol": "email",
                    "Endpoint": "admin-warehouse@company.com",
                    "SubscriptionArn": "arn:aws:sns:us-east-1:123456789012:test-topic:uuid-sub-999",
                },
            ]
        }

        res = notifications.inspect_topic_subscriptions(
            topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            sns_client=mock_sns,
        )

        self.assertTrue(res["configured"])
        subs = res["subscriptions"]
        self.assertEqual(len(subs), 2)

        # Kiểm tra subscriber 1: PendingConfirmation và đã ẩn PII
        self.assertEqual(subs[0]["status"], "PendingConfirmation")
        self.assertEqual(subs[0]["endpoint_masked"], "ng***@gmail.com")
        self.assertNotIn("nguyendinhkhanh", subs[0]["endpoint_masked"])

        # Kiểm tra subscriber 2: Confirmed
        self.assertEqual(subs[1]["status"], "Confirmed")
        self.assertEqual(subs[1]["endpoint_masked"], "ad***@company.com")

    def test_api_notification_status_endpoint(self):
        with patch("notifications.inspect_topic_subscriptions") as mock_inspect:
            mock_inspect.return_value = {
                "configured": True,
                "subscriptions": [
                    {
                        "protocol": "email",
                        "endpoint_masked": "te***@example.com",
                        "status": "PendingConfirmation",
                        "subscription_arn": "PendingConfirmation",
                    }
                ],
            }
            res = self.client.get("/api/notifications/status")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn("alert_enabled", data)
            self.assertIn("subscriptions", data)
            self.assertEqual(data["subscriptions"][0]["status"], "PendingConfirmation")


if __name__ == "__main__":
    unittest.main()
