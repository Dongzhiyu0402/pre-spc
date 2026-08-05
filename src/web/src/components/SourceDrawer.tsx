import { Drawer, Tag } from 'antd';
import { BookOpen } from 'lucide-react';
import type { Segment } from '../types/api';
import './SourceDrawer.css';

interface Props {
  open: boolean;
  segment: Segment | null;
  /** 原文片段（从 full_text 截取，与来源对照） */
  contextText?: string;
  onClose: () => void;
}

/** 来源抽屉：来源列表 + 左原文右来源对照（移动端 AntD Drawer 自动降级底部面板） */
export default function SourceDrawer({ open, segment, contextText, onClose }: Props) {
  const detail = segment?.source_detail;

  return (
    <Drawer
      title={
        <span className="src-drawer__title">
          <BookOpen size={16} aria-hidden="true" />
          来源详情
        </span>
      }
      placement="right"
      width={480}
      open={open}
      onClose={onClose}
    >
      {!segment ? (
        <div className="src-drawer__empty text-muted">
          点击文中的高亮片段，可查看命中来源与原文对照
        </div>
      ) : (
        <div className="src-drawer__body">
          <section className="src-drawer__block">
            <h4 className="src-drawer__label">原文片段</h4>
            <p className="src-drawer__quote">{contextText ?? '（原文片段暂不可用）'}</p>
          </section>

          <section className="src-drawer__block">
            <h4 className="src-drawer__label">命中来源对照</h4>
            {detail ? (
              <div className="src-drawer__source">
                <div className="src-drawer__source-title">{detail.title}</div>
                <dl className="src-drawer__dl">
                  <div className="src-drawer__dl-row">
                    <dt>作者</dt>
                    <dd>{detail.author}</dd>
                  </div>
                  <div className="src-drawer__dl-row">
                    <dt>出处</dt>
                    <dd>{detail.venue}</dd>
                  </div>
                  <div className="src-drawer__dl-row">
                    <dt>年份</dt>
                    <dd>{detail.year}</dd>
                  </div>
                  <div className="src-drawer__dl-row">
                    <dt>相似度</dt>
                    <dd className="font-mono">{segment.similarity.toFixed(0)}%</dd>
                  </div>
                  <div className="src-drawer__dl-row">
                    <dt>引用标记</dt>
                    <dd>
                      {detail.is_cited ? <Tag color="success">已引用</Tag> : <Tag color="warning">未引用</Tag>}
                    </dd>
                  </div>
                </dl>
              </div>
            ) : (
              <div className="src-drawer__fallback">
                来源：{segment.matched_source} · 相似度 {segment.similarity.toFixed(0)}%
                <div className="text-meta text-sm">（详细来源信息后端补充中）</div>
              </div>
            )}
          </section>
        </div>
      )}
    </Drawer>
  );
}
