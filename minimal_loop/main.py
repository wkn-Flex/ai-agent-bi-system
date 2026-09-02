# -*- coding: utf-8 -*-
"""
最小闭环主程序：交互式Text-to-SQL
功能：输入自然语言问题 → LLM生成SQL → 执行SQL → 显示结果
使用方式：python main.py
"""
from sql_generator import SQLGenerator
from sql_executor import get_sql_executor


def main():
    print('=' * 70)
    print('  基于AI Agent的BI自动化数据分析 - 最小闭环（Text-to-SQL）')
    print('=' * 70)
    print()
    print('  功能：输入自然语言问题，自动生成SQL并执行查询')
    print('  输入 "exit" 或 "quit" 退出程序')
    print('  输入 "schema" 查看数据库Schema')
    print()

    # 初始化
    generator = SQLGenerator()
    executor = get_sql_executor()

    while True:
        print('-' * 70)
        question = input('\n请输入你的问题: ').strip()

        if not question:
            continue

        if question.lower() in ('exit', 'quit', '退出'):
            print('\n再见！')
            break

        if question.lower() == 'schema':
            print('\n' + generator.schema_text)
            continue

        print(f'\n正在处理: {question}')
        print('-' * 70)

        # 生成SQL并执行（含self-correction重试）
        sql, result, attempts = generator.generate_with_retry(
            question=question,
            execute_func=executor.execute
        )

        print('-' * 70)
        if result is not None:
            # 显示结果
            print(f'\n最终SQL（第{attempts}次尝试成功）:')
            print(sql)
            print()
            print(executor.format_result(result))
        else:
            print(f'\n✗ 查询失败（尝试{attempts}次后仍未成功）')
            print(f'最后生成的SQL:\n{sql}')

        print()


if __name__ == '__main__':
    main()
