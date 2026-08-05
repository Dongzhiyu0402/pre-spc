# Spec - 预查重项目 v1.0

> 生成日期：2026-08-05
> 基于：PRD v1.0 + 架构文档 v0.1 + UIUX 文档 v1.0（用户已确认）
> 状态：已确认
> 代码仓库：https://github.com/Dongzhiyu0402/pre-spc（GitHub，Phase 3 接入）

---

## 1. 产品定义

- **一句话描述**：大学生在正式送检知网/维普/万方之前，用本工具低成本预估查重率（输出预估区间+置信度），通过用户回传真实查重报告持续校准，逐步逼近目标平台真实结果。
- **目标用户**：本科大四毕业生（P0，21-24 岁，论文 0.8-2 万字）；硕博研究生（P1 扩展）。
- **核心问题**：反复送检花钱多（知网黑市 198 元/篇、硕博 580 元/篇）、平台间结果矛盾、论文泄露风险。
- **产品定位**：送检前的"相对风险提示 + 趋势预测"，**不承诺与知网完全一致**。

## 2. MVP 范围（锁定——不在此列表的功能一律不做）

| 优先级 | 功能 | 验收标准摘要 | RICE 评分 |
|--------|------|-------------|-----------|
| P0 | 文档上传查重（docx/txt/md/pdf，1 万字 30 秒内出结果） | AC-01~04 | 6.0 |
| P0 | 查重报告（预估中值+区间+置信度、相似片段高亮、来源提示、导出 PDF/HTML） | AC-05~09 | 7.5 |
| P0 | 多平台方案切换（知网/维普/万方模拟 + API 适配层预留） | AC-10~11 | 5.4 |
| P0 | 账号与用量管理（注册/登录/免费次数/积分，防滥用） | AC-12~13 | 5.0 |
| P0 | 校准训练系统（回传真实报告→配对→线性回归→预估区间，随样本迭代） | AC-14~15 | 2.8（战略核心，必须闭环） |

## 3. 明确不做（Out-of-Scope — 锁定）

| 不做的功能 | 原因 | 何时考虑 |
|------------|------|----------|
| 承诺与知网结果完全一致 | 知网学术库不可获取，技术上不现实 + 法律风险 | 永不承诺，以预估区间呈现 |
| 第三方查重 API 真实直连 | 知网/维普/PaperPass 均无公开开发者 API；灰色渠道法律风险 | P1 评估万方 API / to B 商务 API |
| AI 降重/改写 | 学术伦理风险 + 改写质量不可控 | 不做 |
| 论文代写/代改/代售 | 学术不端 | 不做 |
| 批量查重/格式检测/历史对比 | MVP ROI 不足 | P1 |
| 英文论文检测 | Turnitin 生态不同 | 有明确需求后 |

## 4. 技术架构（锁定 — 版本锚定，以架构师 Phase 2 确认已安装版本为准）

| 层 | 技术 | 版本方向 | 锁定原因 |
|----|------|----------|----------|
| 后端 | FastAPI + Pydantic 2.x + SQLAlchemy 2.0 + asyncpg | Python 3.10+ | ASGI 异步、自动 OpenAPI、与引擎同栈 Python |
| 数据库 | PostgreSQL 16（服务端）；SQLite（桌面端离线缓存） | 16.x | 轻量试点足够，支持 JSONB 存报告 |
| 任务队列 | RQ 2.x + Redis 7 | 2.x / 7.x | 几百人试点足够，Celery 过度设计，未来可平滑迁移 |
| 桌面端 | PyQt6 + PyInstaller 6.x（onedir） | 6.8+ / 6.x | 用户熟悉 Python 栈；onedir+杀软白名单规避误报 |
| Web 前端 | React 18 + Vite + TypeScript + Ant Design 5 | 18.x / 5.x | 组件体系成熟，Token 可覆盖为 Teal |
| 图标库 | Lucide（锁定一套，双端同源） | - | Web 用 lucide-react，桌面用 Lucide SVG+QSvgRenderer |
| 查重引擎 | 自研：字符级 n-gram 包含度（2-6 字多窗口）+ SimHash 召回 + MinHash/LSH 建库 | - | 与知网"13 字连续匹配"同源，免分词误差，支持片段高亮 |
| 语料库 | THUCNews + 中文维基 dump（OpenCC 归一）+ 用户脱敏增量 | - | 开源可得；仅内部基准，不得对外宣称"学术比对库" |
| 校准模型 | 冷启动规则偏移 → 线性回归（50-200 样本）→ LightGBM（≥200） | - | 按（平台,论文类型）分桶，MAE 目标收敛 5% 以内 |
| 认证 | JWT（access 15min + refresh 7d） | - | 标准方案 |
| 部署 | 轻量云 2C4G + Docker Compose + 域名 SSL | - | 自费轻量预算 |

## 5. API 端点清单（锁定——开发时以此为唯一依据）

> 架构师 Phase 2 产出 `openapi.yaml`（OpenAPI 3.0），前端据此生成 TS 类型，后端据此实现。

| Method | Path | 功能 | 认证 | 请求体 | 响应体 |
|--------|------|------|------|--------|--------|
| POST | /api/v1/auth/register | 注册（送免费次数） | 否 | {email, password, nickname} | {user, tokens} |
| POST | /api/v1/auth/login | 登录 | 否 | {email, password} | {user, tokens} |
| POST | /api/v1/auth/refresh | 刷新 token | refresh | - | {tokens} |
| GET | /api/v1/auth/me | 当前用户信息 | access | - | {user} |
| GET | /api/v1/plans | 可用查重方案列表 | access | - | [{code, name, type, price_info}] |
| POST | /api/v1/checks | 创建查重任务（上传文档） | access | multipart: file, plan_code | {task_id, status} |
| GET | /api/v1/checks/{id} | 任务状态/结果摘要 | access | - | {task_id, status, progress, result?} |
| GET | /api/v1/checks/{id}/report | 完整报告（区间/片段/来源） | access | - | {report} |
| GET | /api/v1/checks/{id}/export | 导出报告 | access | ?format=pdf\|html | 文件流 |
| GET | /api/v1/checks | 历史查重列表 | access | ?page=&limit= | {items, total} |
| POST | /api/v1/checks/{id}/recheck | 再次检测（同一文档） | access | {plan_code} | {task_id} |
| POST | /api/v1/calibration/reports | 回传真实查重报告 | access | multipart: file, platform, real_rate, task_id | {sample_id, status} |
| GET | /api/v1/calibration/status | 校准样本数/模型状态 | access | - | {sample_count, model_version, mae} |
| GET | /api/v1/users/me/usage | 免费次数/积分余额 | access | - | {free_quota, points} |

## 6. 数据库表清单（锁定）

| 表名 | 核心字段 | 索引 | 关联 |
|------|----------|------|------|
| users | id, email, password_hash, nickname, role, free_quota, points, created_at | uk_email | - |
| check_tasks | id, user_id, file_name, file_size, word_count, plan_code, status, engine_version, created_at | idx_user, idx_status | users.id |
| check_results | id, task_id, raw_score, est_median, est_low, est_high, confidence, segments_json, created_at | idx_task | check_tasks.id |
| check_segments | id, result_id, start_offset, end_offset, highlight_type, matched_source, similarity | idx_result | check_results.id |
| plans | id, code, name, type(engine/api), params_json, enabled | uk_code | - |
| calibration_samples | id, user_id, task_id, platform, real_rate, report_file, validated, created_at | idx_platform | users.id, check_tasks.id |
| calibration_models | id, platform, paper_type, sample_count, model_version, mae, params_json, trained_at | uk_platform_type | - |
| point_transactions | id, user_id, amount, type, reason, created_at | idx_user | users.id |

## 7. 页面清单（锁定）

| 页面 | 路由（Web） | 核心组件 | 对应 API | 设计 Token 主题 |
|------|-------------|----------|----------|-----------------|
| 首页/上传页 | / | 导航、拖拽上传区（虚线框 hover 高亮）、方案卡片选择、真实报告卡 mockup、历史列表 | POST /checks, GET /plans, GET /checks | Teal 主色 |
| 报告页 | /report/:id | 预估结果卡（误差带量规+置信度徽标）、章节重复率条、全文高亮视图、来源抽屉、导出按钮 | GET /checks/{id}/report, /export | Teal + 语义色 |
| 登录/注册 | /login /register | 极简居中卡片，错误就近显示 | POST /auth/* | 中性 |
| 历史记录 | /history | 最近检测列表、再次检测、空态引导 | GET /checks | 中性 |
| 用量/我的 | /usage | 免费次数卡、积分、校准报告回传入口 | GET /users/me/usage, POST /calibration/reports | 中性 + Teal 强调 |

桌面端同构页面（PyQt6 原生控件，QSS 消费同一 Token）。

## 8. 设计 Token（锁定）

> 设计师 Phase 2 产出 `design-tokens.json` + `design-tokens.css`，Web/桌面共用同一份。

- **主色**：Teal #0D9488（hover #0F766E / active #115E59 / soft #F0FDFA）
- **中性色**：bg #F7F8FA / surface #FFFFFF / fg #1F2937 / fg-2 #4B5563 / muted #6B7280 / border #E5E7EB
- **语义色**（内容标记组，独立于界面强调色）：高重复红 #DC2626（底 rgba(220,38,38,0.13)）/ 中重复橙 #EA580C（0.12）/ 引用赭黄 #B45309（0.16）/ 成功 #16A34A / 信息 #2563EB
- **字体**：Inter + Noto Sans SC（正文）；JetBrains Mono（报告数字，tabular-nums）
- **图标库**：Lucide（锁定一套，16/20/24px；功能图标全 Lucide，AntD 组件内部控件图标保留默认）
- **主题**：浅色
- **对标品牌**：Linear + Grammarly + Notion（工具型，非营销站）
- **圆角/间距**：--radius 8/12/16/pill；4px 网格（4/8/12/16/20/24/32/40/48/64/80）

## 9. 验收标准（锁定——QA 测试时以此为唯一依据，EARS 格式）

| 编号 | 功能 | EARS 格式验收标准 | 优先级 |
|------|------|-------------------|--------|
| AC-01 | 上传查重 | While 用户已登录且剩余免费次数>0，When 上传 ≤10 万字 docx 并提交，系统**必须**在 30 秒内返回查重结果（Web 异步） | P0 |
| AC-02 | 格式支持 | When 上传 txt/md/pdf，系统**必须**正常解析并出结果 | P0 |
| AC-03 | 超限拦截 | If 文件超过 10 万字或是空文件，系统**必须**返回明确错误且**不消耗**免费次数 | P0 |
| AC-04 | 次数归零 | If 剩余免费次数为 0，When 点击查重，系统**必须**跳转充值/积分页 | P0 |
| AC-05 | 报告完整性 | When 打开报告页，系统**必须**展示预估中值、预估区间、置信度、相似片段高亮、来源提示 | P0 |
| AC-06 | 区间可视化 | If 报告页展示预估区间，系统**必须**以误差带量规可视化呈现（中值刻度点+区间色带），而非仅单一数字 | P0 |
| AC-07 | 阈值线 | If 用户配置学校阈值且预估区间跨过阈值线，系统**必须**绘制阈值线并展示"建议优先修改高亮片段"行动指引 | P0 |
| AC-08 | 样本不足 | If 校准样本不足，系统**必须**展示宽区间提示（"校准样本积累中，结果仅供参考"），**不得**展示虚假精确数字 | P0 |
| AC-09 | 导出 | When 用户导出 PDF/HTML，系统**必须**生成完整报告且免责声明（"预估仅供参考，非官方检测报告"）常驻 | P0 |
| AC-10 | 方案切换 | When 用户选择"知网模拟"方案，系统**必须**按知网模拟参数计算并展示知网预估区间 | P0 |
| AC-11 | 方案可配置 | If 系统新增 API 平台配置，用户**必须**无需发版即可在方案列表看到并可用 | P0 |
| AC-12 | 注册赠送 | When 用户注册完成，系统**必须**赠送免费次数 | P0 |
| AC-13 | 积分扣除 | When 用户查重，系统**必须**优先扣除积分且余额实时可见 | P0 |
| AC-14 | 校准回传 | When 用户上传真实查重报告且格式有效，系统**必须**提取真实查重率并与该文档历史预查重结果配对入库 | P0 |
| AC-15 | 模型训练 | If 校准样本 ≥30 条，系统**必须**触发模型训练并生成新预估区间参数，下次查重使用新参数 | P0 |
| AC-16 | 隐私 | 桌面端**必须**默认离线计算（原文不出本机，仅传指纹）；Web 端文档脱敏授权后入库 | P0 |

## 10. 边界与约束

- 支持 Chrome/Safari/Firefox 最新 2 版；桌面端 Win10/11
- 性能：首屏 <3s；查重 API p95 <500ms（不含引擎）；1 万字 30 秒内出结果
- 并发：峰值 100 并发，任务队列削峰
- 单文件 ≤50MB / ≤10 万字
- 开源语料（THUCNews/维基）仅内部基准，不得对外宣称"学术比对库"
- 所有页面标注"预估仅供参考，非官方检测报告"
- 无障碍 WCAG 2.1 AA 基本合规（P2）

## 11. 内嵌已知坑（从项目记忆拉取 + 调研识别）

| 坑 | 技术栈指纹 | 根因 | 修法 |
|----|------------|------|------|
| PyInstaller 杀软误报 | pyinstaller | 未签名 exe 被误判 | onedir 模式 + 提交杀软白名单，发布期评估 Nuitka |
| 知网级语料库不可获取 | 语料库 | 学术库闭源 | 校准只能缩小差距，UI 呈现预估区间；开源语料仅内部基准 |
| 平台间结果矛盾 | 校准 | 各平台算法/库不同 | 按（平台,论文类型）分桶建模，不混训 |
| 校准样本冷启动慢 | 校准 | 样本稀疏 | 规则+常数偏移兜底；"回传报告换免费次数"激励 |
| 爬虫/滥用引擎 | 用量 | 免费额度被刷 | 账号体系 + 免费次数限制 + 速率限制 |

## 12. 端到端验证步骤（Spec 锁定最后一项）

```bash
# 1. 构建
docker compose up -d --build  # 服务端

# 2. 核心成功流（注册→登录→上传→查重→报告）
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@123","nickname":"tester"}'
# 断言：201 + user + tokens

curl -X POST http://localhost:8000/api/v1/checks \
  -H "Authorization: Bearer {access_token}" \
  -F "file=@sample.docx" -F "plan_code=cnki_sim"
# 断言：202 + task_id + status=pending

curl http://localhost:8000/api/v1/checks/{task_id}/report \
  -H "Authorization: Bearer {access_token}"
# 断言：200 + est_median/est_low/est_high/confidence/segments 完整

# 3. 关键错误流
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@123","nickname":"tester"}'
# 断言：409 + 邮箱已存在
```

## 13. 变更记录

| 日期 | 变更内容 | 原因 | 影响范围 |
|------|----------|------|----------|
| 2026-08-05 | v1.0 创建 | 基于用户确认的三文档生成规格契约 | 全部 |
