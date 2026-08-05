import type { ThemeConfig } from 'antd';

/**
 * AntD 5 Token 映射（来自 antd-token-mapping.md）
 * 唯一目标：AntD 组件库与 design-tokens.json 零漂移。
 * 注意：colorPrimary 必须覆盖 AntD 默认蓝（QA 扫描其十六进制残留）。
 */
export const antdTheme: ThemeConfig = {
  token: {
    // ---- 品牌色 ----
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

    // ---- 圆角 ----
    borderRadius: 8,                // ↔ --radius-sm（按钮/输入框）
    borderRadiusLG: 12,             // ↔ --radius-md（卡片/弹层）
    borderRadiusSM: 8,

    // ---- 字体 ----
    fontFamily: '"Inter", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif',
    fontFamilyCode: '"JetBrains Mono", "SFMono-Regular", Consolas, monospace',

    // ---- 动效（禁弹跳/弹性）----
    motionDurationFast: '0.15s',
    motionDurationMid: '0.2s',
    motionDurationSlow: '0.3s',
    motionEaseOutBack: 'cubic-bezier(0.2, 0, 0, 1)',

    // ---- 控件尺寸（触摸目标 ≥ 44px）----
    controlHeight: 40,
    controlHeightLG: 44,
    paddingContentHorizontal: 16,
    paddingContentVertical: 12,
  },
  components: {
    Button: {
      fontWeight: 510,
      primaryShadow: 'none',
      defaultShadow: 'none',
      dangerShadow: 'none',
    },
    Card: {
      paddingLG: 20,
      borderRadiusLG: 12,
    },
    Input: {
      activeBorderColor: '#0D9488',
      hoverBorderColor: '#0F766E',
      activeShadow: '0 0 0 3px rgba(13,148,136,0.35)',
    },
    Table: {
      headerBg: '#F1F2F4',
      headerColor: '#4B5563',
      rowHoverBg: '#F0FDFA',
      borderColor: '#E5E7EB',
    },
    Modal: {
      borderRadiusLG: 16,
    },
    Progress: {
      defaultColor: '#0D9488',
      remainingColor: '#F1F2F4',
    },
    Tag: {
      defaultBg: '#F0FDFA',
    },
    Drawer: {
      colorBgElevated: '#FFFFFF',
    },
  },
};
