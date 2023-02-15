import sqlite3




def start():
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS products(
    product_id INTEGER PRIMARY KEY,
    company_name TEXT,
    model_name TEXT,
    price INTEGER,
    description TEXT);''')
    cur.execute('''CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER,
    balance INTEGER,
    korzina TEXT);''')
    cur.execute('''CREATE TABLE IF NOT EXISTS payments(
    bill_id TEXT,
    payer_id INTEGER,
    amount INTEGER,
    status  TEXT);''')
    conn.commit()

def add_product(company_name, model_name, price):
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute(f'''INSERT INTO products(company_name, model_name, price) VALUES ('{company_name}', '{model_name}', {price});''')
    conn.commit()
def get_product_by_id(product_id):
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute(f'''SELECT * FROM products WHERE product_id = {product_id};''')
    data = cur.fetchall()[0]
    return data
def create_user(user_id):
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute(f'''SELECT * FROM users WHERE user_id = {user_id}''')
    if cur.fetchall():
        return
    cur.execute(f'''INSERT INTO users(user_id, balance, korzina) VALUES ({user_id}, 0, '');''')
    conn.commit()
def create_payment(bill_id, payer_id, amount):
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute(f'''INSERT INTO payments(bill_id, payer_id, amount, status) VALUES ('{bill_id}', {payer_id}, {amount}, 'active');''')
    conn.commit()
def confirm_payment(bill_id, user_id):
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute(f'''SELECT * FROM payments WHERE bill_id = '{bill_id}';''')
    amount = cur.fetchall()[0][2]
    cur.execute(f'''SELECT * FROM users WHERE user_id = {user_id};''')
    balance = cur.fetchall()[0][1]
    cur.execute(f'''UPDATE payments SET status = 'confirmed' WHERE bill_id = '{bill_id}';''')
    cur.execute(f'''UPDATE users SET balance = {balance+amount} WHERE user_id = {user_id};''')
    conn.commit()
def check_existing_payments(user_id):
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute(f'''SELECT * FROM payments WHERE payer_id = {user_id} and status = 'active';''')
    if cur.fetchall():
        return True
    else:
        return False
def add_product_to_korzina(product_id, user_id):
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute(f'''SELECT * FROM users WHERE user_id = {user_id};''')
    data = cur.fetchall()[0][2]
    data += f' {product_id}'
    cur.execute(f'''UPDATE users SET korzina = {data} WHERE user_id = {user_id};''')
    conn.commit()
def get_company_names():
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute(f'''SELECT * FROM products''')
    data = cur.fetchall()
    data = set([i[1] for i in data])
    return data
def get_company_products(company_name):
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute(f'''SELECT * FROM products WHERE company_name = '{company_name}';''')
    data = cur.fetchall()
    return data
def get_user(user_id):
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute(f'''SELECT * FROM users WHERE user_id = {user_id}''')
def clean_korzina(user_id):
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute(f'''UPDATE users SET korzina = '' WHERE user_id = {user_id};''')
    conn.commit()
def spend_balance(user_id, cost):
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute(f'''SELECT * FROM users WHERE user_id = {user_id};''')
    balance = cur.fetchall()[ 0 ][ 1 ]
    cur.execute(f'''UPDATE USERS SET balance = {balance-cost} WHERE user_id = {user_id};''')
    conn.commit()
def create_korzina_txt(user_id):
    conn = sqlite3.connect('main.db')
    cur = conn.cursor()
    cur.execute(f'''SELECT * FROM users WHERE user_id = {user_id};''')
    products = list()
    korzina = cur.fetchall()[0][2]
    for product_id in korzina.split():
        product = get_product_by_id(int(product_id))
        products.append(f'{product[1]}: {product[2]}')
    return '\n'.join(products)
