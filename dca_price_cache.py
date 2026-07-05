#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价格缓存模块 — dca_price_cache.py

将实时行情查询改为「早市+收市」两趟更新，中间所有模块只读缓存。
缓存持久化到 dca_price_cache.json，每次显式调用 refresh_all() 才更新。

用法:
    from dca_price_cache import PriceCache
    pc = PriceCache()
    pc.refresh_all()            # 更新所有ETF价格
    price = pc.get('510300')    # 读缓存（当天有效）
    all_prices = pc.get_dict()  # {code: price, ...}
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional, List

# ============================================================
# 模块级单例（全局共享，各文件 import 拿到同一实例）
# ============================================================
_PRICE_CACHE_INSTANCE = None


def get_cache(data_dir: str = None) -> "PriceCache":
    """获取全局单例缓存实例"""
    global _PRICE_CACHE_INSTANCE
    if _PRICE_CACHE_INSTANCE is None:
        _PRICE_CACHE_INSTANCE = PriceCache(data_dir)
    return _PRICE_CACHE_INSTANCE


class PriceCache:
    """价格缓存：当天有效，显式刷新才更新"""

    CACHE_FILENAME = "dca_price_cache.json"

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.dirname(os.path.abspath(__file__))
        self._file = os.path.join(data_dir, self.CACHE_FILENAME)
        self._cache: Dict[str, dict] = {}  # {code: {price, timestamp, source, date}}
        self._load()

    # ── 持久化 ──────────────────────────────────────────────

    def _load(self):
        if os.path.exists(self._file):
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def _save(self):
        try:
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[价格缓存] 保存失败: {e}")

    # ── 读写 ────────────────────────────────────────────────

    def update(self, code: str, price: float, source: str = "api"):
        """写一条缓存"""
        now = datetime.now()
        self._cache[code] = {
            "price": price,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "source": source,
            "date": now.strftime("%Y-%m-%d"),
        }
        self._save()

    def get(self, code: str) -> Optional[float]:
        """
        读取缓存价格（仅当天有效）
        Returns:
            float — 价格
            None  — 无当天缓存
        """
        entry = self._cache.get(code)
        if entry and entry.get("date") == datetime.now().strftime("%Y-%m-%d"):
            return entry["price"]
        return None

    def get_dict(self) -> Dict[str, float]:
        """返回 {code: price} 仅含当天有效缓存"""
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            k: v["price"]
            for k, v in self._cache.items()
            if v.get("date") == today
        }

    def has_valid_cache(self, code: str = None) -> bool:
        """
        检查是否有当天有效缓存
        Args:
            code: 指定代码，None 则检查是否有任意
        """
        if code:
            return self.get(code) is not None
        today = datetime.now().strftime("%Y-%m-%d")
        return any(v.get("date") == today for v in self._cache.values())

    # ── 批量刷新 ────────────────────────────────────────────

    def refresh_all(self, etf_list: List[dict] = None) -> int:
        """
        刷新所有 ETF 价格到缓存 —— 唯一真正调行情的地方
        Args:
            etf_list: ETF 配置列表，默认从 dca_config 导入
        Returns:
            成功更新的 ETF 数量
        """
        if etf_list is None:
            from dca_config import ETF_PORTFOLIO as etf_list

        from dca_trading import get_etf_price

        count = 0
        for etf in etf_list:
            code = etf["code"]
            try:
                info = get_etf_price(code)
                if info.get("success"):
                    self.update(code, info["price"], info.get("source", "api"))
                    count += 1
                else:
                    print(f"  [价格缓存] {code} 获取失败: {info.get('error', '?')}")
            except Exception as e:
                print(f"  [价格缓存] {code} 异常: {e}")
        print(f"  [价格缓存] 刷新完成: {count}/{len(etf_list)} 个ETF已更新")
        return count

    # ── 信息 ────────────────────────────────────────────────

    def summary(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        valid = [k for k, v in self._cache.items() if v.get("date") == today]
        return f"价格缓存: {len(valid)} 个有效 (日期:{today})"


# ============================================================
# 便利函数（供外部 import 直接调用）
# ============================================================

def refresh_prices():
    """开市 / 收市时调用：刷新所有 ETF 价格缓存"""
    cache = get_cache()
    return cache.refresh_all()


def get_cached_price(code: str) -> Optional[float]:
    """读缓存价格"""
    return get_cache().get(code)


def get_all_cached_prices() -> Dict[str, float]:
    """读所有缓存"""
    return get_cache().get_dict()


if __name__ == "__main__":
    # 测试
    pc = PriceCache()
    print(f"当前缓存有效: {pc.has_valid_cache()}")
    print(f"缓存路径: {pc._file}")
    if not pc.has_valid_cache():
        print("无有效缓存，尝试刷新...")
        n = pc.refresh_all()
        print(f"刷新 {n} 个")
    print(pc.summary())
    for code, price in pc.get_dict().items():
        print(f"  {code}: {price}")
