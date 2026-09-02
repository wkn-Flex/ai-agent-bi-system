# -*- coding: utf-8 -*-
"""
Superstore数据集导入MySQL脚本
功能：读取CSV → 数据清洗 → 去重 → 按4张表结构分批导入MySQL
导入顺序：customers → products → orders → order_items（外键依赖顺序）
"""
import pandas as pd
import pymysql
from datetime import datetime

# ========== 配置区（根据你的MySQL环境修改） ==========
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',           # 改成你的MySQL用户名
    'password': '123456',     # 改成你的MySQL密码
    'database': 'superstore_bi',
    'charset': 'utf8mb4',
}

CSV_PATH = r'E:\archive\Sample_ Superstore.csv'
BATCH_SIZE = 500  # 每批插入条数

# ========== 1. 读取并清洗数据 ==========
print('=' * 60)
print('Step 1: 读取CSV文件...')
df = pd.read_csv(CSV_PATH, encoding='utf-8')
print(f'  原始数据: {len(df)} 行, {len(df.columns)} 列')

# 清洗日期字段（处理混合格式：MM-DD-YYYY 和 M/D/YYYY）
def parse_date(date_str):
    """统一解析日期为 YYYY-MM-DD 格式"""
    if pd.isna(date_str):
        return None
    date_str = str(date_str).strip()
    # 尝试多种格式
    for fmt in ['%m-%d-%Y', '%m/%d/%Y', '%-m/%-d/%Y', '%m-%d-%y', '%m/%d/%y']:
        try:
            return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    # 兜底：用pandas解析
    try:
        return pd.to_datetime(date_str, dayfirst=False).strftime('%Y-%m-%d')
    except Exception:
        print(f'  [警告] 无法解析日期: {date_str}')
        return None

df['order_date_clean'] = df['Order Date'].apply(parse_date)
df['ship_date_clean'] = df['Ship Date'].apply(parse_date)

# 统计日期解析失败数
order_date_fail = df['order_date_clean'].isna().sum()
ship_date_fail = df['ship_date_clean'].isna().sum()
print(f'  订单日期解析失败: {order_date_fail} 条')
print(f'  发货日期解析失败: {ship_date_fail} 条')

# 去除日期解析失败的行（如果有）
df = df.dropna(subset=['order_date_clean', 'ship_date_clean'])
print(f'  清洗后数据: {len(df)} 行')

# ========== 2. 拆分4张表数据并去重 ==========
print('\n' + '=' * 60)
print('Step 2: 拆分表数据并去重...')

# 2.1 customers表（按customer_id去重，保留第一条）
customers_df = df[['Customer ID', 'Segment', 'City', 'State', 'Region', 'Country']].copy()
customers_df = customers_df.drop_duplicates(subset=['Customer ID'], keep='first')
customers_df.columns = ['customer_id', 'segment', 'city', 'state', 'region', 'country']
print(f'  customers: {len(customers_df)} 条（去重后）')

# 2.2 products表（按product_id去重）
products_df = df[['Product ID', 'Product Name', 'Category', 'Sub-Category']].copy()
products_df = products_df.drop_duplicates(subset=['Product ID'], keep='first')
products_df.columns = ['product_id', 'product_name', 'category', 'sub_category']
print(f'  products: {len(products_df)} 条（去重后）')

# 2.3 orders表（按order_id去重）
orders_df = df[['Order ID', 'order_date_clean', 'ship_date_clean', 'Ship Mode', 'Customer ID']].copy()
orders_df = orders_df.drop_duplicates(subset=['Order ID'], keep='first')
orders_df.columns = ['order_id', 'order_date', 'ship_date', 'ship_mode', 'customer_id']
print(f'  orders: {len(orders_df)} 条（去重后）')

# 2.4 order_items表（保留全部，对应原始每一行）
order_items_df = df[['Order ID', 'Product ID', 'Sales', 'Quantity', 'Discount', 'Profit']].copy()
order_items_df.columns = ['order_id', 'product_id', 'sales', 'quantity', 'discount', 'profit']
print(f'  order_items: {len(order_items_df)} 条（全部保留）')

# ========== 3. 连接数据库 ==========
print('\n' + '=' * 60)
print('Step 3: 连接MySQL数据库...')

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print(f'  连接成功: {DB_CONFIG["host"]}:{DB_CONFIG["port"]}/{DB_CONFIG["database"]}')
except Exception as e:
    print(f'  [错误] 数据库连接失败: {e}')
    print('  请检查: 1) MySQL是否启动  2) 用户名密码是否正确  3) 数据库superstore_bi是否已创建')
    exit(1)

# ========== 4. 清空表数据（按外键依赖逆序） ==========
print('\n' + '=' * 60)
print('Step 4: 清空已有表数据...')
cursor.execute('SET FOREIGN_KEY_CHECKS = 0')
for table in ['order_items', 'orders', 'products', 'customers']:
    cursor.execute(f'TRUNCATE TABLE {table}')
    print(f'  已清空: {table}')
cursor.execute('SET FOREIGN_KEY_CHECKS = 1')
conn.commit()

# ========== 5. 分批插入数据 ==========
def batch_insert(cursor, table, columns, data_df, batch_size=BATCH_SIZE):
    """分批插入数据"""
    total = len(data_df)
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)
    sql = f'INSERT INTO {table} ({columns_str}) VALUES ({placeholders})'

    inserted = 0
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = data_df.iloc[start:end]
        values = [tuple(row) for row in batch.itertuples(index=False, name=None)]
        cursor.executemany(sql, values)
        inserted += len(values)
        print(f'  {table}: 已插入 {inserted}/{total} 条 ({inserted*100//total}%)')
    conn.commit()
    return inserted

print('\n' + '=' * 60)
print('Step 5: 分批导入数据...')

# 5.1 导入customers
print('\n  [1/4] 导入 customers...')
batch_insert(cursor, 'customers',
             ['customer_id', 'segment', 'city', 'state', 'region', 'country'],
             customers_df)

# 5.2 导入products
print('\n  [2/4] 导入 products...')
batch_insert(cursor, 'products',
             ['product_id', 'product_name', 'category', 'sub_category'],
             products_df)

# 5.3 导入orders
print('\n  [3/4] 导入 orders...')
batch_insert(cursor, 'orders',
             ['order_id', 'order_date', 'ship_date', 'ship_mode', 'customer_id'],
             orders_df)

# 5.4 导入order_items
print('\n  [4/4] 导入 order_items...')
batch_insert(cursor, 'order_items',
             ['order_id', 'product_id', 'sales', 'quantity', 'discount', 'profit'],
             order_items_df)

# ========== 6. 导入后验证 ==========
print('\n' + '=' * 60)
print('Step 6: 验证导入结果...')

tables = ['customers', 'products', 'orders', 'order_items']
expected = {
    'customers': len(customers_df),
    'products': len(products_df),
    'orders': len(orders_df),
    'order_items': len(order_items_df),
}

all_pass = True
for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    actual = cursor.fetchone()[0]
    exp = expected[table]
    status = '✓' if actual == exp else '✗'
    if actual != exp:
        all_pass = False
    print(f'  {status} {table}: 实际={actual}, 预期={exp}')

# 额外验证：外键完整性
cursor.execute('''
    SELECT COUNT(*) FROM orders o
    LEFT JOIN customers c ON o.customer_id = c.customer_id
    WHERE c.customer_id IS NULL
''')
orphan_orders = cursor.fetchone()[0]
print(f'\n  外键检查 - orders中无对应customer的记录: {orphan_orders} 条')

cursor.execute('''
    SELECT COUNT(*) FROM order_items oi
    LEFT JOIN orders o ON oi.order_id = o.order_id
    WHERE o.order_id IS NULL
''')
orphan_items_order = cursor.fetchone()[0]
print(f'  外键检查 - order_items中无对应order的记录: {orphan_items_order} 条')

cursor.execute('''
    SELECT COUNT(*) FROM order_items oi
    LEFT JOIN products p ON oi.product_id = p.product_id
    WHERE p.product_id IS NULL
''')
orphan_items_product = cursor.fetchone()[0]
print(f'  外键检查 - order_items中无对应product的记录: {orphan_items_product} 条')

# 数据抽样验证
print('\n  数据抽样（order_items前3条）:')
cursor.execute('SELECT id, order_id, product_id, sales, quantity, discount, profit FROM order_items LIMIT 3')
for row in cursor.fetchall():
    print(f'    {row}')

print('\n  数据抽样（销售额统计）:')
cursor.execute('SELECT SUM(sales), SUM(profit), AVG(discount) FROM order_items')
row = cursor.fetchone()
print(f'    总销售额: {row[0]:.2f}, 总利润: {row[1]:.2f}, 平均折扣: {row[2]:.4f}')

cursor.close()
conn.close()

print('\n' + '=' * 60)
if all_pass and orphan_orders == 0 and orphan_items_order == 0 and orphan_items_product == 0:
    print('  导入完成！所有验证通过 ✓')
else:
    print('  导入完成，但存在异常，请检查上方日志 ✗')
print('=' * 60)
