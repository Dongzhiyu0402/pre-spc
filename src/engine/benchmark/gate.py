"""门禁判定：全部指标达标返回 0，否则非 0（可接入 CI）。

用法：python -m engine.benchmark.gate --input reports/benchmark_cnki.json \
      --mae-max 15 --spearman-min 0.6 --recall-min 0.7 --p95-max 30000
"""

import argparse
import json
import sys


def evaluate(report: dict, mae_max: float, spearman_min: float, recall_min: float, p95_max: int) -> tuple[bool, list[str]]:
    """判定基准报告是否达标。返回 (pass, [失败原因])。"""
    failures: list[str] = []
    if report.get("mae_raw", 999) > mae_max:
        failures.append(f"MAE {report.get('mae_raw')} > {mae_max}")
    if report.get("spearman_raw", -1) < spearman_min:
        failures.append(f"Spearman {report.get('spearman_raw')} < {spearman_min}")
    if report.get("recall_dup", 0) < recall_min:
        failures.append(f"Recall {report.get('recall_dup')} < {recall_min}")
    if report.get("p95_ms", 999999) > p95_max:
        failures.append(f"p95 {report.get('p95_ms')}ms > {p95_max}ms")
    return not failures, failures


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="引擎基准门禁判定")
    parser.add_argument("--input", required=True)
    parser.add_argument("--mae-max", type=float, default=15.0)
    parser.add_argument("--spearman-min", type=float, default=0.6)
    parser.add_argument("--recall-min", type=float, default=0.7)
    parser.add_argument("--p95-max", type=int, default=30000)
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as fh:
        report = json.load(fh)
    passed, failures = evaluate(report, args.mae_max, args.spearman_min, args.recall_min, args.p95_max)
    if passed:
        print(f"GATE PASS: {report.get('plan_code')} (MAE={report.get('mae_raw')}, Spearman={report.get('spearman_raw')}, Recall={report.get('recall_dup')}, p95={report.get('p95_ms')}ms)")
        sys.exit(0)
    print(f"GATE FAIL: {report.get('plan_code')}")
    for fail in failures:
        print(f"  - {fail}")
    sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
