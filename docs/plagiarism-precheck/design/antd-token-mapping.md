# AntD 5 Token 映射表（Teal 设计语言 → AntD ConfigProvider theme.token）

> 目的：确保 Web 端 AntD 组件库与 `design-tokens.json`（v1.0.0）零漂移。
> 使用方式：Web 入口用 `<ConfigProvider theme={theme}>` 包裹；非 AntD 部分直接用 design-tokens.css 变量。
> 注意：AntD 只服务 Web；桌面端 PyQt6 用 QSS 消费同一 Token（见 desktop-qss.md），不引入 AntD。

## 1. 基础 Token 映射

```tsx
// src/theme.ts
import type { ThemeConfig } from 'antd';

export const antdTheme: ThemeConfig = {
  token: {
    // ---- 品牌色（核心：覆盖 AntD 默认蓝 #1677ff）----
    colorPrimary: '#0D9488',        // ↔ --accent
    colorInfo: '#2563EB',           // ↔ --info
    colorSuccess: '#16A34A',        // ↔ --success
    colorWarning: '#EA580C',        // ↔ --warn
    colorError: '#DC2626',          // ↔ --danger
    colorLink: '#0D9488',           // ↔ --accent（链接色随品牌）

    // ---- 中性色 ----
    colorBgLayout: '#F7F8FA',       // ↔ --bg（页面背景）
    colorBgContainer: '#FFFFFF',    // ↔ --surface（卡片/容器）
    colorBgElevated: '#FFFFFF',     // 下拉/弹层
    colorText: '#1F2937',           // ↔ --fg（主文本）
    colorTextSecondary: '#4B5563',  // ↔ --fg-2
    colorTextTertiary: '#6B7280',   // ↔ --muted
    colorTextQuaternary: '#9CA3AF', // ↔ --meta
    colorBorder: '#E5E7EB',         // ↔ --border
    colorBorderSecondary: '#F1F2F4',// ↔ --border-soft
    colorSplit: '#F1F2F4',          // 分隔线 ↔ --border-soft

    // ---- 圆角（AntD 默认 6，按 Token 分级覆盖）----
    borderRadius: 8,                // ↔ --radius-sm（按钮/输入框）
    borderRadiusLG: 12,             // ↔ --radius-md（卡片/弹层）
    borderRadiusSM: 8,

    // ---- 字体 ----
    fontFamily: '"Inter", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif', // ↔ --font-body
    fontFamilyCode: '"JetBrains Mono", "SFMono-Regular", Consolas, monospace',            // ↔ --font-mono（代码/数字）

    // ---- 动效 ----
    motionDurationFast: '0.15s',    // ↔ --motion-fast
    motionDurationMid: '0.2s',      // ↔ --motion-base
    motionDurationSlow: '0.3s',     // ↔ --motion-slow
    motionEaseOutBack: 'cubic-bezier(0.2, 0, 0, 1)',  // 统一缓动，禁弹跳

    // ---- 控件尺寸（触摸目标 ≥ 44px）----
    controlHeight: 40,              // 输入框/按钮高 ↔ --btn-height
    controlHeightLG: 44,            // 大控件（移动端主 CTA）
    paddingContentHorizontal: 16,
    paddingContentVertical: 12,
  },
  components: {
    Button: {
      fontWeight: 510,              // ↔ --weight-medium
      primaryShadow: 'none',
      defaultShadow: 'none',
      dangerShadow: 'none',
    },
    Card: {
      paddingLG: 20,                // ↔ --card-padding
      borderRadiusLG: 12,           // ↔ --card-radius
    },
    Input: {
      activeBorderColor: '#0D9488', // focus border ↔ --accent
      hoverBorderColor: '#0F766E',  // ↔ --accent-hover
      activeShadow: '0 0 0 3px rgba(13,148,136,0.35)', // ↔ --focus-ring
    },
    Table: {
      headerBg: '#F1F2F4',          // ↔ --surface-warm
      headerColor: '#4B5563',       // ↔ --fg-2
      rowHoverBg: '#F0FDFA',        // ↔ --accent-soft（hover 行）
      borderColor: '#E5E7EB',       // ↔ --border
    },
    Modal: {
      borderRadiusLG: 16,           // ↔ --radius-lg
    },
    Progress: {
      defaultColor: '#0D9488',      // 进度条主色 ↔ --accent
      remainingColor: '#F1F2F4',    // 轨道 ↔ --gauge-track
    },
    Tag: {
      defaultBg: '#F0FDFA',         // 徽标底 ↔ --accent-soft
    },
    Drawer: {
      colorBgElevated: '#FFFFFF',
    },
  },
};
```

## 2. 关键规则（QA 可据此扫描）

1. **禁止残留 AntD 默认蓝**：全局搜索 `#1677ff`，出现即视为 Token 覆盖失败（blocking）。
2. **报告页高亮色不走 AntD semantic token**：`--highlight-*`（rgba 红/橙/赭黄/灰）是内容标记语义色，仅在报告内容渲染时使用，**禁止**用 colorError/colorWarning 替代（它们是组件状态色，语义不同）。
3. **功能图标全 Lucide**：`lucide-react` 导入；AntD 组件内部控件图标（Table 排序箭头/Select 展开箭头/Modal 关闭/Pagination 箭头）保留默认，不参与 Lucide 统一判定。
4. **数字对齐**：查重率/字数/相似比/区间端点用 `fontFamilyCode` 或 CSS `--font-mono` + `font-variant-numeric: tabular-nums`。
5. **每屏强调色 ≤2 处**：colorPrimary 只用于主 CTA/选中态/关键高亮；标题用 colorText 深色，不用 primary。

## 3. 与验收标准（AC）的映射

| AC | 依赖的 Token/组件 |
|----|-------------------|
| AC-06 区间可视化 | 误差带量规（--gauge-band / --gauge-median / --gauge-threshold） |
| AC-07 阈值线+行动指引 | 阈值线组件（--gauge-threshold）+ 提示文案样式（--accent-soft 底 + --accent text） |
| AC-08 样本不足宽区间 | 量规色带宽度随 est_low/est_high 动态 + 提示文案 |
| AC-09 导出+免责声明 | 导出按钮（Button primary）+ 免责声明常量样式（--muted） |
| AC-16 隐私 | 桌面端隐私徽标（shield-check + --accent-soft）；Web 脱敏说明（--muted） |

---

*变更记录：v1.0.0 创建（2026-08-05，与 design-tokens.json v1.0.0 配套）*
