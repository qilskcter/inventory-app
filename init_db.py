import os
import psycopg2

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "inventory_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD") or os.environ.get("DB_PASS")
DB_PORT = os.environ.get("DB_PORT", "5432")


def get_db_connection():
    try:
        connect_timeout = int(os.environ.get("DB_CONNECT_TIMEOUT", "5"))
    except ValueError as error:
        raise ValueError("DB_CONNECT_TIMEOUT must be a positive integer") from error
    if connect_timeout < 1:
        raise ValueError("DB_CONNECT_TIMEOUT must be a positive integer")

    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        connect_timeout=connect_timeout,
    )


def init_db(schema_file=os.path.join("database", "schema.sql")):
    """Đọc file schema.sql và khởi tạo các bảng CSDL."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base_dir, schema_file)

    if not os.path.exists(schema_path):
        fallback_path = os.path.join(base_dir, "schema.sql")
        if os.path.exists(fallback_path):
            schema_path = fallback_path
        else:
            raise FileNotFoundError(f"Không tìm thấy file schema tại '{schema_path}'")

    with open(schema_path, "r", encoding="utf-8") as schema_file_handle:
        schema_sql = schema_file_handle.read()

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("KẾT NỐI VÀ KHỞI TẠO CSDL TỪ SCHEMA.SQL THÀNH CÔNG!")

if __name__ == "__main__":
    init_db()
