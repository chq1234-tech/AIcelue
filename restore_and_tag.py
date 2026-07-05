#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恢复备份的资金/股票/交易数据，并给所有交易记录添加 type='dca' 标签
"""
import os
import json
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(SCRIPT_DIR, 'backup_simul_20260704_113008')
BACKUP_FILE = os.path.join(BACKUP_DIR, 'dca_portfolio_data.json')
TARGET_FILE = os.path.join(SCRIPT_DIR, 'dca_portfolio_data.json')


def main():
    print("=" * 80)
    print("【恢复数据 + 添加定投标签】")
    print("=" * 80)

    # 1. 检查备份文件
    if not os.path.exists(BACKUP_FILE):
        print(f"[错误] 备份文件不存在: {BACKUP_FILE}")
        return False
    print(f"\n[1] 备份文件: {BACKUP_FILE}")
    print(f"    备份大小: {os.path.getsize(BACKUP_FILE)} bytes")

    # 2. 恢复备份
    shutil.copy2(BACKUP_FILE, TARGET_FILE)
    print(f"\n[2] 已恢复备份到: {TARGET_FILE}")

    # 3. 读取数据
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 4. 显示恢复后的状态
    print(f"\n[3] 恢复后持仓:")
    for code, h in data.get('holdings', {}).items():
        if h.get('shares', 0) > 0:
            print(f"    {code} {h.get('name','')}: {h['shares']}股, 成本{h['avg_cost']:.4f}, 总成本{h['total_cost']:.2f}")
    print(f"    现金余额: {data.get('cash_balance', 0):.2f}")
    print(f"    累计投入: {data.get('total_invested', 0):.2f}")

    # 5. 给所有交易记录添加 type='dca' 标签
    trades = data.get('trade_history', [])
    print(f"\n[4] 交易记录数: {len(trades)}")

    # 统计已有标签
    type_counts = {}
    for t in trades:
        ttype = t.get('type', None)
        type_counts[ttype] = type_counts.get(ttype, 0) + 1
    print(f"    修改前 type 分布: {type_counts}")

    # 给所有交易添加 type='dca'（对于已有 stop_profit/reinvest 的不动）
    # 用户要求"把所有的交易数据增加定投标签" → 全部设置为 dca
    modified_count = 0
    for t in trades:
        old_type = t.get('type', None)
        if old_type != 'dca':
            t['type'] = 'dca'
            modified_count += 1

    # 统计修改后标签
    type_counts_after = {}
    for t in trades:
        ttype = t.get('type', None)
        type_counts_after[ttype] = type_counts_after.get(ttype, 0) + 1
    print(f"    修改后 type 分布: {type_counts_after}")
    print(f"    已修改 {modified_count} 条交易记录")

    # 6. 保存
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n[5] 数据已保存到: {TARGET_FILE}")

    # 7. 验证
    print(f"\n[6] 验证 - 最近5条交易记录:")
    for t in trades[-5:]:
        print(f"    {t.get('type','N/A'):12} {t.get('timestamp','')} {t['code']} {t['name']}")

    print(f"\n{'=' * 80}")
    print(f"恢复 + 标签添加完成")
    print(f"{'=' * 80}")
    return True


if __name__ == '__main__':
    main()
