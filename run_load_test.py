"""
Script thực thi kiểm thử tải tự động với Locust (Headless Mode).
Mô phỏng 15 người dùng đồng thời (trong dải 10–20 người dùng) gửi request liên tục trong 45 giây.
Đo lường thời gian đáp ứng (latency), thông lượng (RPS) và tỷ lệ lỗi (failure rate).
"""

import csv
import os
import subprocess
import sys

HOST = os.environ.get(
    "TARGET_HOST",
    "http://inventory-env-py312.eba-vbehyxmh.us-east-1.elasticbeanstalk.com",
)
USERS = int(os.environ.get("LOAD_USERS", "15"))  # Mô phỏng 15 users (trong dải 10–20)
SPAWN_RATE = int(os.environ.get("LOAD_SPAWN_RATE", "3"))  # 3 users/giây
RUN_TIME = os.environ.get("LOAD_RUN_TIME", "40s")  # Thời lượng 40 giây

OUTPUT_DIR = os.path.join("documents", "week_4")
CSV_PREFIX = os.path.join(OUTPUT_DIR, "load_test_stats")
HTML_REPORT = os.path.join(OUTPUT_DIR, "load_test_report.html")

PYTHON_EXEC = sys.executable

cmd = [
    PYTHON_EXEC,
    "-m",
    "locust",
    "-f",
    "locustfile.py",
    "--headless",
    "--host",
    HOST,
    "-u",
    str(USERS),
    "-r",
    str(SPAWN_RATE),
    "--run-time",
    RUN_TIME,
    "--csv",
    CSV_PREFIX,
    "--html",
    HTML_REPORT,
    "--loglevel",
    "INFO",
]

print("================================================================================")
print(f"BẮT ĐẦU KIỂM THỬ TẢI NHẸ VỚI LOCUST:")
print(f" - Target Host: {HOST}")
print(f" - Concurrent Users: {USERS} (Mô phỏng 10–20 người dùng đồng thời)")
print(f" - Spawn Rate: {SPAWN_RATE} users/sec")
print(f" - Duration: {RUN_TIME}")
print(f" - Output CSV: {CSV_PREFIX}_*.csv")
print(f" - Output HTML: {HTML_REPORT}")
print("================================================================================")

result = subprocess.run(cmd)

print("\n================================================================================")
print("KẾT THÚC PHIÊN TEST TẢI. TỔNG HỢP KẾT QUẢ ĐO LƯỜNG:")
print("================================================================================")

stats_csv = f"{CSV_PREFIX}_stats.csv"
if os.path.exists(stats_csv):
    try:
        import csv
        with open(stats_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                print(" | ".join(row))
    except Exception as e:
        print(f"Lỗi đọc file CSV kết quả: {e}")
else:
    print(f"Không tìm thấy file kết quả tại: {stats_csv}")
