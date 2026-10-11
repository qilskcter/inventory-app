import unittest
from unittest.mock import MagicMock, patch

import psycopg2

import app as inventory_app


class InventoryApiTests(unittest.TestCase):
    def setUp(self):
        inventory_app.app.config.update(TESTING=True)
        self.client = inventory_app.app.test_client()

    def _connection(self, fetchone=None, fetchall=None):
        cursor = MagicMock()
        cursor.fetchone.side_effect = fetchone or []
        cursor.fetchall.return_value = fetchall or []
        connection = MagicMock()
        connection.cursor.return_value = cursor
        return connection, cursor

    def test_inventory_page_renders_products_and_flash_messages(self):
        product = {
            "id": 3,
            "sku": "SKU-3",
            "name": "Mouse",
            "quantity": 1,
            "min_threshold": 2,
        }
        connection, _ = self._connection(fetchall=[product])

        with self.client.session_transaction() as session:
            session["_flashes"] = [("success", "Đã cập nhật kho.")]

        with patch.object(inventory_app, "get_db_connection", return_value=connection):
            response = self.client.get("/")

        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("SKU-3", html)
        self.assertIn("Mouse", html)
        self.assertIn("Sắp hết", html)
        self.assertIn('value="IN"', html)
        self.assertIn('value="OUT"', html)
        self.assertIn("Đã cập nhật kho.", html)
        self.assertNotIn("with messages =", html)

    def test_inventory_page_shows_empty_state(self):
        connection, _ = self._connection(fetchall=[])

        with patch.object(inventory_app, "get_db_connection", return_value=connection):
            response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Kho chưa có sản phẩm", response.get_data(as_text=True))

    def test_create_product_returns_created_product_and_defaults(self):
        product = {
            "id": 7,
            "sku": "SKU-7",
            "name": "Keyboard",
            "quantity": 0,
            "min_threshold": 5,
        }
        connection, cursor = self._connection(fetchone=[product])

        with patch.object(inventory_app, "get_db_connection", return_value=connection):
            response = self.client.post(
                "/api/products", json={"sku": "SKU-7", "name": "Keyboard"}
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json(), product)
        self.assertEqual(cursor.execute.call_args.args[1], ("SKU-7", "Keyboard", 0, 5))
        connection.commit.assert_called_once()

    def test_create_product_rejects_negative_quantity(self):
        with patch.object(inventory_app, "get_db_connection") as get_connection:
            response = self.client.post(
                "/api/products",
                json={"sku": "SKU-7", "name": "Keyboard", "quantity": -1},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("quantity", response.get_json()["error"])
        get_connection.assert_not_called()

    def test_create_transaction_updates_stock_and_records_history(self):
        product = {
            "id": 3,
            "sku": "SKU-3",
            "name": "Mouse",
            "quantity": 12,
            "min_threshold": 2,
        }
        transaction = {
            "id": 15,
            "product_id": 3,
            "type": "IN",
            "quantity": 4,
        }
        connection, cursor = self._connection(fetchone=[product, transaction])

        with patch.object(inventory_app, "get_db_connection", return_value=connection):
            response = self.client.post(
                "/api/transactions",
                json={"product_id": 3, "type": "IN", "quantity": 4},
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json(), {"product": product, "transaction": transaction})
        self.assertIn("quantity = quantity + %s", cursor.execute.call_args_list[0].args[0])
        connection.commit.assert_called_once()

    def test_outbound_transaction_uses_atomic_stock_check(self):
        connection, cursor = self._connection(
            fetchone=[None, {"id": 3}]
        )

        with patch.object(inventory_app, "get_db_connection", return_value=connection):
            response = self.client.post(
                "/api/transactions",
                json={"product_id": 3, "type": "OUT", "quantity": 4},
            )

        self.assertEqual(response.status_code, 409)
        self.assertIn("vượt quá", response.get_json()["error"])
        update_sql = cursor.execute.call_args_list[0].args[0]
        self.assertIn("quantity >= %s", update_sql)
        self.assertEqual(len(cursor.execute.call_args_list), 2)
        connection.commit.assert_not_called()
        connection.rollback.assert_called_once()

    def test_patch_cannot_change_stock_outside_transaction_api(self):
        with patch.object(inventory_app, "get_db_connection") as get_connection:
            response = self.client.patch(
                "/api/products/3", json={"quantity": 99}
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("quantity", response.get_json()["error"])
        get_connection.assert_not_called()

    def test_patch_updates_product_metadata(self):
        product = {
            "id": 3,
            "sku": "SKU-3",
            "name": "Mouse",
            "quantity": 8,
            "min_threshold": 3,
        }
        connection, cursor = self._connection(fetchone=[product])

        with patch.object(inventory_app, "get_db_connection", return_value=connection):
            response = self.client.patch("/api/products/3", json={"name": "Mouse Pro"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), product)
        self.assertIn("name = %s", cursor.execute.call_args.args[0])
        self.assertEqual(cursor.execute.call_args.args[1], ("Mouse Pro", 3))
        connection.commit.assert_called_once()

    def test_delete_product_returns_no_content(self):
        connection, cursor = self._connection(fetchone=[{"id": 3}])

        with patch.object(inventory_app, "get_db_connection", return_value=connection):
            response = self.client.delete("/api/products/3")

        self.assertEqual(response.status_code, 204)
        self.assertIn("DELETE FROM products", cursor.execute.call_args.args[0])
        connection.commit.assert_called_once()

    def test_duplicate_sku_returns_conflict(self):
        connection, cursor = self._connection()
        cursor.execute.side_effect = psycopg2.IntegrityError("duplicate SKU")

        with patch.object(inventory_app, "get_db_connection", return_value=connection):
            response = self.client.post(
                "/api/products", json={"sku": "SKU-7", "name": "Keyboard"}
            )

        self.assertEqual(response.status_code, 409)
        connection.rollback.assert_called_once()

    def test_create_transaction_rejects_non_positive_quantity(self):
        with patch.object(inventory_app, "get_db_connection") as get_connection:
            response = self.client.post(
                "/api/transactions",
                json={"product_id": 3, "type": "OUT", "quantity": 0},
            )

        self.assertEqual(response.status_code, 400)
        get_connection.assert_not_called()

    def test_inventory_form_submits_inbound_transaction(self):
        product = {
            "id": 3,
            "sku": "SKU-3",
            "name": "Mouse",
            "quantity": 12,
            "min_threshold": 2,
        }
        transaction = {"id": 15}
        connection, cursor = self._connection(fetchone=[product, transaction])

        with patch.object(inventory_app, "get_db_connection", return_value=connection):
            response = self.client.post(
                "/transaction",
                data={"product_id": "3", "quantity": "4", "type": "IN"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn("quantity = quantity + %s", cursor.execute.call_args_list[0].args[0])
        self.assertEqual(cursor.execute.call_args_list[0].args[1], (4, 3))
        connection.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
