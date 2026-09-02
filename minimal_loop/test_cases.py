# -*- coding: utf-8 -*-
"""
测试用例集：10个不同难度的业务分析问题
用于自动测试Text-to-SQL系统的准确率
难度分级：简单(单表聚合)、中等(多表JOIN)、复杂(多步分析/子查询)
"""

TEST_CASES = [
    # ========== 简单难度（单表聚合，3个） ==========
    {
        'id': 1,
        'difficulty': '简单',
        'category': '销售概览',
        'question': '2023年全年总销售额是多少？',
        'expected_keywords': ['SUM', 'sales', 'order_date', '2023'],
        'description': '单表聚合，按年份过滤',
    },
    {
        'id': 2,
        'difficulty': '简单',
        'category': '产品分析',
        'question': '销售额最高的前5个产品名称是什么？',
        'expected_keywords': ['product_name', 'SUM', 'sales', 'ORDER BY', 'DESC', 'LIMIT'],
        'description': '单表聚合+排序+Top-N',
    },
    {
        'id': 3,
        'difficulty': '简单',
        'category': '异常预警',
        'question': '找出所有利润为负的订单，按亏损金额从大到小排序',
        'expected_keywords': ['profit', '<', '0', 'ORDER BY', 'ASC'],
        'description': '条件过滤+排序',
    },

    # ========== 中等难度（多表JOIN，4个） ==========
    {
        'id': 4,
        'difficulty': '中等',
        'category': '区域分析',
        'question': '哪个地区的总销售额最高？',
        'expected_keywords': ['region', 'SUM', 'sales', 'JOIN', 'GROUP BY', 'ORDER BY', 'DESC', 'LIMIT'],
        'description': '两表JOIN（customers+orders+order_items）+聚合+排序',
    },
    {
        'id': 5,
        'difficulty': '中等',
        'category': '客户分析',
        'question': '不同客户细分市场（Consumer/Corporate/Home Office）的平均订单金额分别是多少？',
        'expected_keywords': ['segment', 'AVG', 'sales', 'JOIN', 'GROUP BY'],
        'description': '两表JOIN+分组聚合+平均值',
    },
    {
        'id': 6,
        'difficulty': '中等',
        'category': '产品类别分析',
        'question': '三大产品类别（Furniture/Office Supplies/Technology）的总销售额和总利润分别是多少？',
        'expected_keywords': ['category', 'SUM', 'sales', 'profit', 'JOIN', 'GROUP BY'],
        'description': '两表JOIN+多指标聚合',
    },
    {
        'id': 7,
        'difficulty': '中等',
        'category': '时间趋势',
        'question': '2023年每个月的销售额是多少？按月份升序排列',
        'expected_keywords': ['MONTH', 'order_date', 'SUM', 'sales', 'GROUP BY', 'ORDER BY'],
        'description': '日期函数+按月分组+排序',
    },

    # ========== 复杂难度（多步分析/子查询/HAVING，3个） ==========
    {
        'id': 8,
        'difficulty': '复杂',
        'category': '业绩归因',
        'question': '2023年第四季度相比第三季度，销售额增长了多少？增长率是多少？',
        'expected_keywords': ['SUM', 'sales', 'QUARTER', '2023'],
        'description': '同比/环比计算，可能需要子查询或CASE WHEN',
    },
    {
        'id': 9,
        'difficulty': '复杂',
        'category': '亏损分析',
        'question': '哪些产品子类别总体是亏损的？按亏损总额从大到小排序，并显示亏损金额',
        'expected_keywords': ['sub_category', 'SUM', 'profit', 'GROUP BY', 'HAVING', 'ORDER BY'],
        'description': '分组聚合+HAVING过滤+排序',
    },
    {
        'id': 10,
        'difficulty': '复杂',
        'category': '综合分析',
        'question': '找出2023年销售额最高的前3个州，以及它们各自的客户数量和平均订单金额',
        'expected_keywords': ['state', 'SUM', 'sales', 'COUNT', 'DISTINCT', 'AVG', 'JOIN', 'GROUP BY', 'ORDER BY', 'LIMIT'],
        'description': '多表JOIN+多指标聚合+排序+Top-N',
    },
]


def get_test_cases_by_difficulty(difficulty=None):
    """按难度筛选测试用例"""
    if difficulty is None:
        return TEST_CASES
    return [tc for tc in TEST_CASES if tc['difficulty'] == difficulty]


def print_test_cases():
    """打印所有测试用例"""
    print('=' * 70)
    print(f'  测试用例集（共{len(TEST_CASES)}个）')
    print('=' * 70)
    for tc in TEST_CASES:
        print(f'\n[{tc["id"]}] 难度: {tc["difficulty"]} | 场景: {tc["category"]}')
        print(f'    问题: {tc["question"]}')
        print(f'    说明: {tc["description"]}')


if __name__ == '__main__':
    print_test_cases()
