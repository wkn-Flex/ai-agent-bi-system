# -*- coding: utf-8 -*-
"""
SQL执行器模块
功能：安全执行SQL查询（只允许SELECT），返回格式化的结果
"""
import pymysql
from config import DB_CONFIG, SQL_CONFIG


class SQLExecutor:
    """SQL执行器，含安全检查和结果格式化"""

    # 禁止的SQL关键字（写操作）
    FORBIDDEN_KEYWORDS = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER',
        'CREATE', 'TRUNCATE', 'RENAME', 'GRANT', 'REVOKE',
        'SET', 'REPLACE', 'MERGE', 'CALL', 'EXECUTE',
    ]

    def __init__(self):
        self.conn = pymysql.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
        print('[SQLExecutor] 初始化成功，数据库连接已建立')

    def _check_security(self, sql):
        """
        SQL安全检查：只允许SELECT查询

        Returns:
            tuple: (是否安全, 错误信息)
        """
        if not sql or not sql.strip():
            return False, 'SQL语句为空'

        sql_upper = sql.upper().strip()

        # 必须以SELECT开头
        if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
            return False, f'只允许SELECT查询，当前语句以"{sql_upper[:20]}"开头'

        # 检查禁止的关键字
        for keyword in self.FORBIDDEN_KEYWORDS:
            # 使用单词边界匹配，避免误判（如SELECT中的字段名包含"update"）
            if f' {keyword} ' in f' {sql_upper} ' or f'\n{keyword} ' in f'\n{sql_upper}':
                return False, f'SQL包含禁止的写操作关键字: {keyword}'

        return True, None

    def execute(self, sql):
        """
        执行SQL查询

        Args:
            sql: SQL语句

        Returns:
            tuple: (是否成功, 结果数据或错误信息)
                成功时结果为 dict: {'columns': [...], 'rows': [...], 'row_count': int}
                失败时结果为错误信息字符串
        """
        # 安全检查
        if SQL_CONFIG['only_select']:
            safe, error = self._check_security(sql)
            if not safe:
                return False, f'安全检查失败: {error}'

        try:
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()

            # 限制返回行数
            if len(rows) > SQL_CONFIG['result_max_rows']:
                rows = rows[:SQL_CONFIG['result_max_rows']]

            columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []

            result = {
                'columns': columns,
                'rows': rows,
                'row_count': len(rows),
            }
            return True, result

        except pymysql.Error as e:
            error_msg = f'MySQL错误 [{e.args[0]}]: {e.args[1]}'
            return False, error_msg
        except Exception as e:
            return False, f'执行异常: {str(e)}'

    def format_result(self, result, max_display_rows=20):
        """
        将查询结果格式化为可读文本

        Args:
            result: execute()返回的结果dict
            max_display_rows: 最大显示行数

        Returns:
            str: 格式化后的文本
        """
        if not result or result['row_count'] == 0:
            return '查询结果为空（0行）'

        columns = result['columns']
        rows = result['rows']
        display_rows = rows[:max_display_rows]

        lines = []
        lines.append(f'查询结果: 共 {result["row_count"]} 行（显示前 {len(display_rows)} 行）')
        lines.append('')

        # 表头
        header = ' | '.join(columns)
        lines.append(header)
        lines.append('-' * len(header))

        # 数据行
        for row in display_rows:
            values = []
            for col in columns:
                val = row[col]
                if val is None:
                    values.append('NULL')
                elif isinstance(val, float):
                    values.append(f'{val:.4f}')
                else:
                    values.append(str(val))
            lines.append(' | '.join(values))

        if len(rows) > max_display_rows:
            lines.append('')
            lines.append(f'... 还有 {len(rows) - max_display_rows} 行未显示')

        return '\n'.join(lines)

    def close(self):
        """关闭数据库连接"""
        self.cursor.close()
        self.conn.close()
        print('[SQLExecutor] 数据库连接已关闭')


# 单例模式
_executor_instance = None

def get_sql_executor():
    """获取SQL执行器单例"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = SQLExecutor()
    return _executor_instance
