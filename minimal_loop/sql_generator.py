# -*- coding: utf-8 -*-
"""
SQL生成模块
功能：构建Prompt → 调用LLM → 解析并返回SQL语句
支持self-correction：SQL执行失败时，将错误信息反馈给LLM重新生成
"""
import re
from llm_client import get_llm
from schema_manager import get_schema_manager
from config import FEW_SHOT_EXAMPLES, SQL_CONFIG


class SQLGenerator:
    """SQL生成器"""

    def __init__(self):
        self.llm = get_llm()
        self.schema_mgr = get_schema_manager()
        self.schema_text = self.schema_mgr.get_full_schema_text()
        print('[SQLGenerator] 初始化完成，Schema已加载')

    def _build_system_prompt(self):
        """构建系统提示词：角色设定+任务描述+输出格式要求"""
        return """你是一个专业的商业智能（BI）数据分析专家，擅长将用户的自然语言问题转换为准确的SQL查询语句。

## 你的任务
根据用户提供的业务问题，结合数据库Schema，生成可以直接执行的MySQL查询语句。

## 输出要求
1. 只输出SQL语句本身，不要输出任何解释、注释或Markdown代码块标记
2. SQL必须是标准MySQL语法
3. 只允许SELECT查询，禁止INSERT、UPDATE、DELETE、DROP、ALTER等写操作
4. 表名和字段名必须与Schema中完全一致
5. 多表查询必须使用JOIN，不要使用隐式连接（逗号分隔表名）
6. 聚合查询使用合适的GROUP BY
7. 排序使用ORDER BY，限制结果数量使用LIMIT
8. 日期字段使用YEAR()、MONTH()、DATE_FORMAT()等函数处理
9. 数值计算使用ROUND()保留合适小数位

## 注意事项
- 仔细理解用户问题中的业务术语，映射到正确的字段
- "销售额"对应 sales 字段，"利润"对应 profit 字段，"数量"对应 quantity 字段
- "折扣"对应 discount 字段（0-0.8的小数）
- 时间范围问题注意使用 order_date 字段
- 地区维度问题注意使用 customers 表的 region/state/city 字段
- 产品维度问题注意使用 products 表的 category/sub_category/product_name 字段"""

    def _build_user_prompt(self, question, error_msg=None):
        """
        构建用户提示词：Schema + 少样本示例 + 用户问题

        Args:
            question: 用户的自然语言问题
            error_msg: 上一次SQL执行的错误信息（用于self-correction）
        """
        parts = []

        # 1. 数据库Schema
        parts.append('## 数据库Schema')
        parts.append(self.schema_text)

        # 2. 少样本示例
        parts.append('## 示例参考')
        for i, example in enumerate(FEW_SHOT_EXAMPLES, 1):
            parts.append(f'示例{i}:')
            parts.append(f'  问题: {example["question"]}')
            parts.append(f'  SQL: {example["sql"]}')
        parts.append('')

        # 3. 错误信息（self-correction时使用）
        if error_msg:
            parts.append('## 上一次SQL执行错误')
            parts.append(f'错误信息: {error_msg}')
            parts.append('请根据错误信息修正SQL语句，只输出修正后的SQL。')
            parts.append('')

        # 4. 用户问题
        parts.append('## 用户问题')
        parts.append(question)
        parts.append('')
        parts.append('请生成对应的SQL查询语句:')

        return '\n'.join(parts)

    def _extract_sql(self, text):
        """
        从LLM回复中提取纯SQL语句
        处理可能的Markdown代码块、多余解释等情况
        """
        # 去除Markdown代码块标记
        text = re.sub(r'```sql\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text)
        text = re.sub(r'`', '', text)

        # 去除开头的"SQL:"等前缀
        text = re.sub(r'^(SQL|sql|查询语句|Query):\s*', '', text, flags=re.IGNORECASE)

        # 去除行内注释（-- 开头的行）
        lines = text.strip().split('\n')
        sql_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('--'):
                continue
            sql_lines.append(line)

        sql = '\n'.join(sql_lines).strip()

        # 如果包含分号，只取第一个语句
        if ';' in sql:
            sql = sql[:sql.index(';')]

        return sql.strip()

    def generate(self, question, error_msg=None):
        """
        生成SQL语句

        Args:
            question: 用户的自然语言问题
            error_msg: 上一次执行错误信息（可选，用于self-correction）

        Returns:
            str: 生成的SQL语句
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(question, error_msg)

        raw_response = self.llm.chat(system_prompt, user_prompt)
        sql = self._extract_sql(raw_response)

        return sql

    def generate_with_retry(self, question, execute_func):
        """
        生成SQL并执行，失败时自动重试（self-correction）

        Args:
            question: 用户的自然语言问题
            execute_func: SQL执行函数，接收SQL返回(成功标志, 结果或错误信息)

        Returns:
            tuple: (最终SQL, 执行结果, 重试次数)
        """
        error_msg = None
        for attempt in range(1, SQL_CONFIG['max_retry'] + 1):
            print(f'  [尝试 {attempt}/{SQL_CONFIG["max_retry"]}] 生成SQL...')
            sql = self.generate(question, error_msg)
            print(f'  生成的SQL:\n{sql}\n')

            success, result = execute_func(sql)

            if success:
                print(f'  ✓ SQL执行成功（第{attempt}次尝试）')
                return sql, result, attempt
            else:
                error_msg = result
                print(f'  ✗ SQL执行失败: {error_msg[:100]}')
                if attempt < SQL_CONFIG['max_retry']:
                    print(f'  正在尝试self-correction...\n')

        print(f'  ✗ 达到最大重试次数 {SQL_CONFIG["max_retry"]}，仍失败')
        return sql, None, SQL_CONFIG['max_retry']
