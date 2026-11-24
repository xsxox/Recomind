# -*- coding: utf-8 -*-
"""评估指标单元测试。"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_V = os.path.join(ROOT, "vendor")
if os.path.isdir(_V) and _V not in sys.path:
    sys.path.insert(0, _V)

from evaluation.metrics import (coverage, diversity, evaluate_ranked, hit_rate,  # noqa: E402
                                ndcg_at_k, precision_at_k, recall_at_k)


def _run(tests):
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {name}: {exc}")
            failed += 1
    print(f"\n通过 {passed} 项，失败 {failed} 项")
    return failed


def t_precision():
    assert abs(precision_at_k([1, 2, 3, 4, 5], {2, 4}, 5) - 0.4) < 1e-9
    assert precision_at_k([1, 2, 3], {9}, 3) == 0.0
    assert precision_at_k([], {1}, 3) == 0.0


def t_recall():
    assert abs(recall_at_k([1, 2, 3, 4, 5], {2, 4, 6}, 5) - 2 / 3) < 1e-9
    assert recall_at_k([1], {}, 3) == 0.0


def t_hit_rate():
    assert hit_rate([1, 2, 3], {2}, 3) == 1.0
    assert hit_rate([1, 2, 3], {9}, 3) == 0.0


def t_ndcg():
    assert abs(ndcg_at_k([1, 2, 3], {1, 2, 3}, 3) - 1.0) < 1e-9


def t_coverage_diversity():
    assert abs(coverage([[1, 2, 3], [2, 3, 4]], 4) - 1.0) < 1e-9
    assert abs(diversity([[1, 2, 3]], lambda a, b: 1.0)) < 1e-9
    assert abs(diversity([[1, 2, 3]], lambda a, b: 0.0) - 1.0) < 1e-9


def t_evaluate_ranked():
    ranked = {1: [10, 11, 12], 2: [20, 21, 22]}
    heldout = {1: {11}, 2: {30}}
    m = evaluate_ranked(ranked, heldout, 3)
    assert abs(m["precision"] - 1 / 6) < 1e-9
    assert abs(m["recall"] - 0.5) < 1e-9
    assert abs(m["hit_rate"] - 0.5) < 1e-9


if __name__ == "__main__":
    sys.exit(_run([
        ("precision_at_k", t_precision),
        ("recall_at_k", t_recall),
        ("hit_rate", t_hit_rate),
        ("ndcg_at_k", t_ndcg),
        ("coverage / diversity", t_coverage_diversity),
        ("evaluate_ranked", t_evaluate_ranked),
    ]))
