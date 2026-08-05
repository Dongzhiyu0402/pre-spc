#!/usr/bin/env bash
# M2 种子语料构建命令封装（THUCNews/维基 -> 清洗 -> 指纹 -> 入库）
# 无网络/无数据时使用内置 demo 语料跑通基准。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/../.."

SOURCE="${1:-demo}"   # demo | thucnews | wiki
INPUT="${2:-}"

cd "${PROJECT_ROOT}/src"
if [ "${SOURCE}" = "demo" ]; then
    echo "==> 构建内置 demo 语料索引"
    python - << 'EOF'
from engine.corpus.build import build_default_corpus, DEFAULT_INDEX_DIR
idx = build_default_corpus(DEFAULT_INDEX_DIR, force=True)
print(f"corpus docs: {idx.size()}")
EOF
elif [ -n "${INPUT}" ]; then
    echo "==> 从 ${INPUT} 构建语料（${SOURCE}）"
    PYTHONPATH=. python -m engine.corpus.build --source "${SOURCE}" --input "${INPUT}" --output src/engine/models/corpus_index
else
    echo "错误：${SOURCE} 模式需要 --input 数据目录" >&2
    exit 2
fi
