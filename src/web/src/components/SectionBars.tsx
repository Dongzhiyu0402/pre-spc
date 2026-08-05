import type { ChapterStat } from '../types/api';
import { formatRate, rateLevel } from '../utils/format';

interface Props {
  chapters: ChapterStat[];
  onSelect?: (chapter: ChapterStat) => void;
}

const LEVEL_COLORS: Record<string, string> = {
  low: 'var(--success)',
  ok: 'var(--accent)',
  mid: 'var(--warn)',
  high: 'var(--danger)',
};

/** 章节重复率条：细进度条（6px pill），按等级着色，hover 高亮可点击定位 */
export default function SectionBars({ chapters, onSelect }: Props) {
  return (
    <div>
      {chapters.map((c) => (
        <div
          key={c.title}
          className="chapter-row"
          role="button"
          tabIndex={0}
          onClick={() => onSelect?.(c)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onSelect?.(c);
            }
          }}
        >
          <span className="chapter-row__title ellipsis" title={c.title}>
            {c.title}
          </span>
          <div className="chapter-track">
            <div
              className="chapter-fill"
              style={{
                width: `${Math.max(2, Math.min(100, c.rate))}%`,
                background: LEVEL_COLORS[rateLevel(c.rate)],
              }}
            />
          </div>
          <span className="chapter-row__rate font-mono">{formatRate(c.rate)}</span>
        </div>
      ))}
    </div>
  );
}
