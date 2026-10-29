"""
Kiểm thử tính ổn định của Connection Pool (psycopg2.pool.ThreadedConnectionPool).
Kiểm tra:
1. Khởi tạo ThreadedConnectionPool kích thước 2–5 kết nối.
2. Xử lý chuỗi request liên tục (50 requests đa luồng đồng thời).
3. Đảm bảo giải phóng connection trong finally ở cả trường hợp thành công và ngoại lệ.
4. Kiểm soát trần kết nối (maxconn = 5) và cơ chế xử lý khi cạn kiệt pool (PoolError -> HTTP 503).
5. Xác nhận không rò rỉ socket và pool tái sử dụng kết nối ổn định 100%.
"""

import concurrent.futures
import logging
import os
import sys
import threading
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import psycopg2
from psycopg2 import pool

import app as inventory_app
import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("test_pool_stability")


class ConnectionPoolStabilityTests(unittest.TestCase):
    def setUp(self):
        init_db.close_db_pool()
        inventory_app.app.config.update(TESTING=True)
        self.client = inventory_app.app.test_client()

    def tearDown(self):
        init_db.close_db_pool()

    def test_pool_initialization_with_min_max_limits(self):
        """Kiểm tra khởi tạo ThreadedConnectionPool với kích thước chuẩn 2–5 kết nối."""
        with patch("init_db.psycopg2.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_conn.closed = 0
            mock_connect.return_value = mock_conn

            db_pool = init_db.get_db_pool(minconn=2, maxconn=5)
            self.assertIsNotNone(db_pool)
            self.assertEqual(db_pool.minconn, 2)
            self.assertEqual(db_pool.maxconn, 5)
            # Pool kích thước 2 kết nối ban đầu
            self.assertEqual(mock_connect.call_count, 2)

    def test_connection_release_in_finally_on_success(self):
        """Xác minh kết nối được hoàn trả về pool trong khối finally khi truy vấn thành công."""
        with patch("init_db.psycopg2.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_conn.closed = 0
            mock_connect.return_value = mock_conn

            db_pool = init_db.get_db_pool(minconn=2, maxconn=5)

            # Lấy kết nối
            conn = init_db.get_db_connection()
            self.assertIn(conn, db_pool._used.values())

            # Thực hiện khối try...finally
            try:
                # Mô phỏng thao tác database thành công
                pass
            finally:
                init_db.release_db_connection(conn)

            # Kết nối phải được trả về pool và không còn nằm trong _used
            self.assertNotIn(conn, db_pool._used.values())
            self.assertIn(conn, db_pool._pool)

    def test_connection_release_in_finally_on_exception(self):
        """Xác minh kết nối được giải phóng an toàn trong finally ngay cả khi xảy ra Exception."""
        with patch("init_db.psycopg2.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_conn.closed = 0
            mock_connect.return_value = mock_conn

            db_pool = init_db.get_db_pool(minconn=2, maxconn=5)
            conn = init_db.get_db_connection()
            self.assertIn(conn, db_pool._used.values())

            # Mô phỏng lỗi xảy ra trong khối try
            with self.assertRaises(RuntimeError):
                try:
                    raise RuntimeError("Lỗi truy vấn SQL giả lập")
                finally:
                    init_db.release_db_connection(conn)

            # Kết nối vẫn phải được hoàn trả về pool đầy đủ
            self.assertNotIn(conn, db_pool._used.values())
            self.assertIn(conn, db_pool._pool)

    def test_continuous_sequential_requests_stability(self):
        """Kiểm thử chuỗi 50 request liên tục tuần tự, xác nhận tái sử dụng pool không cạn kiệt."""
        with patch("init_db.psycopg2.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_conn.closed = 0
            cursor = MagicMock()
            cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = cursor
            mock_connect.return_value = mock_conn

            db_pool = init_db.get_db_pool(minconn=2, maxconn=5)

            # Chạy chuỗi 50 requests liên tiếp gọi API
            for i in range(50):
                response = self.client.get("/api/products")
                self.assertEqual(response.status_code, 200)

            # Toàn bộ kết nối được giải phóng, không kết nối nào bị rò rỉ trong _used
            self.assertEqual(len(db_pool._used), 0)
            self.assertGreaterEqual(len(db_pool._pool), 2)

    def test_concurrent_multithreaded_requests_stability(self):
        """Kiểm thử tính ổn định của pool khi các luồng đồng thời gửi request liên tục (50 tổng requests)."""
        peak_used = 0
        used_lock = threading.Lock()

        def fake_connect(*args, **kwargs):
            c = MagicMock()
            c.closed = 0
            cur = MagicMock()
            cur.fetchall.return_value = [
                {"id": 1, "sku": "SKU-01", "name": "Test", "quantity": 10, "min_threshold": 5}
            ]
            c.cursor.return_value = cur
            return c

        with patch("init_db.psycopg2.connect", side_effect=fake_connect):
            db_pool = init_db.get_db_pool(minconn=2, maxconn=5)

            def make_request(req_id):
                nonlocal peak_used
                client = inventory_app.app.test_client()
                with used_lock:
                    current_active = len(db_pool._used)
                    if current_active > peak_used:
                        peak_used = current_active
                resp = client.get("/api/products")
                return resp.status_code

            # Chạy 50 requests qua ThreadPoolExecutor với 10 worker threads đồng thời
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request, i) for i in range(50)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            # 100% request phải thành công HTTP 200
            self.assertEqual(len(results), 50)
            self.assertTrue(all(code == 200 for code in results))

            # Số kết nối đồng thời tại mọi thời điểm không được vượt quá maxconn = 5
            self.assertLessEqual(peak_used, 5)
            # Sau khi toàn bộ các luồng hoàn tất, toàn bộ kết nối phải được giải phóng về pool (_used = 0)
            self.assertEqual(len(db_pool._used), 0)
            self.assertGreaterEqual(len(db_pool._pool), 2)

    def test_pool_exhaustion_raises_and_returns_503(self):
        """Kiểm tra khi pool đạt trần 5 kết nối và cạn kiệt, hệ thống bắt PoolError và trả về HTTP 503."""
        with patch.dict("os.environ", {"DB_POOL_TIMEOUT": "0.1"}):
            with patch("init_db.psycopg2.connect") as mock_connect:
                conns = []
                for _ in range(5):
                    c = MagicMock()
                    c.closed = 0
                    conns.append(c)
                mock_connect.side_effect = conns

                db_pool = init_db.get_db_pool(minconn=2, maxconn=5)

                # Rút cạn 5 kết nối từ pool
                checked_out = [db_pool.getconn() for _ in range(5)]
                self.assertEqual(len(checked_out), 5)

                # Request thứ 6 gọi API sẽ gặp PoolError vì hết kết nối khả dụng
                response = self.client.get("/api/products")
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.headers.get("Retry-After"), "5")
                self.assertIn("tạm thời hết kết nối khả dụng", response.get_json()["error"])

                # Giải phóng các kết nối
                for c in checked_out:
                    db_pool.putconn(c)

                # Sau khi giải phóng, request mới hoạt động bình thường
                cursor = MagicMock()
                cursor.fetchall.return_value = []
                conns[0].cursor.return_value = cursor
                response_after = self.client.get("/api/products")
                self.assertEqual(response_after.status_code, 200)


if __name__ == "__main__":
    unittest.main()
