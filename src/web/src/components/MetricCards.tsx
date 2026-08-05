import './MetricCards.css';

export interface MetricItem {
  label: string;
  value?: number;
  unit?: string;
}

interface Props {
  items: MetricItem[];
}

/** 指标小卡（去除引用率 / 去除本人率 / 单篇最大复制比）—— 缺失显示 "—"，不造假 */
export default function MetricCards({ items }: Props) {
  return (
    <div className="grid-metrics metric-cards">
      {items.map((m) => (
        <div key={m.label} className="card metric-card">
          <div className="metric-card__label text-muted text-sm">{m.label}</div>
          <div className="metric-card__value font-mono">
            {m.value === undefined || m.value === null ? '—' : `${m.value.toFixed(1)}${m.unit ?? '%'}`}
          </div>
        </div>
      ))}
    </div>
  );
}
