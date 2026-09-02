# -*- coding: utf-8 -*-
"""
数据库Schema管理：读取表结构并格式化为LLM可理解的描述
"""
import pymysql
from config import DB_CONFIG


class SchemaManager:
    def __init__(self):
        self.conn = pymysql.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        self._schema_cache = None

    def get_full_schema_text(self):
        if self._schema_cache is not None:
            return self._schema_cache

        self.cursor.execute("SHOW TABLES")
        tables = [row[0] for row in self.cursor.fetchall()]

        lines = [f'数据库: {DB_CONFIG["database"]}', f'表数量: {len(tables)}', '']

        for table_name in tables:
            self.cursor.execute(f"DESCRIBE `{table_name}`")
            columns = self.cursor.fetchall()

            self.cursor.execute("""
                SELECT TABLE_COMMENT FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """, (DB_CONFIG['database'], table_name))
            table_comment = self.cursor.fetchone()[0]

            self.cursor.execute("""
                SELECT COLUMN_NAME, COLUMN_COMMENT FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """, (DB_CONFIG['database'], table_name))
            comment_map = {row[0]: row[1] for row in self.cursor.fetchall()}

            lines.append(f'--- 表: {table_name} ({table_comment}) ---')
            lines.append('字段列表:')
            for col in columns:
                name, col_type, nullable, key = col[0], col[1], col[2], col[3]
                key_info = ' [主键]' if key == 'PRI' else (' [索引]' if key == 'MUL' else '')
                comment = f' -- {comment_map.get(name, "")}' if comment_map.get(name) else ''
                lines.append(f'  - {name} ({col_type}){key_info}{comment}')
            lines.append('')

        lines.append('--- 表关系 ---')
        lines.append('  - customers.customer_id -> orders.customer_id (1:N)')
        lines.append('  - orders.order_id -> order_items.order_id (1:N)')
        lines.append('  - products.product_id -> order_items.product_id (1:N)')
        lines.append('')

        self._schema_cache = '\n'.join(lines)
        return self._schema_cache

    def close(self):
        self.cursor.close()
        self.conn.close()


_schema_instance = None

def get_schema_manager():
    global _schema_instance
    if _schema_instance is None:
        _schema_instance = SchemaManager()
    return _schema_instance
