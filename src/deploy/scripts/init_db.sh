#!/usr/bin/env bash
# 首次建库：执行 schema.sql（容器内 postgres 已通过 initdb 挂载执行，
# 本脚本用于手动/CI 环境：psql 执行 DDL + alembic upgrade）
set -euo pipefail

DB_URL="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-pre}"
DB_PASSWORD="${POSTGRES_PASSWORD:-pre}"
DB_NAME="${POSTGRES_DB:-pre_spc}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_FILE="${SCRIPT_DIR}/../../docs/plagiarism-precheck/api/schema.sql"

echo "==> 执行 schema.sql (${DB_URL}:${DB_PORT}/${DB_NAME})"
PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_URL}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -v ON_ERROR_STOP=1 -f "${SCHEMA_FILE}"

echo "==> alembic upgrade head"
cd "${SCRIPT_DIR}/../../backend" && PYTHONPATH=.. alembic upgrade head

echo "==> 初始化完成"
