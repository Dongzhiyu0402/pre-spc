# 预查重项目 可执行目录结构 v1.0

> 生成日期：2026-08-05
> 依据：Spec-预查重项目-v1.0.md §4（技术架构锁定）+ 代码组织规范（分层·依赖只向下·单文件≤300行·按资源分包）
> 适用范围：Phase 3 开发唯一目录依据。仓库根：`pre-spc/`（GitHub: Dongzhiyu0402/pre-spc）

---

## 1. 总览

```
pre-spc/
├── backend/       # FastAPI 服务端（Web API + RQ worker + 校准训练）
├── engine/        # 查重引擎（纯 Python，无框架依赖，Web/桌面双端共用）
├── desktop/       # PyQt6 桌面端（本地引擎调用 + 在线 API 客户端）
├── web/           # React 18 + Vite + TS 前端
├── deploy/        # Docker Compose / Nginx / 环境变量
├── docs/          # 规格文档（Spec/openapi/schema 等，与仓库 docs 同步）
└── README.md
```

**分层依赖铁律（强制）**：
- 依赖只向下，禁止反向 import。
- `backend/app/api` → `services` → `repositories` → `models`（数据层）。
- `backend` 与 `desktop` 通过 `engine` 的纯函数接口调用引擎；`desktop` 另经 HTTP 调 `backend` API。
- `engine` 不依赖任何 Web 框架、不 import HTTP 对象、不碰数据库（语料库构建工具除外，见 §3）。

---

## 2. backend/（FastAPI 服务端）

```
backend/
├── app/
│   ├── main.py                # 入口：只装配（创建 app、挂中间件、include_router、启动），<100 行
│   ├── config.py              # pydantic-settings 配置（env 驱动：DB/Redis/JWT/额度）
│   ├── api/                   # 表现层：路由端点，只做参数校验 + 调 service + 组装响应
│   │   ├── deps.py            # 依赖注入（get_db、get_current_user、get_current_refresh_token）
│   │   ├── auth.py            # POST /auth/register、/auth/login、/auth/refresh、GET /auth/me
│   │   ├── plans.py           # GET /plans
│   │   ├── checks.py          # POST/GET /checks、GET /checks/{id}(/report)(/export)、POST /recheck
│   │   ├── calibration.py     # POST /calibration/reports、GET /calibration/status
│   │   └── usage.py           # GET /users/me/usage
│   ├── services/              # 业务层：业务规则、事务编排、跨模块协作；不 import HTTP 对象
│   │   ├── auth_service.py    # 注册/登录/刷新/当前用户（含注册送次数 -> AC-12）
│   │   ├── check_service.py   # 创建任务/扣额度/状态查询/再检测（AC-01/03/04/13）
│   │   ├── report_service.py  # 组装完整报告（区间/片段/来源/免责声明）
│   │   ├── calibration_service.py  # 回传样本解析配对/模型训练触发（AC-14/15）
│   │   ├── quota_service.py   # 额度/积分扣减与流水（原子事务）
│   │   └── plan_service.py    # 方案列表（DB 配置驱动 -> AC-11）
│   ├── repositories/          # 数据层：SQLAlchemy 查询封装，不含业务逻辑
│   │   ├── user_repo.py
│   │   ├── check_task_repo.py
│   │   ├── check_result_repo.py
│   │   ├── plan_repo.py
│   │   ├── calibration_repo.py
│   │   └── point_repo.py
│   ├── models/                # SQLAlchemy ORM 模型（与 api/schema.sql 对齐）
│   │   ├── user.py
│   │   ├── check_task.py
│   │   ├── check_result.py
│   │   ├── check_segment.py
│   │   ├── plan.py
│   │   ├── calibration_sample.py
│   │   ├── calibration_model.py
│   │   └── point_transaction.py
│   ├── schemas/               # Pydantic 请求/响应模型（与 api/openapi.yaml 对齐）
│   │   ├── auth.py
│   │   ├── check.py
│   │   ├── report.py
│   │   ├── calibration.py
│   │   ├── plan.py
│   │   └── usage.py
│   ├── core/                  # 横切关注点
│   │   ├── security.py        # JWT 签发/校验（access 15min + refresh 7d）、密码哈希
│   │   ├── exceptions.py      # 统一错误码/异常 -> 响应信封 {code,data,message}
│   │   ├── rate_limit.py      # 防滥用限流（AC-13 防爬）
│   │   └── logging.py
│   └── worker/                # RQ 任务（查重是耗时任务，必须异步 -> AC-01）
│       ├── tasks.py           # run_check_job（调 engine 流水线）、train_calibration_job
│       └── worker.py          # RQ worker 入口
├── alembic/                   # 数据库迁移（versions/ 存放迁移脚本）
│   └── env.py
├── tests/                     # pytest（单元 + 集成；路由 -> service mock）
│   ├── conftest.py
│   ├── test_auth_api.py
│   ├── test_check_api.py
│   ├── test_calibration_api.py
│   └── test_services/
├── Dockerfile
├── pyproject.toml
└── requirements.txt           # 版本锚定（FastAPI>=0.115, pydantic>=2, SQLAlchemy 2.0, RQ 2.x）
```

**backend 要点**：
- 入口 `main.py` 只装配，不写业务（硬规则 #4）。
- 每个资源 = api + service + repository 三件套（硬规则 #3）。
- 单文件 ≤ 300 行，超限按子功能拆分（硬规则 #2）。
- `services` 之间跨模块协作走对方 service 接口，不直连 repository（铁律）。

---

## 3. engine/（查重引擎，双端共用，核心资产）

```
engine/
├── __init__.py                # 暴露统一入口：run_check(text, plan_params) -> EngineResult
├── cleaning/                  # 文本清洗（参考 paper_checking_system 思路）
│   ├── text_cleaner.py        # 去页眉页脚/目录/参考文献/非中文字符/空白归一
│   ├── section_splitter.py    # 章节分段（摘要/引言/正文/结论/致谢）
│   └── doc_extractor.py       # docx/txt/md/pdf -> 纯文本 + 结构（python-docx/PyMuPDF）
├── fingerprint/               # 指纹计算（多算法，各算法独立文件）
│   ├── ngram.py               # 字符级 n-gram 指纹（2-6 字多窗口，主判据）
│   ├── simhash.py             # SimHash 64 位指纹（候选召回）
│   ├── minhash.py             # MinHash 签名（语料库建库/去重，datasketch）
│   └── tfidf.py               # TF-IDF 向量（校准特征，scikit-learn）
├── recall/                    # 候选召回
│   └── simhash_index.py       # SimHash 倒排/分段索引 + 汉明距离召回候选文档
├── scoring/                   # 精算（主判据流水线）
│   ├── containment.py         # 候选集内 n-gram 包含度精算（contamination 分数）
│   ├── longest_match.py       # 最长连续命中片段统计（对齐知网"13 字"信号）
│   └── segment_agg.py         # 命中片段聚合 -> segments + sources + raw_score
├── calibration/               # 校准层（engine 内，模型文件落盘）
│   ├── features.py            # 特征工程（raw_score/最长片段/命中统计/文档结构/平台 one-hot）
│   ├── rules.py               # 冷启动规则+常数偏移（样本<50）
│   ├── linear.py              # 线性回归校准（50<=样本<200，scikit-learn）
│   ├── gbdt.py                # LightGBM 校准（样本>=200）
│   ├── model_store.py         # 模型文件读写（按 platform+paper_type 分桶）
│   └── predict.py             # 统一推理入口：-> (est_median, est_low, est_high, confidence)
├── corpus/                    # 语料库构建（仅内部基准，不对外宣称学术比对库）
│   ├── build.py               # 种子语料构建流水线（THUCNews/维基 -> 清洗 -> 指纹 -> 入库）
│   ├── opencc_norm.py         # 简繁归一（OpenCC）
│   └── ingest_user_docs.py    # 用户脱敏文档入库（授权后）
├── models/                    # 模型产物目录（gitignore，运行时生成）
│   ├── corpus_index/          # SimHash/MinHash 索引快照
│   └── calibration/           # 各桶校准模型 (.joblib/.txt)
└── tests/
    ├── test_ngram.py
    ├── test_containment.py
    ├── test_cleaning.py
    └── test_calibration_math.py
```

**engine 要点**：
- 引擎层**不 import 任何 Web 框架 / HTTP 对象**，保证桌面端离线可用（AC-16）。
- 统一入口 `run_check(text, plan_params)`，输入纯文本+方案参数，输出结构化 `EngineResult`（raw_score + segments + sources + features），与 Web/桌面解耦。
- 语料库索引落 `models/corpus_index/`，校准模型落 `models/calibration/`，运行时从磁盘加载。
- 桌面端直接调用本引擎（本地离线计算，原文不出本机，仅传指纹/特征用于在线校准同步）。

---

## 4. desktop/（PyQt6 桌面端）

```
desktop/
├── app/
│   ├── main.py                # 入口：只装配（QApplication + 主窗口 + 路由），<100 行
│   ├── config.py              # 本地配置（Token 消费、服务端地址、离线/在线模式）
│   ├── ui/                    # 页面（与 Web 同构，QSS 消费同一 design-tokens.json）
│   │   ├── upload_page.py     # 上传页（拖拽上传、方案卡片）
│   │   ├── report_page.py     # 报告页（预估区间量规、片段高亮、来源）
│   │   ├── login_page.py      # 登录/注册
│   │   ├── history_page.py    # 历史记录
│   │   └── usage_page.py      # 用量/回传入口
│   ├── widgets/               # 复用控件（GaugeWidget 量规、HighlightTextView 高亮文本）
│   │   ├── gauge_widget.py
│   │   └── highlight_text.py
│   ├── services/              # 桌面端服务（本地引擎 + 在线 API 客户端）
│   │   ├── local_check_service.py   # 本地离线查重（调 engine.run_check）
│   │   ├── api_client.py            # HTTP 客户端（登录/同步/回传，JWT）
│   │   └── sync_service.py          # 在线同步（指纹/特征上传、校准拉取）
│   ├── store/                 # 本地 SQLite 缓存（报告/用量/会话）
│   │   └── local_db.py
│   ├── resources/             # 静态资源
│   │   ├── icons/             # Lucide SVG（功能图标，与 Web 同源同套）
│   │   ├── qss/               # QSS 样式（内嵌 Token 值，来自 design-tokens.json）
│   │   └── design-tokens.json # 与 web 共用同一份 Token 源
│   └── theme.py               # Token -> QSS 变量映射（单一数据源消费端）
├── build/                     # PyInstaller 配置
│   ├── pre-spc.spec           # onedir 模式（规避杀软误报）+ 图标/资源打包
│   └── build.bat              # 构建脚本
├── tests/
└── pyproject.toml
```

**desktop 要点**：
- 默认离线计算：本地调 `engine.run_check`，原文不出本机（AC-16 桌面端条款）。
- 在线功能仅：登录/同步指纹特征/回传校准报告（HTTP 调 backend，JWT）。
- 图标：`resources/icons/` 存放 Lucide SVG，`QSvgRenderer` 渲染，与 Web 同一套（P0 锁定）。
- QSS 不硬编码颜色，全部从 `design-tokens.json` 生成（P0：禁止硬编码颜色）。

---

## 5. web/（React 前端）

```
web/
├── src/
│   ├── main.tsx               # 入口：只装配（Router + ConfigProvider + ThemeProvider）
│   ├── App.tsx                # 路由表（/ /report/:id /login /register /history /usage）
│   ├── api/                   # API 客户端（由 openapi.yaml 生成 TS 类型，唯一请求出口）
│   │   ├── client.ts          # fetch 封装（baseURL、JWT 注入、错误信封解析）
│   │   ├── auth.ts
│   │   ├── checks.ts
│   │   ├── calibration.ts
│   │   ├── plans.ts
│   │   └── usage.ts
│   ├── pages/                 # 页面组件（只组装，逻辑进 hooks/components）
│   │   ├── UploadPage.tsx     # 首页/上传（拖拽上传、方案卡片、历史列表）
│   │   ├── ReportPage.tsx     # 报告页（量规/阈值线/高亮视图/来源抽屉/导出）
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── HistoryPage.tsx
│   │   └── UsagePage.tsx
│   ├── components/            # 复用组件
│   │   ├── Gauge.tsx          # 误差带量规（中值刻度+区间色带+阈值线，AC-06/07）
│   │   ├── HighlightText.tsx  # 全文高亮视图（high/mid/cite 语义色）
│   │   ├── SourceDrawer.tsx
│   │   ├── UploadDropzone.tsx
│   │   └── Disclaimer.tsx     # 免责声明常驻（AC-09）
│   ├── hooks/                 # 业务 hooks（useCheckPolling、useAuth）
│   ├── theme/                 # 设计 Token 消费（AntD ConfigProvider + CSS 变量）
│   │   ├── antd-theme.ts      # theme.token 映射（colorPrimary #0D9488 等，来自 design-tokens.json）
│   │   └── tokens.css         # 从 design-tokens.css 引入的非 AntD 部分
│   ├── assets/                # Lucide 图标（lucide-react 按需引入）
│   ├── types/                 # openapi 生成的 TS 类型
│   └── utils/
├── package.json
├── vite.config.ts
├── tsconfig.json
└── index.html
```

**web 要点**：
- API 调用统一封装在 `src/api/`，页面不直接写 fetch（前端分层对应后端）。
- TS 类型由 openapi.yaml 生成（`types/`），前后端以 openapi.yaml 为唯一契约。
- AntD 仅 Web 使用；功能图标全 Lucide（lucide-react），AntD 组件内部控件图标保留默认（P0 边界，见 Spec §8 备注）。
- 所有页面渲染 `Disclaimer`（"预估仅供参考，非官方检测报告"，AC-09/边界约束）。

---

## 6. deploy/

```
deploy/
├── docker-compose.yml         # backend + worker + postgres + redis + nginx 编排
├── nginx.conf                 # 反代 /api -> backend，静态资源 -> web build
├── .env.example               # 环境变量模板（DB/JWT_SECRET/Redis/额度配置）
├── Dockerfile.backend
├── Dockerfile.worker
└── scripts/
    ├── init_db.sh             # 首次建库执行 schema.sql + alembic upgrade
    └── build_corpus.sh        # M2 种子语料构建命令封装
```

**部署要点**：
- 单台轻量云 2C4G，Docker Compose 一键编排（Spec §4）。
- worker 独立容器跑 RQ，与 API 容器隔离，可独立扩容。
- 文档原件加密存本地卷 + 30 天定时清理（对齐知网做法）。

---

## 7. 文件组织硬规则自检（Phase 3 门禁）

- [ ] 入口文件（backend/app/main.py、desktop/app/main.py、web/src/main.tsx）只装配，<100 行
- [ ] 所有源文件单文件 ≤ 300 行（门禁命令见下）
- [ ] 依赖只向下：api→services→repositories→models；无反向/跨层 import
- [ ] service 不 import HTTP 对象，不返回 HTTP 响应
- [ ] repository 不含业务逻辑
- [ ] engine 不依赖 Web 框架（保证桌面端离线可用）
- [ ] 图标：功能图标统一 Lucide；无 emoji 图标；无硬编码颜色（QSS/CSS 走 Token）
- [ ] 类型/Schema 独立成文件（backend/schemas、web/types）

**门禁命令**：
```bash
# 超 300 行检查（不合格即退回）
find backend desktop engine -name '*.py' | xargs wc -l | sort -rn | awk '$1>300 {print "OVER LIMIT:", $0}'
find web/src -name '*.ts' -o -name '*.tsx' | xargs wc -l | sort -rn | awk '$1>300 {print "OVER LIMIT:", $0}'
# emoji 图标扫描（功能图标不得出现 emoji 字符）
grep -rE "[\x{1F300}-\x{1FAFF}\x{2600}-\x{27BF}]" --include='*.py' --include='*.tsx' --include='*.ts' --include='*.qss' backend desktop web 2>/dev/null
```
