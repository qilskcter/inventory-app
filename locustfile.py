"""
Kịch bản kiểm thử tải nhẹ (Load Testing) bằng Locust cho Hệ thống Quản lý Kho (inventory-app).
Mô phỏng 10–20 người dùng đồng thời truy cập các endpoint:
1. GET  /api/products               (Đọc danh sách sản phẩm - weight: 3)
2. GET  /api/reports/inventory/csv  (Xuất báo cáo tồn kho CSV - weight: 1)
3. POST /api/transactions           (Giao dịch nhập kho nguyên tử - weight: 2)

Tuân thủ nguyên tắc an toàn dữ liệu: chỉ thao tác trên SKU thử nghiệm LOAD-TEST-*.
"""

import logging
import random
from locust import HttpUser, between, task, events

logger = logging.getLogger("locust_inventory")


class InventoryLoadTestUser(HttpUser):
    # Thời gian chờ giữa các thao tác của mỗi người dùng (0.2s - 0.8s mô phỏng thao tác nhanh)
    wait_time = between(0.2, 0.8)

    # Biến chia sẻ giữa các luồng người dùng
    test_product_id = None

    def on_start(self):
        """Khởi tạo người dùng: tìm hoặc tạo sản phẩm thử nghiệm an toàn."""
        if InventoryLoadTestUser.test_product_id is None:
            try:
                # Tìm xem đã có sản phẩm test chưa
                res = self.client.get("/api/products", name="/api/products [Init]")
                if res.status_code == 200:
                    products = res.json()
                    for p in products:
                        if p.get("sku", "").startswith("LOAD-TEST-"):
                            InventoryLoadTestUser.test_product_id = p["id"]
                            break

                # Nếu chưa có, tạo mới một sản phẩm thử nghiệm với tồn ban đầu 1000
                if InventoryLoadTestUser.test_product_id is None:
                    create_payload = {
                        "sku": f"LOAD-TEST-LOCUST-{random.randint(100, 999)}",
                        "name": "Sản phẩm kiểm thử tải Locust",
                        "quantity": 1000,
                        "min_threshold": 5,
                    }
                    create_res = self.client.post(
                        "/api/products",
                        json=create_payload,
                        name="/api/products [Setup]",
                    )
                    if create_res.status_code == 201:
                        InventoryLoadTestUser.test_product_id = create_res.json().get("id")
                        logger.info("Đã tạo sản phẩm kiểm thử tải ID: %s", InventoryLoadTestUser.test_product_id)
            except Exception as e:
                logger.warning("Lỗi trong on_start setup: %s", e)

        # Fallback về ID 19 hoặc 1 nếu không tạo được
        self.product_id = InventoryLoadTestUser.test_product_id or 19

    @task(3)
    def test_get_products(self):
        """Endpoint đọc: GET /api/products (Tần suất cao: trọng số 3)."""
        with self.client.get(
            "/api/products",
            name="GET /api/products",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}: {response.text}")

    @task(1)
    def test_export_inventory_csv(self):
        """Endpoint xuất báo cáo: GET /api/reports/inventory/csv (Trọng số 1)."""
        with self.client.get(
            "/api/reports/inventory/csv",
            name="GET /api/reports/inventory/csv",
            catch_response=True,
        ) as response:
            if response.status_code == 200 and "text/csv" in response.headers.get("Content-Type", ""):
                response.success()
            else:
                response.failure(f"CSV Export Error {response.status_code}")

    @task(2)
    def test_create_transaction(self):
        """Endpoint ghi: POST /api/transactions (Giao dịch nhập kho - trọng số 2)."""
        payload = {
            "product_id": self.product_id,
            "type": "IN",
            "quantity": 1,
        }
        with self.client.post(
            "/api/transactions",
            json=payload,
            name="POST /api/transactions",
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Transaction Error {response.status_code}: {response.text}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("==================================================")
    logger.info("BẮT ĐẦU PHIÊN KIỂM THỬ TẢI NHẸ (LOAD TESTING)")
    logger.info("Host mục tiêu: %s", environment.host)
    logger.info("==================================================")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("==================================================")
    logger.info("KẾT THÚC PHIÊN KIỂM THỬ TẢI NHẸ")
    logger.info("Tổng số requests: %s", environment.stats.total.num_requests)
    logger.info("Tổng số failures: %s", environment.stats.total.num_failures)
    logger.info("==================================================")
