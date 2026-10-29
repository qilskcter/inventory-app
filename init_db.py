import logging
import os
import threading
import time
import psycopg2
from psycopg2 import pool

logger = logging.getLogger(__name__)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "inventory_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD") or os.environ.get("DB_PASS")
DB_PORT = os.environ.get("DB_PORT", "5432")

# Ngưỡng kết nối Connection Pool (mặc định 2–5 kết nối theo yêu cầu dự án)
DB_POOL_MIN_CONN = int(os.environ.get("DB_POOL_MIN_CONN", "2"))
DB_POOL_MAX_CONN = int(os.environ.get("DB_POOL_MAX_CONN", "5"))
DB_POOL_TIMEOUT = float(os.environ.get("DB_POOL_TIMEOUT", "3.0"))

_db_pool = None
_pool_lock = threading.Lock()


def _get_connect_timeout():
    """Kiểm tra và lấy giá trị DB_CONNECT_TIMEOUT hợp lệ."""
    try:
        connect_timeout = int(os.environ.get("DB_CONNECT_TIMEOUT", "5"))
    except ValueError as error:
        raise ValueError("DB_CONNECT_TIMEOUT must be a positive integer") from error
    if connect_timeout < 1:
        raise ValueError("DB_CONNECT_TIMEOUT must be a positive integer")
    return connect_timeout


def _get_pool_limits():
    """Lấy giới hạn số kết nối minconn và maxconn cho Connection Pool."""
    try:
        minconn = int(os.environ.get("DB_POOL_MIN_CONN", str(DB_POOL_MIN_CONN)))
        maxconn = int(os.environ.get("DB_POOL_MAX_CONN", str(DB_POOL_MAX_CONN)))
    except ValueError as error:
        raise ValueError("DB_POOL_MIN_CONN và DB_POOL_MAX_CONN phải là số nguyên dương") from error
    if minconn < 1 or maxconn < minconn:
        raise ValueError("Giới hạn Connection Pool không hợp lệ: minconn >= 1 và maxconn >= minconn")
    return minconn, maxconn


def get_db_pool(minconn=None, maxconn=None):
    """
    Khởi tạo hoặc trả về ThreadedConnectionPool (Singleton thread-safe).
    Kích thước mặc định từ 2 đến 5 kết nối tái sử dụng cho các luồng ứng dụng.
    """
    global _db_pool

    # Luôn kiểm tra tính hợp lệ của timeout trước
    connect_timeout = _get_connect_timeout()

    if _db_pool is None or getattr(_db_pool, "closed", False):
        with _pool_lock:
            if _db_pool is None or getattr(_db_pool, "closed", False):
                default_min, default_max = _get_pool_limits()
                min_c = minconn if minconn is not None else default_min
                max_c = maxconn if maxconn is not None else default_max

                db_host = os.environ.get("DB_HOST", DB_HOST)
                db_name = os.environ.get("DB_NAME", DB_NAME)
                db_user = os.environ.get("DB_USER", DB_USER)
                db_pass = os.environ.get("DB_PASSWORD") or os.environ.get("DB_PASS") or DB_PASSWORD
                db_port = os.environ.get("DB_PORT", DB_PORT)

                logger.info(
                    "Đang khởi tạo ThreadedConnectionPool (minconn=%d, maxconn=%d, host=%s, db=%s, timeout=%ds)...",
                    min_c,
                    max_c,
                    db_host,
                    db_name,
                    connect_timeout,
                )
                _db_pool = pool.ThreadedConnectionPool(
                    min_c,
                    max_c,
                    host=db_host,
                    database=db_name,
                    user=db_user,
                    password=db_pass,
                    port=db_port,
                    connect_timeout=connect_timeout,
                )
                logger.info(
                    "Khởi tạo ThreadedConnectionPool thành công (minconn=%d, maxconn=%d).",
                    min_c,
                    max_c,
                )
    return _db_pool


def close_db_pool():
    """Đóng toàn bộ kết nối trong Connection Pool khi shutdown hoặc kết thúc kiểm thử."""
    global _db_pool
    with _pool_lock:
        if _db_pool is not None:
            try:
                if not getattr(_db_pool, "closed", False):
                    logger.info("Đang đóng ThreadedConnectionPool và giải phóng toàn bộ socket kết nối...")
                    _db_pool.closeall()
                    logger.info("Đã đóng hoàn tất ThreadedConnectionPool.")
            except Exception as error:
                logger.warning("Lỗi khi đóng ThreadedConnectionPool: %s", error)
            finally:
                _db_pool = None


def get_db_connection(timeout=None):
    """
    Lấy một kết nối từ ThreadedConnectionPool.
    Nếu pool chưa khởi tạo, tự động khởi tạo pool với kích thước 2–5 kết nối.
    Nếu pool tạm thời đạt trần kết nối (maxconn), đợi tối đa timeout giây (mặc định 3.0s)
    để các luồng khác hoàn thành tác vụ và giải phóng kết nối trong finally.
    """
    pool_instance = get_db_pool()
    wait_timeout = timeout if timeout is not None else float(os.environ.get("DB_POOL_TIMEOUT", str(DB_POOL_TIMEOUT)))
    start_time = time.time()

    while True:
        try:
            conn = pool_instance.getconn()
            logger.info("Lấy connection từ ThreadedConnectionPool thành công.")
            return conn
        except pool.PoolError as error:
            elapsed = time.time() - start_time
            if elapsed >= wait_timeout:
                logger.error(
                    "Connection pool cạn kiệt (đạt trần %d kết nối) sau khi đợi %.2f giây: %s",
                    pool_instance.maxconn,
                    elapsed,
                    error,
                )
                raise
            time.sleep(0.02)


def release_db_connection(conn, close=False):
    """
    Giải phóng kết nối và hoàn trả lại cho Connection Pool.
    Nếu connection bị lỗi hoặc bị đóng, đặt close=True để pool loại bỏ socket hỏng.
    Nếu pool không khả dụng hoặc connection là đối tượng độc lập/mock, đóng kết nối trực tiếp.
    """
    if conn is None:
        return
    global _db_pool
    is_closed = getattr(conn, "closed", 0) != 0
    should_close = close or is_closed

    if _db_pool is not None and not getattr(_db_pool, "closed", False):
        used_conns = list(getattr(_db_pool, "_used", {}).values())
        if conn in used_conns:
            try:
                _db_pool.putconn(conn, close=should_close)
                logger.info(
                    "Giải phóng connection về ThreadedConnectionPool thành công (closed=%s).",
                    should_close,
                )
                return
            except Exception as error:
                logger.warning(
                    "Không thể trả connection về pool (%s), chuyển sang đóng trực tiếp.",
                    error,
                )

    try:
        conn.close()
        logger.info("Đã đóng kết nối trực tiếp.")
    except Exception as error:
        logger.debug("Lỗi khi đóng kết nối trực tiếp: %s", error)


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
        release_db_connection(conn)

    print("KẾT NỐI VÀ KHỞI TẠO CSDL TỪ SCHEMA.SQL THÀNH CÔNG!")


if __name__ == "__main__":
    init_db()
