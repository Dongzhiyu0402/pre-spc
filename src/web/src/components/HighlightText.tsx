import { useMemo } from 'react';
import type { HighlightType, Segment } from '../types/api';
import './HighlightText.css';

interface Props {
  text: string;
  segments: Segment[];
  activeIndex?: number;
  onSegmentClick?: (segment: Segment, index: number) => void;
}

type Node =
  | { kind: 'text'; text: string }
  | { kind: 'hl'; text: string; segment: Segment; index: number };

const LABEL: Record<HighlightType, string> = {
  high: '高重复',
  mid: '中重复',
  cite: '引用',
  exclude: '排除',
};

function buildNodes(text: string, segments: Segment[]): Node[] {
  const sorted = [...segments].sort((a, b) => a.start_offset - b.start_offset);
  const nodes: Node[] = [];
  let cursor = 0;
  let index = 0;

  for (const seg of sorted) {
    const start = Math.max(0, Math.min(text.length, seg.start_offset));
    const end = Math.max(start, Math.min(text.length, seg.end_offset));
    if (end <= cursor || start < cursor) continue; // 跳过重叠片段，保证渲染干净
    if (start > cursor) {
      nodes.push({ kind: 'text', text: text.slice(cursor, start) });
    }
    nodes.push({ kind: 'hl', text: text.slice(start, end), segment: seg, index: index++ });
    cursor = end;
  }
  if (cursor < text.length) {
    nodes.push({ kind: 'text', text: text.slice(cursor) });
  }
  return nodes;
}

/**
 * 全文高亮视图：片段按 highlight_type 映射 --highlight-*（红/橙/赭黄/灰），
 * 正文恒为 --fg 深色（对比度 4.5:1）；片段开头带文字标签（WCAG 1.4.1 不只靠颜色）。
 */
export default function HighlightText({ text, segments, activeIndex, onSegmentClick }: Props) {
  const nodes = useMemo(() => buildNodes(text, segments), [text, segments]);

  return (
    <div className="hl-text">
      {nodes.map((node, i) => {
        if (node.kind === 'text') {
          return (
            <span key={i} className="hl-text__plain">
              {node.text}
            </span>
          );
        }
        const active = activeIndex === node.index;
        return (
          <span
            key={i}
            className={`hl-text__hl hl-text__hl--${node.segment.highlight_type} ${active ? 'hl-text__hl--active' : ''}`}
            role="button"
            tabIndex={0}
            title={`命中来源：${node.segment.matched_source} · 相似度 ${node.segment.similarity.toFixed(0)}%`}
            onClick={() => onSegmentClick?.(node.segment, node.index)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onSegmentClick?.(node.segment, node.index);
              }
            }}
          >
            <span className="hl-text__tag">{LABEL[node.segment.highlight_type]}</span>
            {node.text}
          </span>
        );
      })}
    </div>
  );
}
