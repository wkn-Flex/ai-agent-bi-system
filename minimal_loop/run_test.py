# -*- coding: utf-8 -*-
"""
自动测试脚本：运行所有测试用例，统计准确率
评估指标：
1. 执行成功率：SQL能否成功执行（含self-correction后）
2. 首次成功率：第一次生成的SQL就能成功执行的比例
3. 平均重试次数
4. 按难度分级统计
"""
import time
from sql_generator import SQLGenerator
from sql_executor import get_sql_executor
from test_cases import TEST_CASES


def run_all_tests():
    """运行所有测试用例"""
    print('=' * 70)
    print('  Text-to-SQL 系统自动测试')
    print('=' * 70)

    generator = SQLGenerator()
    executor = get_sql_executor()

    results = []
    total_start = time.time()

    for i, tc in enumerate(TEST_CASES, 1):
        print(f'\n{"-" * 70}')
        print(f'[{i}/{len(TEST_CASES)}] 难度: {tc["difficulty"]} | 场景: {tc["category"]}')
        print(f'问题: {tc["question"]}')
        print('-' * 70)

        start_time = time.time()
        sql, result, attempts = generator.generate_with_retry(
            question=tc['question'],
            execute_func=executor.execute
        )
        elapsed = time.time() - start_time

        success = result is not None
        first_try_success = (attempts == 1 and success)

        result_info = {
            'id': tc['id'],
            'difficulty': tc['difficulty'],
            'category': tc['category'],
            'question': tc['question'],
            'sql': sql,
            'success': success,
            'first_try_success': first_try_success,
            'attempts': attempts,
            'elapsed': elapsed,
            'row_count': result['row_count'] if success else 0,
        }
        results.append(result_info)

        status = '✓ 成功' if success else '✗ 失败'
        print(f'\n结果: {status} | 尝试次数: {attempts} | 耗时: {elapsed:.1f}s | 返回行数: {result_info["row_count"]}')
        if success:
            print(f'SQL:\n{sql}')

    total_elapsed = time.time() - total_start

    # ========== 统计结果 ==========
    print('\n' + '=' * 70)
    print('  测试结果统计')
    print('=' * 70)

    total = len(results)
    success_count = sum(1 for r in results if r['success'])
    first_try_count = sum(1 for r in results if r['first_try_success'])
    total_attempts = sum(r['attempts'] for r in results)
    avg_attempts = total_attempts / total if total > 0 else 0
    avg_elapsed = total_elapsed / total if total > 0 else 0

    print(f'\n总测试用例数: {total}')
    print(f'执行成功率: {success_count}/{total} = {success_count*100/total:.1f}%')
    print(f'首次成功率: {first_try_count}/{total} = {first_try_count*100/total:.1f}%')
    print(f'平均重试次数: {avg_attempts:.2f}')
    print(f'平均耗时: {avg_elapsed:.1f}s/题')
    print(f'总耗时: {total_elapsed:.1f}s')

    # 按难度分级统计
    print(f'\n{"-" * 70}')
    print('  按难度分级统计')
    print('-' * 70)

    for difficulty in ['简单', '中等', '复杂']:
        diff_results = [r for r in results if r['difficulty'] == difficulty]
        if not diff_results:
            continue
        diff_total = len(diff_results)
        diff_success = sum(1 for r in diff_results if r['success'])
        diff_first = sum(1 for r in diff_results if r['first_try_success'])
        diff_avg_attempts = sum(r['attempts'] for r in diff_results) / diff_total
        print(f'\n  {difficulty} ({diff_total}题):')
        print(f'    执行成功率: {diff_success}/{diff_total} = {diff_success*100/diff_total:.1f}%')
        print(f'    首次成功率: {diff_first}/{diff_total} = {diff_first*100/diff_total:.1f}%')
        print(f'    平均重试次数: {diff_avg_attempts:.2f}')

    # 失败用例详情
    failed = [r for r in results if not r['success']]
    if failed:
        print(f'\n{"-" * 70}')
        print('  失败用例详情')
        print('-' * 70)
        for r in failed:
            print(f'\n  [{r["id"]}] {r["difficulty"]} - {r["question"]}')
            print(f'    尝试次数: {r["attempts"]}')
            print(f'    最后SQL:\n{r["sql"]}')

    # 成功用例的SQL示例
    print(f'\n{"-" * 70}')
    print('  成功用例SQL示例（前3个）')
    print('-' * 70)
    success_results = [r for r in results if r['success']][:3]
    for r in success_results:
        print(f'\n  [{r["id"]}] {r["question"]}')
        print(f'  {r["sql"]}')

    print('\n' + '=' * 70)
    print('  测试完成')
    print('=' * 70)

    return results


if __name__ == '__main__':
    run_all_tests()
