import os
import psycopg2

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "inventory_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "123456")
DB_PORT = os.environ.get("DB_PORT", "5432")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )

def init_db(schema_file=os.path.join("database", "schema.sql")):
    """Đọc file schema.sql và khởi tạo các bảng CSDL."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(base_dir, schema_file)

        # Trường hợp fallback nếu file ở thư mục gốc
        if not os.path.exists(schema_path):
            fallback_path = os.path.join(base_dir, "schema.sql")
            if os.path.exists(fallback_path):
                schema_path = fallback_path
            else:
                print(f"LỖI: Không tìm thấy file schema tại '{schema_path}'")
                return

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(schema_sql)
        conn.commit()
        cur.close()
        conn.close()
        print("KẾT NỐI VÀ KHỞI TẠO CSDL TỪ SCHEMA.SQL THÀNH CÔNG!")
    except Exception as e:
        print(f"LỖI KHỞI TẠO CSDL: {e}")

if __name__ == "__main__":
    init_db()
