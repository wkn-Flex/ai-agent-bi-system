# -*- coding: utf-8 -*-
"""
数据库Schema管理模块
功能：从MySQL读取表结构（表名、字段名、类型、注释），格式化为LLM可理解的Schema描述
"""
import pymysql
from config import DB_CONFIG


class SchemaManager:
    """数据库Schema管理器"""

    def __init__(self):
        self.conn = pymysql.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        self._schema_cache = None  # Schema缓存，避免重复查询
        print('[Schema] 初始化成功，数据库连接已建立')

    def get_all_tables(self):
        """获取数据库中所有表名"""
        self.cursor.execute("SHOW TABLES")
        return [row[0] for row in self.cursor.fetchall()]

    def get_table_schema(self, table_name):
        """
        获取单张表的结构信息

        Returns:
            list: 字段列表，每个元素为 dict {name, type, nullable, key, default, comment}
        """
        self.cursor.execute(f"DESCRIBE `{table_name}`")
        columns = []
        for row in self.cursor.fetchall():
            columns.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2],
                'key': row[3],
                'default': row[4],
                'extra': row[5],
            })

        # 获取表注释
        self.cursor.execute(f"""
            SELECT TABLE_COMMENT FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """, (DB_CONFIG['database'], table_name))
        table_comment = self.cursor.fetchone()[0]

        # 获取字段注释
        self.cursor.execute(f"""
            SELECT COLUMN_NAME, COLUMN_COMMENT FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """, (DB_CONFIG['database'], table_name))
        comment_map = {row[0]: row[1] for row in self.cursor.fetchall()}

        for col in columns:
            col['comment'] = comment_map.get(col['name'], '')

        return {
            'table_name': table_name,
            'table_comment': table_comment,
            'columns': columns,
        }

    def get_full_schema_text(self):
        """
        获取完整的数据库Schema文本描述（用于LLM Prompt）

        Returns:
            str: 格式化后的Schema描述文本
        """
        if self._schema_cache is not None:
            return self._schema_cache

        tables = self.get_all_tables()
        lines = []
        lines.append(f'数据库: {DB_CONFIG["database"]}')
        lines.append(f'表数量: {len(tables)}')
        lines.append('')

        for table_name in tables:
            schema = self.get_table_schema(table_name)
            lines.append(f'--- 表: {schema["table_name"]} ({schema["table_comment"]}) ---')
            lines.append(f'字段列表:')
            for col in schema['columns']:
                key_info = ''
                if col['key'] == 'PRI':
                    key_info = ' [主键]'
                elif col['key'] == 'MUL':
                    key_info = ' [索引]'
                comment = f' -- {col["comment"]}' if col['comment'] else ''
                lines.append(f'  - {col["name"]} ({col["type"]}){key_info}{comment}')
            lines.append('')

        # 添加表关系说明
        lines.append('--- 表关系 ---')
        lines.append('  - customers.customer_id → orders.customer_id (1:N)')
        lines.append('  - orders.order_id → order_items.order_id (1:N)')
        lines.append('  - products.product_id → order_items.product_id (1:N)')
        lines.append('')

        self._schema_cache = '\n'.join(lines)
        return self._schema_cache

    def get_sample_data(self, table_name, limit=3):
        """获取表的样本数据（用于帮助LLM理解数据格式）"""
        self.cursor.execute(f"SELECT * FROM `{table_name}` LIMIT {limit}")
        columns = [desc[0] for desc in self.cursor.description]
        rows = self.cursor.fetchall()
        return columns, rows

    def close(self):
        """关闭数据库连接"""
        self.cursor.close()
        self.conn.close()
        print('[Schema] 数据库连接已关闭')


# 单例模式
_schema_instance = None

def get_schema_manager():
    """获取Schema管理器单例"""
    global _schema_instance
    if _schema_instance is None:
        _schema_instance = SchemaManager()
    return _schema_instance
