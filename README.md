# pre-spc 预查重系统

面向大学生的低成本预查重工具：正式送检知网/维普/万方之前，先用本工具预估查重率（输出预估区间+置信度），通过用户回传真实查重报告持续校准，逐步逼近目标平台真实结果。

> 定位：送检前的"相对风险提示 + 趋势预测"，不承诺与知网完全一致（知网学术库不可获取）。

## 功能（MVP P0）

| 功能 | 说明 |
|------|------|
| 文档上传查重 | docx/txt/md/pdf，1 万字 30 秒内出结果 |
| 查重报告 | 预估中值+区间+置信度（误差带量规）、相似片段高亮（行业色义）、来源抽屉、导出 PDF/HTML、免责声明常驻 |
| 多方案切换 | 知网/维普/万方模拟 + API 适配层预留（配置可增删，无需发版） |
| 账号与用量 | 注册赠次数、积分、防滥用（超限 402） |
| 校准训练 | 回传真实查重报告 → 配对入库 → 线性回归（≥30 样本）→ 预估收敛 |

**明确不做**：承诺与知网一致、AI 降重改写、论文代写代售、第三方 API 灰色渠道。

## 技术栈

- 后端：FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 + RQ/Redis（SQLite 可本地跑）
- 引擎：自研字符级 n-gram 包含度（2-6 字多窗口）+ SimHash 召回 + 校准模型（规则→线性回归→LightGBM），纯 Python 双端共用
- Web：React 18 + Vite + TypeScript + Ant Design 5 + Lucide
- 桌面：PyQt6（离线引擎，论文不出本机）
- 部署：Docker Compose（backend+worker+pg16+redis7）

## 目录结构

```
docs/plagiarism-precheck/   # 全部项目文档（大纲/PRD/架构/UIUX/Spec/QA）
src/engine/                 # 自研查重引擎（纯 Python，双端共用）
src/backend/                # FastAPI 服务（14 端点）
src/web/                    # React 前端（5 页）
src/desktop/                # PyQt6 桌面端（同构 5 页）
src/deploy/                 # Docker Compose + nginx + 构建脚本
```

## 本地快速启动（后端，SQLite 免装 PG/Redis）

```bash
cd src/backend
pip install -r requirements.txt
PYTHONPATH=.. PRE_DATABASE_URL="sqlite+aiosqlite:///./dev.db" \
  PRE_RQ_SYNC=1 PRE_AUTO_CREATE_TABLES=1 PRE_JWT_SECRET="dev-secret" \
  python -m uvicorn app.main:app --port 8000
```

## 前端启动

```bash
cd src/web
npm install
VITE_USE_MOCK=true npm run dev    # mock 模式（无需后端）
VITE_USE_MOCK=false npm run dev   # 真实 API（/api 代理到 localhost:8000）
```

## 生产部署

```bash
cd src/deploy
docker compose up -d --build
```

## 测试

```bash
# 单元测试（engine 36 + backend 23 + desktop 7 = 66）
cd src && PYTHONPATH=. pytest engine/tests backend/tests desktop/tests

# 集成测试（需后端启动在 8000 端口）
cd src/web && python integration_test.py   # 24/24
```

## 文档

- PRD：`docs/plagiarism-precheck/PRD-预查重项目-v1.0.md`
- 规格契约：`docs/plagiarism-precheck/Spec-预查重项目-v1.0.md`
- QA 报告：`docs/plagiarism-precheck/QA-预查重项目-v1.0.md`

## License

见 LICENSE（MIT）。
