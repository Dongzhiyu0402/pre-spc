# 预查重项目 DESIGN.md

> 生成日期：2026-08-05 | 设计师：颜好看 (UI/UX) | 基于：Spec v1.0（§7 页面清单 / §8 设计 Token / AC-05~09 报告验收锁定）
> 三轴刻度：DESIGN_VARIANCE=4 / MOTION_INTENSITY=3 / VISUAL_DENSITY=5
> 寄存器：Product（工具型，标杆=赢得熟悉感）
> Token 唯一源：design-tokens.json v1.0.0（同目录）

---

## 1. Visual Theme & Atmosphere（视觉主题与氛围）

- **视觉主题关键词**：可信、清爽、精确、克制、学术工具的新鲜感
- **氛围描述**：浅色冷调为主，品牌强调色仅 Teal 一处；报告页以"预估区间 + 置信度"的诚实可视化建立信任（区别于竞品的虚假精确与陈旧营销风）；整体接近 Grammarly 的清爽工具感 + Linear 的排版精度 + Notion 的克制留白
- **对标品牌**：Linear（工具感/状态完整度）、Grammarly（清爽报告气质）、Notion（中性色基底）；不抄 PaperPass/知网/维普的陈旧营销风，但**保留行业已认知的颜色语义**（红=复制/黄=引用/灰=排除/黑=原创）
- **反 AI 模板**：无紫粉渐变、无毛玻璃装饰、无发光边框、无"大标题+副标题+居中 CTA+抽象图形"的千篇一律 Hero——首页展示真实报告卡 mockup + 拖拽上传区

## 2. Color Palette & Roles（色彩与角色）

> 完整值见 `design-tokens.json`（primitive/semantic/component 三层）。此处为角色说明。

- **A1-identity**：`--bg #F7F8FA` / `--surface #FFFFFF` / `--fg #1F2937` / `--muted #6B7280` / `--accent #0D9488` / `--border #E5E7EB`
- **A2-semantic（状态色，组件状态用，映射 AntD semantic）**：`--success #16A34A` / `--warn #EA580C` / `--danger #DC2626` / `--info #2563EB`
- **C-extension（内容标记语义色，报告页高亮，独立成组，不走 AntD semantic token）**：
  - `--highlight-high rgba(220,38,38,0.13)` 高重复（红）
  - `--highlight-mid rgba(234,88,12,0.12)` 中重复（橙）
  - `--highlight-cite rgba(180,83,9,0.16)` 引用（赭黄，加深保对比）
  - `--highlight-exclude rgba(107,114,128,0.10)` 排除（灰）
  - 原创 = 无底色，正文默认 `--fg`
- **每屏强调色 ≤2 处**：仅用于主 CTA、选中态、关键数据高亮（预估中值刻度点）。标题用深色中性色，不用强调色
- **高亮对比度规则**：高亮仅作底色，正文恒为深色 `--fg`（#1F2937），保证 WCAG 4.5:1
- 配色来源：color-palettes.md 生产力青绿（Teal）系 + 竞品调研校准

## 3. Typography（排版）

- **标题/正文**：`--font-display` / `--font-body` = Inter + Noto Sans SC + PingFang SC/Microsoft YaHei fallback（中文场景强制 Noto Sans SC，避免回退系统字）
- **数据/等宽**：`--font-mono` = JetBrains Mono + SFMono-Regular/Consolas（报告页查重率、字数、相似比、区间端点用等宽 + `font-variant-numeric: tabular-nums` 对齐）
- **Google Fonts @import**：
  ```css
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&family=JetBrains+Mono:wght@400;500&display=swap');
  ```
- **字号阶梯**：xs 12 / sm 14 / md 16（正文基准）/ lg 18 / xl 20 / 2xl 24 / 3xl 32 / 4xl 40（px；rem 见 design-tokens.css）
- **字重三级**：400 正文 / 510 次标题·按钮·表头 / 590 大标题·CTA
- **行高**：正文 1.6 / 标题 1.25
- **字距**：ALL CAPS 小标签 `0.06em`；标题 `-0.02em`；正文 0
- **表格/数据数字**：一律 `--font-mono` + tabular-nums（"专业可信感"关键细节，竞品普遍忽视）

## 4. Components（组件规范）

> 所有交互组件必须覆盖：default / hover / focus-visible / active / disabled / loading / error。图标统一 Lucide（功能图标），尺寸 16（行内）/ 20（按钮内）/ 24（独立）。

| 组件 | 规范 |
|------|------|
| **按钮 Primary** | bg `--accent` / text `--accent-on` / hover `--accent-hover` / active `--accent-active`；radius 8px；高 40px；padding-x 16px；disabled opacity 0.5；loading 内置 spinner（SVG，禁 emoji） |
| **按钮 Secondary** | bg `--surface` / 1px border `--border` / text `--fg`；hover border→`--accent` |
| **按钮 Ghost** | 透明底 / text `--accent` / hover bg `--accent-soft` |
| **按钮 Destructive** | bg `--danger` / text `#fff`（用于删除报告等确认操作） |
| **输入框** | bg `--surface` / border `--border` / radius 8px / 高 40px；focus：border→`--accent` + `--focus-ring`；error：border→`--danger` + 就近错误文案；label 可见（禁仅 placeholder） |
| **卡片** | bg `--surface` / 1px border `--border` / radius 12px / padding 20px；无默认阴影（hover 可 `--elev-raised`）；禁彩色左边框 |
| **导航** | 顶部极简导航（Logo + 方案选择 + 历史 + 登录/用量）；桌面端同构 |
| **上传拖拽区** | 2px dashed border `--border`；hover/拖入 → border `--accent` + bg `--accent-soft`；内含 upload-cloud 图标 + 主文案 + 格式/大小说明；文件已选态显示文件名/大小/字数/移除按钮 |
| **预估结果卡（报告页核心）** | 见 §页面方向与 antd-token-mapping；含误差带量规组件 |
| **误差带量规** | 横向；轨道 `--gauge-track`；区间色带 `--gauge-band`（rgba teal 0.18）；中值刻度点 `--gauge-median`（Teal，最亮点）；阈值线 `--gauge-threshold`（红虚线）+ 阈值标签；区间端点文字 mono；样本不足时色带自动变宽 |
| **章节重复率条** | 细进度条（高 6px，radius pill）；背景 `--gauge-track`；填充按重复率等级着色（≤10 绿 / 10-20 Teal / 20-30 橙 / >30 红） |
| **全文高亮视图** | 正文 `--fg`；高亮底色用 `--highlight-*`（行业色义）；点击片段高亮边框 → 打开来源抽屉 |
| **来源抽屉** | 右侧滑出（移动端底部面板）；来源列表：篇名/作者/出处/年份/相似比/是否引用徽标；左原文右来源对照；关闭按钮 X（Lucide） |
| **徽标 Badge** | 置信度徽标（如"置信度 82%"）：radius pill，bg `--accent-soft`，text `--accent`；隐私徽标（桌面端"本地离线引擎"）：shield-check 图标 + text |
| **Toast** | 操作成功/失败提示，`--z-toast`，150-200ms 进入，3s 自动消失（可手动关闭） |
| **模态框** | radius 16px，`--z-modal`，遮罩 rgba(0,0,0,0.4)，内容区 `--surface`，关闭按钮 Lucide |
| **骨架屏** | 报告加载中占位，微光动画（仅 opacity/transform，禁 width/height 动画） |

## 5. Layout & Spacing（布局与间距）

- **间距基准**：4px 网格（4/8/12/16/20/24/32/40/48/64）
- **圆角阶梯**：sm 8 / md 12 / lg 16 / pill
- **容器**：`--container-max 1200px`；内容页 `max-w-4xl 896px`；表单卡 `max-w-2xl 672px`
- **响应式断点**：sm 640 / md 768 / lg 1024 / xl 1280
- **网格**：桌面 12 列 gap 24；平板 8 列；手机 4 列
- **节区节奏**：桌面 80 / 平板 48 / 手机 32（`--section-y-*`）
- **Variance=4 布局规则**：主流程可预测网格；报告页允许非对称（左原文右来源对照）；>3 的非对称在 <768px 回退单列

## 6. Depth & Elevation（深度与阴影）

- **三级层级**：`--elev-flat`（默认）/ `--elev-ring`（1px 边框环，卡片/表格）/ `--elev-raised`（模糊阴影，下拉/抽屉/悬浮卡）
- **z-index**：base 0 / dropdown 1000 / sticky 1100 / modal 1200 / toast 1300
- **毛玻璃/模糊**：禁止装饰性 backdrop-filter；仅允许功能性的半透明（如模态遮罩）
- **深色模式**：本期不做（Spec 锁定浅色主题），但 Token 结构预留

## 7. Do's & Don'ts（设计守则）

**✅ Do**
1. 报告页永远展示"预估区间 + 置信度"（误差带量规），绝不只给单一数字（AC-06/AC-08）
2. 沿用行业颜色语义：红=高重复 / 橙=中重复 / 黄=引用 / 灰=排除 / 黑=原创
3. 高亮仅作底色，正文恒为深色，保证 4.5:1
4. 首页展示真实产品内容（报告卡 mockup + 拖拽区），不用抽象图形
5. 报告页始终给"下一步"行动指引（跨阈值提示优先改哪些片段），把焦虑转化为行动
6. 免责声明常驻："预估仅供参考，非官方检测报告"
7. 隐私承诺可视化：桌面端"本地离线引擎·论文不出本机"徽标；Web 端脱敏说明
8. 报告数字用 mono + tabular-nums 对齐

**❌ Don't**
1. 禁 emoji 作功能图标（锁 Lucide 16/20/24）
2. 禁紫→粉渐变、发光边框、毛玻璃装饰、渐变文字、侧条纹边框
3. 禁空洞占位文案（"Welcome to"/"Lorem ipsum"）
4. 禁硬编码颜色（唯一例外 #fff/#000，全部走 Token）
5. 禁虚构指标（无来源的"10,000+ 用户"）
6. 禁把高亮色混入界面强调色体系（红/橙/黄只在报告内容标记出现）
7. 禁单一环形或单一数字呈现查重率（虚假精确）
8. 禁红色大面积警示背景（用户焦虑场景，红色仅作片段语义）

## 8. Responsive & Accessibility（响应式与无障碍）

- **响应式策略**：mobile-first；首页/报告页在 <768px 回退单列；来源抽屉移动端改底部面板；导航移动端收起
- **无障碍（WCAG 2.1 AA，P2 但设计期已内置）**：
  - 正文对比度 ≥ 4.5:1（高亮底色方案已保证）
  - 键盘可达：全组件 `:focus-visible` 显示 `--focus-ring`；模态/抽屉焦点陷阱 + Esc 关闭
  - `prefers-reduced-motion`：全局降级（design-tokens.css 已含）
  - 触摸目标 ≥ 44×44px
  - 误差带量规提供文本替代（中值/区间/置信度均以文字呈现，不依赖图形）；色义高亮辅以文字标签（"高重复""引用"），不只靠颜色传达含义
  - 表单 label 可见；错误就近显示
- **5 态覆盖**：Loading（骨架屏/进度条）/ Empty（引导文案+CTA）/ Error（错误码+重试，不消耗次数）/ Populated / Edge（超长截断、10 万字上限拦截）

## 9. Agent Implementation Guide（实现指南）

> 前端按此实现，Token 从 `design-tokens.json` / `design-tokens.css` 引用，禁止硬编码。

### 9.1 Web（React 18 + Vite + TS + AntD 5 + lucide-react）

- AntD 主题覆盖见 `antd-token-mapping.md`（ConfigProvider theme.token，colorPrimary→Teal 等），确保组件库与 Token 零漂移
- 非 AntD 部分（拖拽区、量规、高亮视图、抽屉骨架）直接用 design-tokens.css 变量
- 功能图标全 `lucide-react`；AntD 组件内部控件图标保留默认
- 报告页误差带量规实现建议：SVG 绘制（rect 轨道 + rect 色带 + circle 中值点 + line 阈值线），或 AntD Progress 的 line 变体 + 自定义 overlay；阈值线/区间端点文字用 `--font-mono`
- 高亮视图：富文本渲染，片段按 `highlight_type` 映射 `--highlight-*`；点击片段绑定来源抽屉

### 9.2 桌面端（PyQt6）

- QSS 映射要点见 `desktop-qss.md`；Token 值由同一份 design-tokens.json 生成（构建时注入或运行时常量表）
- 图标：Lucide SVG 打包资源 + QSvgRenderer → QIcon
- 报告高亮：QTextEdit + QTextCharFormat（背景色用对应 rgba）

### 9.3 已知坑提醒

| 坑 | 修法 |
|----|------|
| AntD 默认蓝 #1677ff 泄漏 | 必须在 ConfigProvider 覆盖 colorPrimary；QA 扫描 `#1677ff` 残留 |
| Noto Sans SC 1MB+ | 子集化或 CDN 分片，preload woff2 |
| 高亮底色对比度 | 正文恒为 --fg 深色，勿在高亮上用浅色文字 |
| PyInstaller 杀软误报 | onedir 模式 + 白名单（架构侧） |
| 数字对齐漂移 | 所有报告数字组件统一 --font-mono + tabular-nums |

---

*变更记录：v1.0.0 创建（2026-08-05，Phase 2 设计细化，对齐 Spec §8/§7/AC-05~09）*
