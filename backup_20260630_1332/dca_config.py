#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定投组合配置
方案2：平衡型（适合大多数年轻人）
- 红利ETF：20%（515080）
- 宽基指数：40%（510300沪深300+510500中证500）
- 行业主题：25%（512760芯片+512010医药）
- 海外资产：15%（513100纳指）
"""

# 定投方案基本配置
DCA_CONFIG = {
    'monthly_amount': 3000,
    'commission_rate': 0.0001,
    'min_commission': 0,
    'min_shares': 100,
    'description': '平衡型定投方案 - 适合大多数年轻人'
}

# ==================== 止盈轮动配置 ====================
STOP_PROFIT_ROTATION_CONFIG = {
    'enabled': True,                # 是否启用止盈轮动
    'threshold': 0.20,              # 基础止盈阈值：20%盈利触发（用户可自定义）
    'use_dynamic_threshold': False, # 是否启用动态阈值调整
    'dynamic_threshold_config': {
        'market_volatility_factor': 0.5,    # 市场波动率系数（0-1，越高越敏感）
        'min_threshold': 0.15,               # 动态阈值下限
        'max_threshold': 0.30,               # 动态阈值上限
        'lookback_days': 20,                # 计算波动率的回溯天数
    },
    'per_etf_thresholds': {
        # 个别ETF的自定义止盈阈值（优先于全局阈值）
        # '515080': 0.25,  # 中证红利ETF波动较小，可设较高阈值
        # '512760': 0.18,  # 芯片ETF波动较大，可设较低阈值
    },
    'sell_ratio': 1.0,              # 卖出比例：100%（全部止盈）
    'reinvest_priority': 'underweight_category',  # 再投优先级：低配类别
    'min_hold_days': 30,            # 最低持有天数
    'freeze_days': 30,              # 止盈后冻结天数（避免同标的快速回购）
    'min_shares': 100,              # 最小交易单位
    'commission_rate': 0.0001,       # 交易佣金率
    'min_commission': 0.2,           # 最低佣金
    'check_time': '09:30',          # 每日检查时间
}

# 类别目标配比（与ETF_PORTFOLIO的allocation汇总一致）
CATEGORY_TARGETS = {
    '红利': 0.20,    # 515080
    '宽基': 0.40,    # 510300 + 510500
    '行业': 0.25,    # 512760 + 512010
    '海外': 0.15,    # 513100
}

# ETF配置列表
ETF_PORTFOLIO = [
    {
        'code': '515080',
        'name': '中证红利ETF',
        'category': '红利',
        'allocation': 0.2,
        'monthly_amount': 600,
    },
    {
        'code': '510300',
        'name': '沪深300ETF',
        'category': '宽基',
        'allocation': 0.2,
        'monthly_amount': 600,
    },
    {
        'code': '510500',
        'name': '中证500ETF',
        'category': '宽基',
        'allocation': 0.2,
        'monthly_amount': 600,
    },
    {
        'code': '512760',
        'name': '芯片ETF',
        'category': '行业',
        'allocation': 0.125,
        'monthly_amount': 400,
    },
    {
        'code': '512010',
        'name': '医药ETF',
        'category': '行业',
        'allocation': 0.125,
        'monthly_amount': 400,
    },
    {
        'code': '513100',
        'name': '纳指ETF',
        'category': '海外',
        'allocation': 0.15,
        'monthly_amount': 400,
    },
]
