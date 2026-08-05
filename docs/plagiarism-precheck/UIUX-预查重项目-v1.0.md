# UIUX：低成本预查重工具 v1.0

> 版本：v1.0（Phase 1 设计调研输出）
> 作者：UI/UX 设计师 颜好看
> 日期：2026-08-05
> 状态：待项目总监确认后进入 M1.5 规格契约（Phase 2 产出完整 DESIGN.md 9 节 + design-tokens.json/css）
> 依据：PRD-预查重项目-v1.0.md + Phase1-技术调研与架构规划-v0.1.md + 竞品联网调研（PaperPass / 知网 / 维普 / 万方 / Grammarly / DeepL Write）
> 三轴刻度：DESIGN_VARIANCE=4 / MOTION_INTENSITY=3 / VISUAL_DENSITY=5

---

## 1. 设计语言结论

### 1.1 寄存器判断：Product 寄存器

本项目是**工具型产品**（上传 → 查重 → 报告 → 用量），校内试点、学生自用，设计标杆 = **赢得熟悉感**（Linear / Figma / Notion / Stripe 熟手用户坐下即信任，不在异常组件上停顿）。

- 首页是"工具工作台"而非营销 hero，但允许一段"产品价值"区，**展示真实报告卡而非抽象图形**
- 失败模式不是平淡，而是无目的的奇怪（装饰过度的按钮、不匹配的控件、无功能的动效）
- 每个交互组件全状态：default / hover / focus / active / disabled / loading / error / success
- 动效 150–250ms，传递状态而非装饰，无页面级开场编排

### 1.2 三轴刻度

| 参数 | 值 | 含义 |
|------|-----|------|
| DESIGN_VARIANCE | 4 | 可预测网格；报告页允许非对称（左原文右来源对照） |
| MOTION_INTENSITY | 3 | 功能动效为主（150–250ms），无装饰动画，尊重 prefers-reduced-motion |
| VISUAL_DENSITY | 5 | 主流程清爽；报告页信息密度适中（高但可扫描） |

### 1.3 对标品牌

| 对标 | 借鉴点 |
|------|--------|
| Linear | 排版精度、间距节奏、组件状态完整度（"工具感"） |
| Grammarly | 清爽可信的写作工具报告气质（"清爽 + 报告信息层级"） |
| Notion | 低干扰中性色基底（"留白与克制"） |

**明确不抄**：竞品全部走"陈旧营销风"——PaperPass（蓝红渐变营销站）、知网（PDF 报告单、红底营销页）、维普/万方（表单 + 订单号查询）。这正是差异化机会：用现代工具型设计做同一件事，但**必须保留行业已认知的颜色语义**（红=复制 / 黄=引用 / 灰=排除 / 黑=原创），降低用户学习成本。

### 1.4 竞品 UI 调研要点（已联网核实）

- **PaperPass**：登录（微信扫码/手机号）→ 首页醒目"论文查重"入口 → 上传（填标题/作者）→ 提交 → 约 5 分钟出报告；报告 = 顶部总重复率 + 章节重复率（"文献综述 35%"）+ 红标高重复/橙标中重复 + 点标红看相似来源与原文 + 降重建议 + 导出 Word 版报告
- **知网报告单**：6 种报告单（简洁/全文标明引文/去除本人/全文对照/跨语言/概览）；颜色语义 = 红=文字复制、黄=引用、灰=排除（独创声明/目录/参考文献）、黑=原创；相似文献列表含篇名/作者/出处/时间/复制比/是否引用；片段相似分析含位置/作者/来源标题/相似比（如 85%）；全文对照 = 左原文右来源
- **重复率等级行业共识**：≤10% 优秀 / 10-20% 良好 / 20-30% 合格 / 30-50% 不合格 / >50% 严重

---

## 2. 配色系统

### 2.1 策略

浅色冷调为主；品牌强调色**仅 1 个（Teal）**；报告页红/橙/黄高亮为**内容标记语义色**，独立成组，不属于界面强调色（每屏≤2 处强调色规则不适用于内容标记）。禁紫粉渐变、禁毛玻璃装饰、禁发光边框。

### 2.2 品牌强调色（每屏≤2 处：CTA / 选中态 / 关键数据高亮）

| Token | 值 | 用途 |
|-------|-----|------|
| --accent | #0D9488 | 主色（Teal） |
| --accent-hover | #0F766E | 悬停 |
| --accent-active | #115E59 | 激活/按下 |
| --accent-on | #FFFFFF | accent 背景上的前景 |
| --accent-soft | #F0FDFA | 浅底/选中底 |

选 Teal 理由：①与竞品全用蓝/红形成差异；②清爽年轻贴合 21-24 岁学生；③深 Teal 依然稳重可信；④与"标红=重复"的语义色不冲突（若选红/蓝主色会与重复色打架）。

### 2.3 中性色板（70-90% 表面）

| Token | 值 | 用途 |
|-------|-----|------|
| --bg | #F7F8FA | 页面背景（冷调浅灰，非米色） |
| --surface | #FFFFFF | 卡片/容器 |
| --surface-warm | #F1F2F4 | 三级表面/表头底 |
| --fg | #1F2937 | 主文本 |
| --fg-2 | #4B5563 | 次级文本 |
| --muted | #6B7280 | 副文本/说明 |
| --meta | #9CA3AF | 三级前景/元数据 |
| --border | #E5E7EB | 默认边框 |
| --border-soft | #F1F2F4 | 行分隔/内部线 |

### 2.4 语义色组

**状态语义色（AntD semantic 映射，组件状态用）**：

| Token | 值 | 用途 |
|-------|-----|------|
| --success | #16A34A | 成功/低重复等级 |
| --warn | #EA580C | 警告/中重复等级 |
| --danger | #DC2626 | 错误/高重复等级 |
| --info | #2563EB | 信息提示 |

**内容标记语义色（报告页高亮，独立成组 --highlight-*，不走 AntD semantic token）**：

| Token | 值 | 行业语义 | WCAG 说明 |
|-------|-----|----------|-----------|
| --highlight-high | rgba(220,38,38,0.13) | 高重复（红） | 仅作底色，正文恒为深色 #1F2937，保证 4.5:1 |
| --highlight-mid | rgba(234,88,12,0.12) | 中重复（橙） | 同上 |
| --highlight-cite | rgba(180,83,9,0.16) | 引用（赭黄加深保对比） | 同上 |
| --highlight-exclude | rgba(107,114,128,0.10) | 排除（灰） | 同上 |
| （无底色） | — | 原创（黑） | 正文默认 |

> 透明度基线来自 PM 行业参考（红 0.12-0.15 / 橙 0.12 / 黄 0.20），校准为与全 Token 语义色一致的品牌红/橙/赭黄值。

### 2.5 Design Token 草案（Phase 2 定稿为 design-tokens.json + design-tokens.css）

```css
:root {
  /* A1-identity */
  --bg:#F7F8FA; --surface:#FFFFFF; --fg:#1F2937; --fg-2:#4B5563; --muted:#6B7280; --meta:#9CA3AF;
  --border:#E5E7EB; --border-soft:#F1F2F4;
  --accent:#0D9488; --accent-hover:#0F766E; --accent-active:#115E59; --accent-on:#FFFFFF; --accent-soft:#F0FDFA;
  --font-display:"Inter","Noto Sans SC",sans-serif;
  --font-body:"Inter","Noto Sans SC",sans-serif;
  --font-mono:"JetBrains Mono","SFMono-Regular",Consolas,monospace;

  /* A2-semantic */
  --success:#16A34A; --warn:#EA580C; --danger:#DC2626; --info:#2563EB;

  /* B-slot 组件别名（Phase 2 展开） */
  --btn-primary-bg:var(--accent); --btn-primary-text:var(--accent-on);
  --input-border:var(--border); --input-focus-ring:0 0 0 3px rgba(13,148,136,0.35);

  /* C-extension 内容标记语义色 */
  --highlight-high:rgba(220,38,38,0.13); --highlight-mid:rgba(234,88,12,0.12);
  --highlight-cite:rgba(180,83,9,0.16); --highlight-exclude:rgba(107,114,128,0.10);

  /* 间距（4px 网格） */
  --space-1:4px; --space-2:8px; --space-3:12px; --space-4:16px; --space-5:20px;
  --space-6:24px; --space-8:32px; --space-10:40px; --space-12:48px; --space-16:64px;

  /* 圆角 */
  --radius-sm:8px; --radius-md:12px; --radius-lg:16px; --radius-pill:9999px;

  /* 层级与动效 */
  --elev-flat:none; --elev-ring:0 0 0 1px var(--border); --elev-raised:0 1px 2px rgba(0,0,0,0.04),0 4px 8px rgba(0,0,0,0.06);
  --focus-ring:0 0 0 3px rgba(13,148,136,0.35);
  --motion-fast:150ms; --motion-base:200ms; --ease-standard:cubic-bezier(0.2,0,0,1);

  /* 布局 */
  --container-max:1200px; --section-y-desktop:80px; --section-y-tablet:48px; --section-y-phone:32px;
}
```

---

## 3. 字体系统

| 角色 | 字体 | 说明 |
|------|------|------|
| 标题/正文 | Inter + Noto Sans SC | 中文场景强制 Noto Sans SC，避免中文回退系统字 |
| 数据/等宽 | JetBrains Mono | 报告页查重率数字、字数、相似比用等宽 + tabular-nums 对齐（"专业可信感"关键） |

- 字重三级：400 正文 / 510 次标题 / 590 大标题
- 字距：标题 -0.02em；小标签 ALL CAPS +0.06em；正文 0
- 字号阶梯（8 级）：12 / 14 / 16 / 18 / 20 / 24 / 32 / 40px
- Google Fonts 加载：
  `https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap`
- 性能注意：Noto Sans SC 文件大，须子集化或 CDN 分片

---

## 4. 图标系统

### 4.1 锁定：Lucide（架构师 Spec 锁定，本设计确认）

| 候选 | 结论 |
|------|------|
| **Lucide（锁定）** | 1000+ 图标，ISC≈MIT 可商用，统一 2px 线性描边，现代极简，tree-shakable，官方 React/Vue/Svelte 组件 + 纯 SVG 输出 |
| Tabler | 4000+，MIT，偏"专业后台感"、部分冗余 → 不采用 |
| Phosphor | 1248，6 字重，MIT，视觉偏活泼、选择成本高 → 不采用 |
| Heroicons | 仅 292，MIT，覆盖不足 → 不采用 |

选 Lucide 理由：①统一 2px 线性描边 = 最贴合"极简瑞士/工具型"语言；②Web 与 PyQt6 可共用同一套 SVG（桌面端 QSvgRenderer 渲染为 QIcon），实现**双形态图标统一**；③查重场景图标全覆盖（upload-cloud / file-text / check-circle-2 / alert-triangle / shield-check / settings / user / history / download / external-link / search / copy 等）；④按需引入性能好。

### 4.2 双端同源

- **Web**：`lucide-react`（tree-shaking 按需引入）
- **桌面 PyQt6**：打包 Lucide SVG 资源文件，用 QSvgWidget / QSvgRenderer 渲染为 QIcon
- 两端同一套图标文件，视觉零漂移

### 4.3 图标边界（P0 规则的务实判定，架构师已确认写入 Spec）

- **功能图标**（导航/操作/状态/上传/导出等用户可见）→ 全部 Lucide，不混用 @ant-design/icons；P0"锁定一套 SVG 图标库、全项目统一"以功能图标为判定对象
- **AntD 组件内部控件图标**（Table 排序箭头 / Select 展开箭头 / Modal 关闭 / Pagination 箭头等）→ 组件框架默认控件，非功能图标，允许保留 AntD 默认；Spec 显式标注"组件控件图标允许 AntD 默认（非功能图标，不参与 Lucide 统一判定）"，QA 扫描有据可依
- **尺寸规范**：16px（行内）/ 20px（按钮内）/ 24px（独立图标），全项目统一

### 4.4 禁 emoji

任何 emoji 不得作为功能图标（正则扫描 `[\x{1F300}-\x{1F9FF}\x{2600}-\x{26FF}\x{2700}-\x{27BF}]`）。emoji 仅允许出现在用户生成内容（UGC）中。

---

## 5. 页面设计方向

> 反千篇一律 Hero（P0-5）：所有页面展示真实产品内容，不用"大标题 + 副标题 + 居中 CTA + 抽象图形"。

### 5.1 首页 / 上传页（Web 主战场，桌面端同构）

- **布局**：顶部极简导航（Logo + 方案选择 + 历史 + 登录/用量）→ 非对称区：左侧标题/副标题/上传按钮，右侧【真实报告卡 mockup】（总重复率 + 误差带量规 + 章节条 + 标红片段，静态展示）
- **核心拖拽上传区**：2px dashed 边框，hover/拖入高亮为 Teal 边框 + 浅底；支持 docx/txt/md/pdf（≤10 万字 / 单文件 ≤50MB，1 万字 30 秒）；拖入后显示文件名/大小/字数/图标；校验失败就地报错（格式/大小/空文件），不消耗免费次数
- **上传确认区**：检测方案选择（知网模拟/维普模拟/万方模拟/第三方 API，卡片式单选）+ 开始检测按钮（Loading 态含进度条）
- **历史记录**：右侧栏或下方列表（最近检测 → 再次检测），空态给引导文案 + CTA
- 隐私说明：Web 端上传区附近放脱敏说明（"文档默认脱敏后入库，可 30 天删除"）

### 5.2 报告页（核心页面，差异化视觉中心）

顶部【预估结果卡】三层结构：

1. **第一层**：预估查重率【中值大数字，mono】+ 预估区间（如 "14% – 24%"）+ 置信度徽标（如 "置信度 82%"）
2. **第二层（核心可视化）**：【横向误差带量规】——中间刻度点 = 预估中值，半透明色带 = 预估区间；比单一环形更诚实（单一环形 = 虚假精确，违反 PRD 原则）；量规上画【学校阈值线】（用户可配置，默认 20%）
3. **第三层（行动指引）**：区间跨过阈值线时自动提示"你的预估区间跨过学校阈值，建议优先修改高亮片段"——把焦虑直接转化为行动指引

- **样本不足时**（对齐 PRD 验收 7.5）：色带自动变宽 + 提示"预估区间较宽，校准样本积累中，结果仅供参考"，绝不展示虚假精确数字
- **指标区**：三张指标小卡（去除引用率 / 去除本人率 / 单篇最大复制比）
- **章节重复率**：列表 + 细进度条（"文献综述 35%"）
- **相似片段高亮**：全文视图，沿用行业颜色语义——红=高重复 / 橙=中重复 / 黄=引用 / 灰=排除 / 黑=原创（用户已有认知，不可重造）
- **来源抽屉**：点片段 → 右侧抽屉/底部面板：相似来源列表（篇名/作者/出处/相似比/是否引用/年份）+ 左原文右来源对照
- **导出**：PDF / HTML
- **免责声明常驻**："预估仅供参考，非官方检测报告"
- **加载态**：报告生成中显示进度（解析 → 指纹 → 比对 → 校准），可取消；空态引导"上传论文"；错误态明确错误码 + 就地重试

### 5.3 登录 / 注册页

极简居中卡片；微信扫码 + 手机号/邮箱切换；错误就近显示；登录后跳首页；未登录访问报告 → 跳登录。

### 5.4 用量页 / 我的

剩余免费次数卡片、套餐/积分、历史报告列表（再次检测/导出）、**校准报告回传入口**（本项目差异点——鼓励回传真实报告，界面给明确引导）。

### 5.5 状态覆盖（全组件 5 态）

Loading（骨架屏/进度条）/ Empty（引导文案 + CTA）/ Error（错误码 + 重试，不消耗次数）/ Populated / Edge（超长文本截断、10 万字上限拦截）。

---

## 6. 双形态统一策略（Web + PyQt6）

- **Token 单一数据源**：`design-tokens.json`（Phase 2 产出，含版本号）为唯一源，两端共同契约
  - Web：AntD 5 `ConfigProvider theme.token` 覆盖为 Teal 系 + CSS 变量（design-tokens.css）供非 AntD 部分
  - 桌面 PyQt6：QSS 内嵌 Token 值（AntD 的 CSS-in-JS 不适用于桌面，AntD 只服务 Web）
- **AntD theme.token 映射草案**（Phase 2 定稿后同步 Spec）：
  - colorPrimary → #0D9488（覆盖 AntD 默认蓝 #1677ff）
  - colorInfo → #2563EB / colorSuccess → #16A34A / colorWarning → #EA580C / colorError → #DC2626
  - colorBgLayout → #F7F8FA / colorBgContainer → #FFFFFF
  - colorText → #1F2937 / colorTextSecondary → #4B5563 / colorBorder → #E5E7EB
  - borderRadius → 8（AntD 默认 6，按 Token 圆角 8/12/16 分级覆盖）
  - fontFamily → Inter + Noto Sans SC
- **桌面端保持原生控件观感**（QWidget/QPushButton/QLineEdit/QTabWidget/QTableWidget），不做网页样式伪装；但配色/间距/圆角/字体严格对齐 Token
- **桌面端更简洁**（隐私信任感）：顶栏常驻"本地离线引擎 · 论文不出本机"徽标（shield-check 图标）；去掉 Web 端营销区/导航噪音，聚焦 上传→报告 单线程
- 报告页桌面端用 QTextEdit / QTableWidget 渲染高亮片段

---

## 7. 无障碍与反 AI 模板自查

### 7.1 无障碍

- 正文对比度 ≥ 4.5:1（高亮仅作底色，正文恒为深色）
- 键盘可达 + `:focus-visible` 焦点环（--focus-ring）
- `prefers-reduced-motion` 支持
- 触摸目标 ≥ 44×44px
- 图表（误差带量规）提供文字替代（预估中值/区间/置信度均以文本呈现，不依赖图形）

### 7.2 反 AI 模板自查

| 检查项 | 结论 |
|--------|------|
| 无紫→粉渐变（P0） | ✅ 单一 Teal 纯色 + 同色系深浅 |
| 无 emoji 功能图标（P0） | ✅ 锁定 Lucide |
| 无空洞占位文案（P0） | ✅ 上传区/空态/错误态均为具体动作文案 |
| 无硬编码颜色（P0） | ✅ 全部 Design Token 引用 |
| 非千篇一律 Hero（P0） | ✅ 首页展示真实报告卡 mockup + 拖拽上传区 |
| 无侧条纹边框/渐变文字/毛玻璃装饰 | ✅ |
| 不堆同尺寸卡片网格 | ✅ 报告页以量规+列表+抽屉组织，非重复卡片 |

---

## 8. RoleVerdict

```
verdict: pass
blocking: []
advisory:
- 验收加严建议（已同步 PM，PRD 7.2 已更新）：预估区间必须为可见可视化元素（误差带量规），而非仅单一数字
- M1 用户确认重点：把"预估区间可视化 + 可配置阈值线"作为报告页验收重点向用户确认（差异化核心）
- Phase 2 交付：DESIGN.md 9 节 + design-system/MASTER.md + design-tokens.json/css + 页面级提示词（首页/上传/报告/登录/用量）+ AntD token 映射表
evidence:
- 竞品调研（PaperPass/知网/维普/万方）：行业报告信息结构与颜色语义已核实（红=复制/黄=引用/灰=排除/黑=原创）
- 图标库调研（Lucide/Phosphor/Tabler/Heroicons）：Lucide ISC 许可 + 统一 2px 描边 + 双端可用
- PRD v1.0：验收 7.2（区间可视化）、7.5（样本不足）、边界条件（空/错/加载/隐私）对齐
```

---

## 9. 变更记录

| 日期 | 变更 | 原因 | 影响范围 |
|------|------|------|----------|
| 2026-08-05 | v1.0 创建 | Phase 1 设计调研输出 | 全项目 |
| 2026-08-05 | 报告页置信区间升级为视觉中心 | PM 确认"预估区间+置信度"为核心差异化 | 报告页 |
| 2026-08-05 | 阈值线改为可配置（默认 20%） | 试点各校标准不一 | 报告页/设置 |
| 2026-08-05 | 高亮透明度定稿（品牌红/橙/赭黄 rgba） | PM 行业参考 + WCAG 对比度校准 | design-tokens |
| 2026-08-05 | 图标锁定 Lucide + AntD5 接入边界 | 架构师 Spec 确认 | 全项目 |
