import unittest
from unittest.mock import MagicMock, patch

import psycopg2
from botocore.exceptions import ClientError

import app as inventory_app
import reports


class ReportExportTests(unittest.TestCase):
    def setUp(self):
        inventory_app.app.config.update(TESTING=True)
        self.client = inventory_app.app.test_client()

    def test_sanitize_csv_cell_prevents_formula_injection(self):
        dangerous_inputs = ["=SUM(A1:A10)", "+12345", "-CMD|'/C calc'!A0", "@calc", "\tcmd", "\rcmd"]
        for item in dangerous_inputs:
            with self.subTest(item=item):
                sanitized = reports.sanitize_csv_cell(item)
                self.assertTrue(sanitized.startswith("'"), f"Giá trị {item} phải được bắt đầu bằng dấu nháy đơn")

        # Chuỗi bình thường không bị thêm dấu nháy
        self.assertEqual(reports.sanitize_csv_cell("Bàn phím cơ"), "Bàn phím cơ")
        self.assertEqual(reports.sanitize_csv_cell("SKU-100"), "SKU-100")
        self.assertEqual(reports.sanitize_csv_cell(15), "15")
        self.assertEqual(reports.sanitize_csv_cell(None), "")

    def test_generate_inventory_csv_with_data(self):
        sample_products = [
            {
                "id": 1,
                "sku": "SKU-001",
                "name": "Chuột Gaming",
                "quantity": 10,
                "min_threshold": 5,
                "updated_at": "2026-10-22 10:00:00",
            },
            {
                "id": 2,
                "sku": "SKU-002",
                "name": "Bàn phím cơ",
                "quantity": 2,
                "min_threshold": 5,
                "updated_at": "2026-10-22 11:00:00",
            },
        ]

        csv_content = reports.generate_inventory_csv(sample_products)
        lines = csv_content.strip().split("\r\n") if "\r\n" in csv_content else csv_content.strip().split("\n")

        self.assertEqual(len(lines), 3)  # 1 header + 2 dòng dữ liệu
        self.assertIn("Mã ID,Mã SKU,Tên sản phẩm,Số lượng tồn kho,Ngưỡng an toàn,Trạng thái cảnh báo,Cập nhật lần cuối", lines[0])
        self.assertIn("SKU-001", lines[1])
        self.assertIn("Bình thường", lines[1])
        self.assertIn("SKU-002", lines[2])
        self.assertIn("Cảnh báo hết hàng", lines[2])

    def test_generate_inventory_csv_empty(self):
        csv_content = reports.generate_inventory_csv([])
        lines = csv_content.strip().splitlines()
        self.assertEqual(len(lines), 1)  # Chỉ có dòng header
        self.assertIn("Mã ID,Mã SKU", lines[0])

    def test_api_export_inventory_csv_endpoint(self):
        sample_products = [
            {
                "id": 1,
                "sku": "SKU-001",
                "name": "Chuột Gaming",
                "quantity": 10,
                "min_threshold": 5,
                "updated_at": "2026-10-22 10:00:00",
            }
        ]

        cursor = MagicMock()
        cursor.fetchall.return_value = sample_products
        connection = MagicMock()
        connection.cursor.return_value = cursor

        with patch.object(inventory_app, "get_db_connection", return_value=connection):
            response = self.client.get("/api/reports/inventory/csv")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.content_type)
        self.assertIn("attachment; filename=inventory_report_", response.headers.get("Content-Disposition", ""))
        body = response.get_data()
        # Xác nhận có UTF-8 BOM
        self.assertTrue(body.startswith(b"\xef\xbb\xbf"))
        text = body.decode("utf-8-sig")
        self.assertIn("SKU-001", text)
        self.assertIn("Chuột Gaming", text)

    def test_upload_report_to_s3_success(self):
        mock_s3 = MagicMock()
        csv_text = "Mã ID,Mã SKU\n1,SKU-01"

        res = reports.upload_report_to_s3(
            csv_content=csv_text,
            bucket_name="test-inventory-bucket",
            region_name="us-east-1",
            s3_client=mock_s3,
        )

        self.assertEqual(res["bucket"], "test-inventory-bucket")
        self.assertTrue(res["key"].startswith("inventory_reports/inventory_report_"))
        self.assertTrue(res["key"].endswith(".csv"))

        mock_s3.put_object.assert_called_once()
        call_kwargs = mock_s3.put_object.call_args.kwargs
        self.assertEqual(call_kwargs["Bucket"], "test-inventory-bucket")
        self.assertEqual(call_kwargs["ContentType"], "text/csv; charset=utf-8")
        self.assertEqual(call_kwargs["ServerSideEncryption"], "AES256")
        self.assertEqual(call_kwargs["Metadata"]["report_type"], "inventory_stock")
        self.assertTrue(call_kwargs["Body"].startswith(b"\xef\xbb\xbf"))

    def test_upload_report_to_s3_missing_bucket_raises_error(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "Chưa cấu hình tên S3 Bucket"):
                reports.upload_report_to_s3("data", bucket_name=None)

    def test_api_export_s3_success(self):
        sample_products = [
            {"id": 1, "sku": "SKU-001", "name": "Chuột Gaming", "quantity": 10, "min_threshold": 5, "updated_at": "2026-10-22"}
        ]
        cursor = MagicMock()
        cursor.fetchall.return_value = sample_products
        connection = MagicMock()
        connection.cursor.return_value = cursor

        mock_upload_result = {
            "bucket": "inventory-reports-bucket",
            "key": "inventory_reports/inventory_report_20261022_120000.csv",
            "size_bytes": 1024,
            "timestamp": "20261022_120000",
        }

        with patch.object(inventory_app, "get_db_connection", return_value=connection):
            with patch("app.upload_report_to_s3", return_value=mock_upload_result):
                response = self.client.post("/api/reports/inventory/export-s3")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("lưu trữ an toàn vào Amazon S3", data["message"])
        self.assertEqual(data["s3_bucket"], "inventory-reports-bucket")
        self.assertEqual(data["total_records"], 1)

    def test_api_export_s3_error_returns_clean_response(self):
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        connection = MagicMock()
        connection.cursor.return_value = cursor

        with patch.object(inventory_app, "get_db_connection", return_value=connection):
            with patch("app.upload_report_to_s3", side_effect=RuntimeError("S3 Access Denied")):
                response = self.client.post("/api/reports/inventory/export-s3")

        self.assertEqual(response.status_code, 502)
        self.assertIn("Không thể lưu trữ báo cáo vào Amazon S3", response.get_json()["error"])
        self.assertNotIn("Access Denied", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
