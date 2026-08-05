# 预查重项目 MVP v1.0 — 交付总览

> 2026-08-05 完成全流程（Phase 0 → Phase 4）：需求澄清 → 三文档调研 → Spec 契约 → 设计细化 → 并行开发 → QA 验证 → GitHub 上线

## 交付了什么

**代码（已推送 https://github.com/Dongzhiyu0402/pre-spc）**

| 模块 | 技术 | 内容 |
|------|------|------|
| src/engine | Python 纯引擎 | 清洗/分段/字符级 n-gram(2-6字)/SimHash 召回/片段聚合/校准预测（规则→线性回归）；基准 MAE 7.24、Spearman 0.956 |
| src/backend | FastAPI | 14 端点（auth/plans/checks/calibration/usage），JWT+bcrypt+限流，RQ 异步查重 |
| src/web | React18+AntD5+Lucide | 5 页：上传/报告（误差带量规 SVG）/登录注册/历史/用量，tsc 0 error |
| src/desktop | PyQt6 | 同构 5 页，离线引擎直跑（论文不出本机）+ 联网同步，offscreen 测试 7/7 |
| src/deploy | Docker Compose | backend+worker+pg16+redis7+nginx |

**文档（docs/plagiarism-precheck/）**：项目大纲与里程碑 / PRD v1.0 / 技术调研与架构规划 v0.1 / UIUX v1.0 / Spec v1.0（AC-01~16）/ QA v1.0 / design/（Token+页面提示词+QSS）/ api/（openapi.yaml+schema.sql）

## 质量证据（全部真实运行）

- 单元测试：engine 36 + backend 23 + desktop 7 = **66 passed**
- 集成测试：**24/24 PASS**（注册→上传→三方案查重→报告 4 扩展字段→导出→校准回传→超限 402→历史）
- P0 规则扫描：emoji / 紫粉渐变 / AI 模板味 / 弹跳缓动 **0 命中**
- 引擎基准：MAE 7.24（≤15）/ Spearman 0.956（≥0.6）/ Recall 1.0（≥0.7）/ 1 万字 23ms
- 生产就绪度：**MVP 可试点**（P0 缺陷 0）

## 上线前待办（已知限制，非阻塞）

1. 原文落盘 storage/uploads/ 加密 + 30 天定时清理（隐私合规）
2. PDF 导出需在生产环境安装 reportlab
3. 校准样本 paper_type 字段扩展后才能真正分桶训练
4. exclude_self_rate 恒 null（无本人标记功能，P1 填充）
5. 浏览器 E2E 测试 + 监控告警（试点期后置）

## 下一步建议（M6 运营迭代）

- 服务器上 `docker compose up -d --build` 部署（阿里云轻量 2C4G 即可）
- 校内试点：发 20 个种子用户，验证"校准样本≥30 后预估收敛"假设
- 用"回传报告换免费次数"激励样本积累
- 试点数据跑通后决定是否扩展（批量查重/历史对比/万方 API 直连）
