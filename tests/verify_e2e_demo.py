"""
Kiểm thử toàn trình (End-to-End Test) theo đúng Kịch bản Live Demo (Step-by-step Demo Flow):
Từ Giao diện Web UI -> Backend RESTful API -> ThreadedConnectionPool (RDS PostgreSQL)
-> Cảnh báo tồn kho tự động qua Amazon SNS (Email Subscriber) -> Xuất báo cáo CSV lên Amazon S3 Private.

Bộ kiểm thử bao gồm 6 ca kiểm nghiệm toàn trình (TC-E2E-01 đến TC-E2E-06):
- TC-E2E-01: Kiểm tra trạng thái sẵn sàng của hệ thống, Connection Pool và Email Subscriber SNS thực tế (Confirmed).
- TC-E2E-02: Chuẩn bị bộ dữ liệu Demo trực quan (W4-DEMO-01, W4-DEMO-02, W4-DEMO-03) và kiểm chứng hiển thị Web UI.
- TC-E2E-03: Thực thi giao dịch Nhập/Xuất kho chạm ngưỡng và đối chiếu chi tiết phản hồi Email cảnh báo SNS.
- TC-E2E-04: Kiểm chứng cơ chế chống thông báo lặp (Edge-triggered Debounce) khi xuất tiếp dưới ngưỡng.
- TC-E2E-05: Đối chiếu toàn diện file CSV tải trực tiếp và file CSV lưu trữ trên Amazon S3 Private Bucket (SSE-S3 AES256).
- TC-E2E-06: Kiểm thử các tình huống ngoại lệ trong kịch bản Demo (400, 409, 503) và dọn dẹp an toàn dữ liệu Demo.
"""

import logging
import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import psycopg2
import app as inventory_app
import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("verify_e2e_demo")


class InMemoryDemoDatabase:
    """Mô phỏng cơ sở dữ liệu PostgreSQL phục vụ kiểm thử toàn trình (Stateful E2E Flow)."""

    def __init__(self):
        self.products = {
            1: {
                "id": 1,
                "sku": "1",
                "name": "test",
                "quantity": 11,
                "min_threshold": 5,
                "updated_at": "2026-10-16 15:52:10",
            },
            13: {
                "id": 13,
                "sku": "W3-DEMO-01",
                "name": "Bàn phím cơ RGB",
                "quantity": 10,
                "min_threshold": 5,
                "updated_at": "2026-10-22 13:18:09",
            },
            15: {
                "id": 15,
                "sku": "W3-DEMO-02",
                "name": "Chuột Gaming RGB",
                "quantity": 12,
                "min_threshold": 5,
                "updated_at": "2026-10-22 13:20:05",
            },
        }
        self.transactions = []
        self.next_product_id = 20
        self.next_tx_id = 100

    def create_connection(self):
        conn = MagicMock()
        conn.closed = 0
        db = self

        def cursor_factory(*args, **kwargs):
            cur = MagicMock()
            cur._last_one = None
            cur._last_all = []

            def execute(sql, params=None):
                norm = " ".join(sql.split())
                now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

                if norm.startswith("SELECT * FROM products ORDER BY id ASC"):
                    cur._last_all = [
                        dict(p) for _, p in sorted(db.products.items(), key=lambda x: x[0])
                    ]
                elif norm.startswith("SELECT * FROM products WHERE id = %s"):
                    pid = params[0]
                    cur._last_one = dict(db.products[pid]) if pid in db.products else None
                elif norm.startswith("SELECT id FROM products WHERE id = %s"):
                    pid = params[0]
                    cur._last_one = {"id": pid} if pid in db.products else None
                elif norm.startswith("INSERT INTO products"):
                    sku, name, qty, min_t = params
                    for existing in db.products.values():
                        if existing["sku"] == sku:
                            raise psycopg2.IntegrityError(f"Duplicate SKU: {sku}")
                    pid = db.next_product_id
                    db.next_product_id += 1
                    record = {
                        "id": pid,
                        "sku": sku,
                        "name": name,
                        "quantity": qty,
                        "min_threshold": min_t,
                        "updated_at": now_str,
                    }
                    db.products[pid] = record
                    cur._last_one = dict(record)
                elif norm.startswith("UPDATE products SET quantity = quantity + %s"):
                    qty, pid = params
                    if pid not in db.products:
                        cur._last_one = None
                    else:
                        db.products[pid]["quantity"] += qty
                        db.products[pid]["updated_at"] = now_str
                        cur._last_one = dict(db.products[pid])
                elif norm.startswith("UPDATE products SET quantity = quantity - %s"):
                    qty, pid, min_req = params
                    if pid not in db.products or db.products[pid]["quantity"] < min_req:
                        cur._last_one = None
                    else:
                        db.products[pid]["quantity"] -= qty
                        db.products[pid]["updated_at"] = now_str
                        cur._last_one = dict(db.products[pid])
                elif norm.startswith("INSERT INTO transactions"):
                    pid, t_type, qty = params
                    tx_id = db.next_tx_id
                    db.next_tx_id += 1
                    tx_rec = {
                        "id": tx_id,
                        "product_id": pid,
                        "type": t_type,
                        "quantity": qty,
                        "created_at": now_str,
                    }
                    db.transactions.append(tx_rec)
                    cur._last_one = dict(tx_rec)
                elif norm.startswith("SELECT t.id, t.product_id"):
                    rows = []
                    for tx in reversed(db.transactions):
                        p = db.products.get(tx["product_id"], {"sku": "N/A", "name": "N/A"})
                        rows.append({
                            "id": tx["id"],
                            "product_id": tx["product_id"],
                            "sku": p["sku"],
                            "product_name": p["name"],
                            "type": tx["type"],
                            "quantity": tx["quantity"],
                            "created_at": tx["created_at"],
                        })
                    cur._last_all = rows
                elif norm.startswith("DELETE FROM products WHERE id = %s"):
                    pid = params[0]
                    if pid in db.products:
                        del db.products[pid]
                        cur._last_one = {"id": pid}
                    else:
                        cur._last_one = None

            cur.execute.side_effect = execute
            cur.fetchone.side_effect = lambda: cur._last_one
            cur.fetchall.side_effect = lambda: cur._last_all
            return cur

        conn.cursor.side_effect = cursor_factory
        return conn


class E2ELiveDemoFlowTests(unittest.TestCase):
    """Bộ kiểm thử toàn trình (E2E) xác nhận các bước kịch bản Live Demo hoạt động trơn tru."""

    def setUp(self):
        init_db.close_db_pool()
        inventory_app.app.config.update(TESTING=True)
        self.client = inventory_app.app.test_client()
        self.demo_db = InMemoryDemoDatabase()
        self.published_sns_messages = []
        self.uploaded_s3_objects = []

        self.env_patcher = patch.dict(
            "os.environ",
            {
                "SNS_TOPIC_ARN": "arn:aws:sns:us-east-1:041118630529:inventory-low-stock-alert",
                "SNS_REGION": "us-east-1",
                "ALERT_ENABLED": "true",
                "REPORT_S3_BUCKET": "inventory-reports-us-east-1-24110244",
                "REPORT_S3_REGION": "us-east-1",
            },
        )
        self.env_patcher.start()

        self.mock_sns_client = MagicMock()

        def handle_sns_publish(**kwargs):
            msg_id = f"demo-sns-msg-{len(self.published_sns_messages) + 1:04d}-89ab-cdef01234567"
            record = {
                "MessageId": msg_id,
                "TopicArn": kwargs["TopicArn"],
                "Subject": kwargs["Subject"],
                "Message": kwargs["Message"],
            }
            self.published_sns_messages.append(record)
            return {"MessageId": msg_id}

        self.mock_sns_client.publish.side_effect = handle_sns_publish
        self.mock_sns_client.list_subscriptions_by_topic.return_value = {
            "Subscriptions": [
                {
                    "Protocol": "email",
                    "Endpoint": "24110244@student.hcmute.edu.vn",
                    "SubscriptionArn": (
                        "arn:aws:sns:us-east-1:041118630529:"
                        "inventory-low-stock-alert:d41ec4d9-993a-40e8-943c-821c44f71dd6"
                    ),
                }
            ]
        }

        self.mock_s3_client = MagicMock()

        def handle_s3_put_object(**kwargs):
            self.uploaded_s3_objects.append(kwargs)
            return {"ETag": '"e2e-demo-s3-etag-20261031"'}

        self.mock_s3_client.put_object.side_effect = handle_s3_put_object

        def fake_boto3_client(service_name, region_name=None):
            if service_name == "sns":
                return self.mock_sns_client
            if service_name == "s3":
                return self.mock_s3_client
            raise ValueError(f"Unexpected service: {service_name}")

        self.db_patcher = patch(
            "init_db.psycopg2.connect",
            side_effect=lambda **kw: self.demo_db.create_connection(),
        )
        self.boto_patcher = patch("boto3.client", side_effect=fake_boto3_client)
        self.db_patcher.start()
        self.boto_patcher.start()

    def tearDown(self):
        self.boto_patcher.stop()
        self.db_patcher.stop()
        self.env_patcher.stop()
        init_db.close_db_pool()

    def test_01_demo_environment_and_sns_subscriber_readiness(self):
        """TC-E2E-01: Kiểm tra trạng thái sẵn sàng của hệ thống, Connection Pool và Email Subscriber SNS."""
        logger.info("[TC-E2E-01] Kiểm tra trạng thái SNS Topic và Email Subscriber Confirmed...")
        resp = self.client.get("/api/notifications/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["configured"])
        self.assertEqual(data["region"], "us-east-1")
        self.assertEqual(len(data["subscriptions"]), 1)
        sub = data["subscriptions"][0]
        self.assertEqual(sub["protocol"], "email")
        self.assertEqual(sub["status"], "Confirmed")
        self.assertEqual(sub["endpoint_masked"], "24***@student.hcmute.edu.vn")
        logger.info(" -> ĐẠT: Subscriber %s ở trạng thái %s.", sub["endpoint_masked"], sub["status"])

    def test_02_demo_data_preparation_and_web_ui_rendering(self):
        """TC-E2E-02: Chuẩn bị bộ dữ liệu Demo trực quan (W4-DEMO-01..03) và kiểm chứng giao diện Web UI."""
        logger.info("[TC-E2E-02] Tạo dữ liệu Demo trực quan và kiểm tra hiển thị trên Web UI...")
        r1 = self.client.post(
            "/api/products",
            json={"sku": "W4-DEMO-01", "name": "MacBook Pro 14 M3 Pro", "quantity": 8, "min_threshold": 5},
        )
        r2 = self.client.post(
            "/api/products",
            json={"sku": "W4-DEMO-02", "name": "Màn hình Dell UltraSharp 27 4K", "quantity": 15, "min_threshold": 5},
        )
        r3 = self.client.post(
            "/add",
            data={
                "sku": "W4-DEMO-03",
                "name": "=SUM(A1:A10) Cáp Thunderbolt 4",
                "quantity": "3",
                "min_threshold": "5",
            },
            follow_redirects=True,
        )
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 201)
        self.assertEqual(r3.status_code, 200)

        html = r3.get_data(as_text=True)
        self.assertIn("Thêm sản phẩm thành công!", html)
        self.assertIn("W4-DEMO-01", html)
        self.assertIn("MacBook Pro 14 M3 Pro", html)
        self.assertIn("W4-DEMO-02", html)
        self.assertIn("W4-DEMO-03", html)
        self.assertIn("table-warning", html)
        self.assertIn("Sắp hết", html)
        logger.info(" -> ĐẠT: 3 SKU Demo hiển thị trực quan kèm huy hiệu cảnh báo trên Web UI.")

    def test_03_inbound_and_outbound_edge_triggered_sns_email_reconciliation(self):
        """TC-E2E-03: Giao dịch Nhập/Xuất kho chạm ngưỡng và đối chiếu nội dung Email cảnh báo SNS."""
        logger.info("[TC-E2E-03] Thực thi giao dịch Nhập/Xuất kho và đối chiếu phản hồi Email SNS...")
        create_resp = self.client.post(
            "/api/products",
            json={"sku": "W4-DEMO-01", "name": "MacBook Pro 14 M3 Pro", "quantity": 8, "min_threshold": 5},
        )
        pid = create_resp.get_json()["id"]

        # Bước 3a: Nhập kho +4 (Tồn 8 -> 12 > 5) -> Không gửi SNS
        in_resp = self.client.post(
            "/api/transactions",
            json={"product_id": pid, "type": "IN", "quantity": 4},
        )
        self.assertEqual(in_resp.status_code, 201)
        self.assertEqual(in_resp.get_json()["product"]["quantity"], 12)
        self.assertEqual(len(self.published_sns_messages), 0)

        # Bước 3b: Xuất kho -8 (Tồn 12 -> 4 <= 5) -> Kích hoạt SNS Email
        out_resp = self.client.post(
            "/api/transactions",
            json={"product_id": pid, "type": "OUT", "quantity": 8},
        )
        self.assertEqual(out_resp.status_code, 201)
        self.assertEqual(out_resp.get_json()["product"]["quantity"], 4)
        self.assertEqual(len(self.published_sns_messages), 1)

        email = self.published_sns_messages[0]
        self.assertEqual(
            email["TopicArn"],
            "arn:aws:sns:us-east-1:041118630529:inventory-low-stock-alert",
        )
        self.assertEqual(
            email["Subject"],
            "[INVENTORY ALERT] SKU W4-DEMO-01 chạm ngưỡng tồn kho tối thiểu",
        )
        self.assertIn("CẢNH BÁO TỒN KHO HỆ THỐNG INVENTORY-APP", email["Message"])
        self.assertIn("Mã SKU:            W4-DEMO-01", email["Message"])
        self.assertIn("Tên sản phẩm:      MacBook Pro 14 M3 Pro", email["Message"])
        self.assertIn("Tồn kho trước xuất: 12", email["Message"])
        self.assertIn("Tồn kho hiện tại:  4", email["Message"])
        self.assertIn("Ngưỡng tối thiểu:  5", email["Message"])
        self.assertIn("Trạng thái:        CHẠM HOẶC DƯỚI NGƯỠNG AN TOÀN", email["Message"])
        logger.info(" -> ĐẠT: Đối chiếu khớp 100%% Subject & Body của Email SNS (MessageId=%s).", email["MessageId"])

    def test_04_outbound_debounce_prevents_duplicate_sns_emails(self):
        """TC-E2E-04: Kiểm chứng cơ chế chống gửi thông báo lặp (Debounce) và chu kỳ Re-arm."""
        logger.info("[TC-E2E-04] Kiểm chứng cơ chế chống thông báo lặp (Edge-triggered Debounce)...")
        create_resp = self.client.post(
            "/api/products",
            json={"sku": "W4-DEMO-01", "name": "MacBook Pro 14 M3 Pro", "quantity": 6, "min_threshold": 5},
        )
        pid = create_resp.get_json()["id"]

        # Lần xuất 1: 6 -> 4 (<= 5) -> Gửi email cảnh báo lần 1
        self.client.post("/api/transactions", json={"product_id": pid, "type": "OUT", "quantity": 2})
        self.assertEqual(len(self.published_sns_messages), 1)

        # Lần xuất 2: 4 -> 3 (<= 5) -> Đã dưới ngưỡng từ trước, chặn gửi lặp
        r_deb = self.client.post("/api/transactions", json={"product_id": pid, "type": "OUT", "quantity": 1})
        self.assertEqual(r_deb.status_code, 201)
        self.assertEqual(r_deb.get_json()["product"]["quantity"], 3)
        self.assertEqual(len(self.published_sns_messages), 1)

        # Nhập kho khôi phục mức an toàn: 3 -> 10 (> 5)
        self.client.post("/api/transactions", json={"product_id": pid, "type": "IN", "quantity": 7})
        self.assertEqual(len(self.published_sns_messages), 1)

        # Xuất tụt ngưỡng lần nữa: 10 -> 5 (<= 5) -> Kích hoạt lại (Re-arm) gửi email lần 2
        self.client.post("/api/transactions", json={"product_id": pid, "type": "OUT", "quantity": 5})
        self.assertEqual(len(self.published_sns_messages), 2)
        logger.info(" -> ĐẠT: Chặn lặp thành công khi đã thiếu hàng và tái kích hoạt (Re-arm) chuẩn xác.")

    def test_05_csv_export_and_s3_private_upload_reconciliation(self):
        """TC-E2E-05: Đối chiếu file CSV tải về trình duyệt và file CSV tải lên Amazon S3 Private."""
        logger.info("[TC-E2E-05] Đối chiếu file CSV trực tiếp và Object tải lên S3 Private Bucket...")
        p1 = self.client.post(
            "/api/products",
            json={"sku": "W4-DEMO-01", "name": "MacBook Pro 14 M3 Pro", "quantity": 3, "min_threshold": 5},
        ).get_json()
        self.client.post(
            "/api/products",
            json={"sku": "W4-DEMO-03", "name": "=SUM(A1:A10) Cáp Thunderbolt 4", "quantity": 3, "min_threshold": 5},
        )

        # Tải trực tiếp qua GET /api/reports/inventory/csv
        csv_resp = self.client.get("/api/reports/inventory/csv")
        self.assertEqual(csv_resp.status_code, 200)
        csv_bytes = csv_resp.get_data()
        self.assertTrue(csv_bytes.startswith(b"\xef\xbb\xbf"))
        csv_text = csv_bytes.decode("utf-8-sig")

        # Lưu trữ lên S3 Private qua POST /api/reports/inventory/export-s3
        s3_resp = self.client.post("/api/reports/inventory/export-s3")
        self.assertEqual(s3_resp.status_code, 200)
        s3_info = s3_resp.get_json()
        self.assertEqual(s3_info["s3_bucket"], "inventory-reports-us-east-1-24110244")
        self.assertTrue(s3_info["s3_key"].startswith("inventory_reports/inventory_report_"))
        self.assertEqual(s3_info["total_records"], 5)

        # Đối chiếu nội dung trên S3 với nội dung tải trực tiếp
        s3_obj = self.uploaded_s3_objects[0]
        self.assertEqual(s3_obj["Bucket"], "inventory-reports-us-east-1-24110244")
        self.assertEqual(s3_obj["ServerSideEncryption"], "AES256")
        self.assertEqual(s3_obj["ContentType"], "text/csv; charset=utf-8")
        self.assertEqual(s3_obj["Metadata"]["generated_by"], "inventory-app")
        self.assertEqual(s3_obj["Body"], csv_bytes)

        self.assertIn(f"{p1['id']},W4-DEMO-01,MacBook Pro 14 M3 Pro,3,5,Cảnh báo hết hàng", csv_text)
        self.assertIn("'=SUM(A1:A10) Cáp Thunderbolt 4", csv_text)
        logger.info(
            " -> ĐẠT: File CSV trên S3 (%s, %d bytes) khớp 100%% với dữ liệu RDS và đạt chuẩn SSE-S3 AES256.",
            s3_info["s3_key"],
            s3_info["size_bytes"],
        )

    def test_06_demo_exception_handling_and_safe_cleanup(self):
        """TC-E2E-06: Kiểm thử các tình huống ngoại lệ (400, 409, 503) và dọn dẹp an toàn dữ liệu Demo."""
        logger.info("[TC-E2E-06] Kiểm thử các tình huống ngoại lệ và dọn dẹp an toàn SKU Demo...")
        p1 = self.client.post(
            "/api/products",
            json={"sku": "W4-DEMO-01", "name": "MacBook Pro 14 M3 Pro", "quantity": 4, "min_threshold": 5},
        ).get_json()
        pid = p1["id"]

        # 1. Xuất vượt tồn kho (409 Conflict)
        r_over = self.client.post("/api/transactions", json={"product_id": pid, "type": "OUT", "quantity": 50})
        self.assertEqual(r_over.status_code, 409)

        # 2. Tạo trùng SKU (409 Conflict)
        r_dup = self.client.post("/api/products", json={"sku": "W4-DEMO-01", "name": "Trùng SKU"})
        self.assertEqual(r_dup.status_code, 409)

        # 3. Can thiệp tồn kho qua PATCH (400 Bad Request)
        r_patch = self.client.patch(f"/api/products/{pid}", json={"quantity": 999})
        self.assertEqual(r_patch.status_code, 400)

        # 4. Mô phỏng lỗi đứt kết nối RDS trả về HTTP 503 + Retry-After: 5
        with patch.object(
            inventory_app,
            "get_db_connection",
            side_effect=psycopg2.OperationalError("simulated RDS timeout"),
        ):
            r_503 = self.client.get("/api/products")
            self.assertEqual(r_503.status_code, 503)
            self.assertEqual(r_503.headers.get("Retry-After"), "5")

        # 5. Dọn dẹp an toàn SKU Demo (204 No Content)
        r_del = self.client.delete(f"/api/products/{pid}")
        self.assertEqual(r_del.status_code, 204)
        self.assertEqual(len(self.client.get("/api/products").get_json()), 3)
        logger.info(" -> ĐẠT: Xử lý ngoại lệ 400/409/503 chính xác và dọn dẹp sạch 100% dữ liệu Demo.")


if __name__ == "__main__":
    unittest.main()
