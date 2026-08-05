# QA 测试报告 - 预查重项目 v1.0

> 测试日期：2026-08-05 23:40-23:50
> 执行：项目总监（团队通信通道不可用后直接执行验证，机械证据）
> 测试环境：隔离 venv（Python 3.13.12，pre-spc-qa）；后端 SQLite 模式（无需 Postgres/Redis）

---

## 1. P0 绝对规则最终全量扫描（正则）

| 规则 | 扫描范围 | 结果 |
|------|----------|------|
| emoji 作为功能图标 | src/ 下全部 .tsx/.ts/.html/.py/.qss/.jsx/.js（排除 node_modules/dist） | **0 命中** ✅ |
| 紫色→粉色渐变（#7C3AED/#A855F7/#EC4899/linear-gradient 135deg） | 同上 | **0 命中** ✅ |
| AI 模板味占位（lorem ipsum / welcome to our / sign up today） | 同上 | **0 命中** ✅ |
| 弹跳缓动 cubic-bezier(0.68,-0.55,0.265,1.55) | 同上 | **0 命中** ✅ |

## 2. 测试执行结果（真实运行）

| 套件 | 命令 | 结果 |
|------|------|------|
| engine 单元测试 | pytest engine/tests | **36 passed**（0.31s） |
| backend 单元测试 | pytest backend/tests | **23 passed**（6.62s） |
| desktop 单元测试 | pytest desktop/tests（QT_QPA_PLATFORM=offscreen） | **7 passed**（0.96s） |
| 全量单元 | 合计 | **66 passed** |
| 前后端集成 | src/web/integration_test.py（真实后端 127.0.0.1:8000） | **24/24 PASS** |
| 前端类型检查 | tsc --noEmit（严格模式） | **0 error** |
| 引擎基准 | src/engine/reports/benchmark_cnki.json | MAE 7.24（≤15✅）/ Spearman 0.956（≥0.6✅）/ Recall 1.0（≥0.7✅）/ p95 2ms |

## 3. 集成测试 24 项明细（全 PASS）

注册 201（赠 5 次）/ 重复注册 409 / 登录 200 / 未登录 401 / me / plans 4 方案 / 三方案（cnki/vip/wanfang）查重 succeeded / 报告核心字段（median=100, low=88, high=100, conf=35, segments）/ **报告 4 个 UI 扩展字段全部 present（full_text/metrics/chapters/source_detail）** / 导出 HTML 200 / 导出 PDF 500（reportlab 缺失，前端回退 HTML，符合设计）/ 再检测 202 / 校准回传 201 pending_validation / 用量递减 5→1 + 积分 0→2 / 超限 402 / 历史列表 200

## 4. AC 覆盖评估（Spec §9）

| 编号 | 验收点 | 覆盖 | 证据 |
|------|--------|------|------|
| AC-01 | 1 万字 30 秒出结果 | ✅ | 引擎 1 万字 23ms；集成链路 succeeded |
| AC-02 | txt/md/pdf 解析 | ✅ | 后端单测覆盖格式 |
| AC-03 | 超限/空文件不消耗次数 | ✅ | backend 单测 + 上传校验代码 |
| AC-04 | 次数 0 跳充值 | ✅ | 402 集成验证 + 前端跳转实现 |
| AC-05 | 报告完整性 | ✅ | 集成报告核心字段全 present |
| AC-06 | 区间可视化（量规非单一数字） | ✅ | Gauge.tsx 自绘 SVG（前端代码核查） |
| AC-07 | 阈值线+跨线指引 | ✅ | Gauge 组件 + useSchoolThreshold 联动 |
| AC-08 | 样本不足宽区间 | ✅ | Gauge 组件宽区间态 + 文案核查 |
| AC-09 | 导出+免责声明常驻 | ✅ | 导出 HTML 200 + disclaimer 字段在案 |
| AC-10 | 方案切换出对应预估 | ✅ | 三方案集成均 succeeded |
| AC-11 | 方案可配置无需发版 | ✅ | plans 表驱动 + 4 codes |
| AC-12 | 注册赠次数 | ✅ | 集成 free_quota=5 |
| AC-13 | 积分实时可见 | ✅ | 集成 quota 5→1 points 2 |
| AC-14 | 校准回传配对入库 | ✅ | 集成 201 pending_validation |
| AC-15 | 样本≥30 触发训练 | ✅ | backend 单测覆盖训练触发（engine/scoring/calibration.py 线性回归实现核查） |
| AC-16 | 桌面离线原文不出本机 | ✅ | desktop 离线引擎端到端单测 + 架构核查（原文不落盘仅结果） |

## 5. 契约一致性

- openapi.yaml Report/Segment 4 扩展字段 ↔ 前端 types/api.ts（optional）↔ 后端 schemas/report.py：**三端对齐** ✅

## 6. 已知限制（非阻塞，记录在案）

| 项 | 说明 | 处理 |
|----|------|------|
| exclude_self_rate 恒 null | MVP 无"本人已发表"标记功能，不造假 | 接入本人标记后填充（P1） |
| PDF 导出需 reportlab | 缺失时后端 500，前端自动回退 HTML | requirements 可选依赖，生产安装 |
| 原文落盘 storage/uploads/ | 查重时持久化用于 recheck 与 full_text | 生产待办：加密 + 30 天定时清理 |
| 校准样本 paper_type | schema 无字段，分桶默认 undergrad | P1 扩展字段后真正分桶 |
| calibration sample_count=0 | 集成测试回传后为 pending_validation 未验证计数 | 验证流程上线后由管理员确认 |
| Vite 重复 build 删除被沙箱拦 | 已用 emptyOutDir:false 规避 | CI/服务器环境正常 |

## 7. 生产就绪度评级（production-readiness 口径）

| 维度 | 评级 | 说明 |
|------|------|------|
| 功能完整性 | 高 | AC-01~16 全覆盖，双形态（Web+桌面）闭环 |
| 测试保障 | 中高 | 66 单测 + 24 集成 + tsc 0 error；缺浏览器 E2E（P1） |
| 安全 | 中 | JWT/bcrypt/限流/SQL 参数化/上传校验齐备；原文落盘加密待办 |
| 部署 | 中 | Docker Compose（backend+worker+pg16+redis7）就绪；未真实上云 |
| 可观测性 | 低 | 有埋点事件设计，日志/监控/告警未接入（试点期可后置） |
| 隐私合规 | 中高 | 脱敏授权 + 桌面端原文不出本机；Web 文档 30 天清理待落地 |

**总体评级：MVP 可试点（Ready for Pilot）** —— P0 缺陷 0，P0 规则全过，核心链路（注册→上传→查重→报告→校准回传）端到端真实跑通。上生产前需补齐：原文落盘加密清理、部署监控、reportlab。

## 8. RoleVerdict

verdict: pass
blocking: []
advisory: [原文落盘加密+30天清理、PDF reportlab 生产必装、浏览器 E2E 建议 P1、可观测性后置]
evidence: [engine 36+backend 23+desktop 7=66 passed, integration 24/24, tsc 0 error, benchmark MAE7.24, P0 扫描 0 命中]
