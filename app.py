from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Cấu hình kết nối PostgreSQL
DB_HOST = "localhost"
DB_NAME = "inventory_db"
DB_USER = "postgres"
DB_PASS = "123456"
DB_PORT = "5432"

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    return conn

# Khởi tạo Database và Bảng nếu chưa có
def init_db():
    try:
        conn = get_db_connection()
        print("KẾT NỐI POSTGRESQL THÀNH CÔNG!")
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                sku VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                quantity INT NOT NULL DEFAULT 0,
                min_threshold INT NOT NULL DEFAULT 5
            );
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                product_id INT REFERENCES products(id),
                type VARCHAR(10) NOT NULL, -- 'IN' hoặc 'OUT'
                quantity INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print(f"LỖI KẾT NỐI DATABASE: {e}")

# Trang chủ: Hiển thị danh sách sản phẩm
@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT * FROM products ORDER BY id ASC;')
    products = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', products=products)

# Thêm sản phẩm mới
@app.route('/add', methods=['POST'])
def add_product():
    sku = request.form['sku']
    name = request.form['name']
    quantity = int(request.form['quantity'])
    min_threshold = int(request.form['min_threshold'])
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO products (sku, name, quantity, min_threshold) VALUES (%s, %s, %s, %s)',
            (sku, name, quantity, min_threshold)
        )
        conn.commit()
        flash('Thêm sản phẩm thành công!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Lỗi: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('index'))

# Xử lý Nhập/Xuất kho
@app.route('/transaction', methods=['POST'])
def transaction():
    product_id = int(request.form['product_id'])
    trans_type = request.form['type']  # 'IN' hoặc 'OUT'
    trans_qty = int(request.form['quantity'])
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Lấy thông tin sản phẩm hiện tại
    cur.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cur.fetchone()
    
    if product:
        current_qty = product['quantity']
        if trans_type == 'IN':
            new_qty = current_qty + trans_qty
        else: # OUT
            if current_qty < trans_qty:
                flash('Số lượng xuất vượt quá tồn kho hiện tại!', 'danger')
                cur.close()
                conn.close()
                return redirect(url_for('index'))
            new_qty = current_qty - trans_qty
            
        # Cập nhật số lượng kho và ghi lịch sử giao dịch
        cur.execute('UPDATE products SET quantity = %s WHERE id = %s', (new_qty, product_id))
        cur.execute(
            'INSERT INTO transactions (product_id, type, quantity) VALUES (%s, %s, %s)',
            (product_id, trans_type, trans_qty)
        )
        conn.commit()
        
        # Kiểm tra ngưỡng cảnh báo tồn kho thấp
        if new_qty <= product['min_threshold']:
            flash(f"CẢNH BÁO: Sản phẩm '{product['name']}' đang dưới ngưỡng an toàn (Còn lại: {new_qty})!", 'warning')
        else:
            flash('Giao dịch thành công!', 'success')
            
    cur.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)