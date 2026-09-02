# -*- coding: utf-8 -*-
"""
SQL执行器：安全执行SQL查询，含安全检查和结果格式化
"""
import pymysql
from config import DB_CONFIG, SYSTEM_CONFIG


class SQLExecutor:
    FORBIDDEN_KEYWORDS = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER',
        'CREATE', 'TRUNCATE', 'RENAME', 'GRANT', 'REVOKE',
        'SET', 'REPLACE', 'MERGE', 'CALL', 'EXECUTE',
    ]

    def __init__(self):
        self.conn = pymysql.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)

    def _check_security(self, sql):
        if not sql or not sql.strip():
            return False, 'SQL语句为空'
        sql_upper = sql.upper().strip()
        if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
            return False, f'只允许SELECT查询，当前语句以"{sql_upper[:20]}"开头'
        for keyword in self.FORBIDDEN_KEYWORDS:
            if f' {keyword} ' in f' {sql_upper} ' or f'\n{keyword} ' in f'\n{sql_upper}':
                return False, f'SQL包含禁止的写操作关键字: {keyword}'
        return True, None

    def execute(self, sql):
        if SYSTEM_CONFIG['only_select']:
            safe, error = self._check_security(sql)
            if not safe:
                return False, f'安全检查失败: {error}'
        try:
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            if len(rows) > SYSTEM_CONFIG['result_max_rows']:
                rows = rows[:SYSTEM_CONFIG['result_max_rows']]
            columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []
            result = {'columns': columns, 'rows': rows, 'row_count': len(rows)}
            return True, result
        except pymysql.Error as e:
            return False, f'MySQL错误 [{e.args[0]}]: {e.args[1]}'
        except Exception as e:
            return False, f'执行异常: {str(e)}'

    def close(self):
        self.cursor.close()
        self.conn.close()


_executor_instance = None

def get_sql_executor():
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = SQLExecutor()
    return _executor_instance
