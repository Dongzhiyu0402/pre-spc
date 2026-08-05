import { useId } from 'react';
import './Gauge.css';

interface GaugeProps {
  median: number;
  low: number;
  high: number;
  threshold?: number;
  /** 置信度仅用于无障碍描述（0-100） */
  confidence?: number;
  /** 样本不足宽区间提示由父级控制 */
}

const W = 680;
const H = 116;
const PAD = 44;

function xOf(v: number): number {
  const clamped = Math.max(0, Math.min(100, v));
  return PAD + (clamped / 100) * (W - PAD * 2);
}

/**
 * 误差带量规（AC-06/AC-07/AC-08）—— 自绘 SVG，横向：
 * 轨道 + 区间色带 + 中值刻度点 + 阈值线 + 端点文字 + 0-100 标尺。
 * 仅 transform/opacity 动效；禁弹跳缓动。
 */
export default function Gauge({ median, low, high, threshold, confidence }: GaugeProps) {
  const titleId = useId();
  const crossesThreshold =
    threshold !== undefined && threshold > 0 && threshold <= 100 && high > threshold;

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      role="img"
      aria-labelledby={titleId}
      className="gauge"
      width="100%"
      height="auto"
    >
      <title id={titleId}>
        预估查重率中值 {median.toFixed(1)}%，预估区间 {low.toFixed(0)}% 至 {high.toFixed(0)}%
        {confidence !== undefined ? `，置信度 ${confidence.toFixed(0)}%` : ''}
        {crossesThreshold ? `，已超过学校阈值 ${threshold}%` : ''}
      </title>

      {/* 标尺刻度 0/25/50/75/100 */}
      {[0, 25, 50, 75, 100].map((t) => (
        <g key={t}>
          <line
            x1={xOf(t)}
            y1={76}
            x2={xOf(t)}
            y2={82}
            className="gauge__tick"
          />
          <text x={xOf(t)} y={96} textAnchor="middle" className="gauge__scale">
            {t}%
          </text>
        </g>
      ))}

      {/* 轨道 */}
      <rect x={PAD} y={51} width={W - PAD * 2} height={10} rx={5} className="gauge__track" />

      {/* 区间色带 [low, high] */}
      <rect x={xOf(low)} y={45} width={Math.max(6, xOf(high) - xOf(low))} height={22} rx={6} className="gauge__band" />

      {/* 阈值线（AC-07） */}
      {threshold !== undefined && threshold > 0 && threshold <= 100 && (
        <g>
          <line
            x1={xOf(threshold)}
            y1={14}
            x2={xOf(threshold)}
            y2={86}
            strokeDasharray="4 4"
            className="gauge__threshold-line"
          />
          <text x={xOf(threshold)} y={10} textAnchor="middle" className="gauge__threshold-label">
            学校阈值 {threshold}%
          </text>
        </g>
      )}

      {/* 中值刻度点 + 引导线 */}
      <line x1={xOf(median)} y1={28} x2={xOf(median)} y2={84} className="gauge__median-line" />
      <circle cx={xOf(median)} cy={56} r={7} className="gauge__median-dot" />
      <circle cx={xOf(median)} cy={56} r={12} className="gauge__median-halo" />

      {/* 区间端点文字（mono，量规两端） */}
      <text x={PAD - 8} y={60} textAnchor="end" className="gauge__endpoint">
        {low.toFixed(0)}%
      </text>
      <text x={W - PAD + 8} y={60} textAnchor="start" className="gauge__endpoint">
        {high.toFixed(0)}%
      </text>
    </svg>
  );
}
