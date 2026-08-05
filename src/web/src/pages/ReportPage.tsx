import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Dropdown, Tag, message } from 'antd';
import {
  ArrowLeft,
  Download,
  FileText,
  Search,
  ShieldCheck,
} from 'lucide-react';
import AppNav from '../components/AppNav';
import Gauge from '../components/Gauge';
import MetricCards from '../components/MetricCards';
import SectionBars from '../components/SectionBars';
import HighlightText from '../components/HighlightText';
import SourceDrawer from '../components/SourceDrawer';
import Disclaimer from '../components/Disclaimer';
import { useSchoolThreshold } from '../hooks/useSchoolThreshold';
import { exportReport, getReport } from '../api/checks';
import { listPlans } from '../api/plans';
import { downloadTextFile, generateExportHtml, saveBlob } from '../utils/export';
import { planNameOf } from '../utils/format';
import type { Plan, Report, Segment } from '../types/api';
import './ReportPage.css';

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { threshold } = useSchoolThreshold();

  const [report, setReport] = useState<Report | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const [active, setActive] = useState<{ segment: Segment; index: number } | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const highlightRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void listPlans().then(setPlans).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!id) return;
    let alive = true;
    setLoading(true);
    setError(undefined);
    void getReport(id)
      .then((r) => {
        if (alive) setReport(r);
      })
      .catch((e) => {
        if (alive) setError(e instanceof Error ? e.message : '报告加载失败');
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, [id]);

  const crosses = report !== null && report.est_high > threshold;
  const wideInterval = report !== null && report.est_high - report.est_low >= 8;

  const handleSegmentClick = useCallback((segment: Segment, index: number) => {
    setActive({ segment, index });
    setDrawerOpen(true);
  }, []);

  const scrollToHighlights = useCallback(() => {
    highlightRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, []);

  const doExport = useCallback(
    async (format: 'pdf' | 'html') => {
      if (!report || !id) return;
      setExporting(true);
      try {
        let blob: Blob | null = null;
        try {
          blob = await exportReport(id, format);
        } catch (e) {
          // PDF 后端暂不可用（缺 reportlab）→ 自动回退 HTML（AC-09）
          if (format === 'pdf') {
            message.warning('PDF 导出暂不可用，已自动回退为 HTML 导出');
            try {
              blob = await exportReport(id, 'html');
            } catch {
              blob = null;
            }
            if (blob) {
              saveBlob(blob, `查重报告-${id}.html`);
              return;
            }
          }
          throw e;
        }
        if (blob) {
          saveBlob(blob, `查重报告-${id}.${format}`);
        } else {
          // Mock：本地生成含免责声明的 HTML
          downloadTextFile(
            `查重报告-${id}-${format}.html`,
            generateExportHtml(report, threshold),
          );
          message.info('当前为 Mock 模式，导出 HTML 预览；联调后将返回真实文件');
        }
      } catch (e) {
        message.error(e instanceof Error ? e.message : '导出失败');
      } finally {
        setExporting(false);
      }
    },
    [id, report, threshold],
  );

  if (loading) {
    return (
      <div className="report-page">
        <AppNav />
        <main className="container-narrow report-page__main">
          <div className="skeleton-block" style={{ height: 24, width: 200 }} />
          <div className="skeleton-block" style={{ height: 220, marginTop: 16 }} />
          <div className="skeleton-block" style={{ height: 120, marginTop: 16 }} />
        </main>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="report-page">
        <AppNav />
        <main className="container-narrow report-page__main">
          <div className="card report-page__error">
            <Search size={24} aria-hidden="true" />
            <div className="report-page__error-title">{error ?? '报告不存在或已删除'}</div>
            <div className="text-muted text-sm">该任务可能未完成或已过期，请返回历史记录重新查看</div>
            <Button type="primary" onClick={() => navigate('/history')}>
              返回历史记录
            </Button>
          </div>
        </main>
        <Disclaimer />
      </div>
    );
  }

  const planName = planNameOf(plans, report.plan_code);
  const metrics = report.metrics;
  const firstHigh = report.segments.findIndex((s) => s.highlight_type === 'high');

  return (
    <div className="report-page">
      <AppNav />

      {/* 报告工具条 */}
      <div className="report-page__toolbar">
        <div className="container report-page__toolbar-inner">
          <button type="button" className="report-page__back" onClick={() => navigate('/history')}>
            <ArrowLeft size={16} aria-hidden="true" />
            历史记录
          </button>
          <div className="report-page__file">
            <FileText size={16} aria-hidden="true" />
            <span className="ellipsis" title={report.file_name}>
              {report.file_name ?? `查重报告 · 任务 ${report.task_id}`}
            </span>
            <Tag className="report-page__plan">{planName}</Tag>
          </div>
          <Dropdown
            menu={{
              items: [
                { key: 'pdf', label: '导出 PDF' },
                { key: 'html', label: '导出 HTML' },
              ],
              onClick: ({ key }) => void doExport(key as 'pdf' | 'html'),
            }}
          >
            <Button type="primary" icon={<Download size={16} aria-hidden="true" />} loading={exporting}>
              导出报告
            </Button>
          </Dropdown>
        </div>
      </div>

      <main className="container-narrow report-page__main">
        {/* 预估结果卡 */}
        <section className="card report-page__result" aria-label="预估结果">
          <div className="report-page__result-head">
            <div>
              <div className="eyebrow">预估查重率</div>
              <div className="report-page__median font-mono">{report.est_median.toFixed(1)}%</div>
              <div className="report-page__range font-mono">
                {report.est_low.toFixed(0)}% – {report.est_high.toFixed(0)}%
              </div>
            </div>
            <div className="report-page__result-right">
              <span className="badge">置信度 {report.confidence.toFixed(0)}%</span>
            </div>
          </div>

          <div className="report-page__gauge">
            <Gauge
              median={report.est_median}
              low={report.est_low}
              high={report.est_high}
              threshold={threshold}
              confidence={report.confidence}
            />
          </div>

          {crosses && (
            <div className="report-page__guidance" role="status">
              <ShieldCheck size={18} aria-hidden="true" />
              <span>
                你的预估区间跨过学校阈值 {threshold}%，建议优先修改高亮片段
                {firstHigh >= 0 && (
                  <button type="button" className="report-page__link" onClick={scrollToHighlights}>
                    查看高亮片段
                  </button>
                )}
              </span>
            </div>
          )}

          {wideInterval && (
            <div className="report-page__wide text-muted text-sm">
              预估区间较宽，校准样本积累中，结果仅供参考
            </div>
          )}
        </section>

        {/* 三指标 */}
        <section className="report-page__section" aria-label="附加指标">
          <MetricCards
            items={[
              { label: '去除引用率', value: metrics?.removal_cite_rate },
              { label: '去除本人率', value: metrics?.removal_self_rate },
              { label: '单篇最大复制比', value: metrics?.max_single_source_rate },
            ]}
          />
        </section>

        {/* 章节重复率 */}
        {report.chapters && report.chapters.length > 0 && (
          <section className="card report-page__section" aria-label="章节重复率">
            <h2 className="report-page__section-title">章节重复率</h2>
            <SectionBars chapters={report.chapters} onSelect={scrollToHighlights} />
          </section>
        )}

        {/* 全文高亮视图 */}
        <section className="card report-page__section" ref={highlightRef} aria-label="全文相似片段">
          <h2 className="report-page__section-title">全文相似片段</h2>
          {report.segments.length === 0 ? (
            <div className="report-page__empty">
              未发现明显相似片段，继续保持
            </div>
          ) : report.full_text ? (
            <HighlightText
              text={report.full_text}
              segments={report.segments}
              activeIndex={active?.index}
              onSegmentClick={handleSegmentClick}
            />
          ) : (
            <div className="text-muted text-sm">全文暂不可用（联调后展示）</div>
          )}
        </section>

        <Disclaimer />
      </main>

      <SourceDrawer
        open={drawerOpen}
        segment={active?.segment ?? null}
        contextText={
          active && report.full_text
            ? report.full_text.slice(active.segment.start_offset, active.segment.end_offset)
            : undefined
        }
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
}
