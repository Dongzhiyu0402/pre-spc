import { Info } from 'lucide-react';

/**
 * 免责声明常驻条（AC-09 / 边界约束：所有页面渲染）
 * 文案来自 Report.disclaimer 常量："预估仅供参考，非官方检测报告"
 */
export default function Disclaimer() {
  return (
    <div className="disclaimer-bar" role="note">
      <Info size={16} aria-hidden="true" />
      <span>预估仅供参考，非官方检测报告</span>
    </div>
  );
}
