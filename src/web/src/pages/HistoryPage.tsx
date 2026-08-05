import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Pagination, Select, message } from 'antd';
import { FileSearch, FileText, RefreshCw } from 'lucide-react';
import AppNav from '../components/AppNav';
import StatusTag from '../components/StatusTag';
import Disclaimer from '../components/Disclaimer';
import { useCheckPolling } from '../hooks/useCheckPolling';
import { listChecks, recheck } from '../api/checks';
import { listPlans } from '../api/plans';
import type { CheckStatus, CheckTaskSummary, Plan } from '../types/api';
import { formatDateTime, formatWordCount, planNameOf } from '../utils/format';
import './HistoryPage.css';

const STATUS_OPTIONS: Array<{ label: string; value: string }> = [
  { label: '全部状态', value: 'all' },
  { label: '已完成', value: 'succeeded' },
  { label: '检测中', value: 'processing' },
  { label: '排队中', value: 'pending' },
  { label: '失败', value: 'failed' },
];

export default function HistoryPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<CheckTaskSummary[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [planFilter, setPlanFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [rechecking, setRechecking] = useState<number | null>(null);
  const [recheckTaskId, setRecheckTaskId] = useState<number | null>(null);

  const polling = useCheckPolling(recheckTaskId);

  useEffect(() => {
    void listPlans().then(setPlans).catch(() => undefined);
  }, []);

  const load = useCallback(async (p: number) => {
    setLoading(true);
    setError(undefined);
    try {
      const data = await listChecks(p, 10);
      setItems(data.items);
      setTotal(data.total);
      setPage(data.page);
    } catch (e) {
      setError(e instanceof Error ? e.message : '历史记录加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(page);
  }, [load, page]);

  // 再次检测完成后跳转新报告
  useEffect(() => {
    if (polling.done) {
      if (polling.status === 'succeeded' && recheckTaskId !== null) {
        navigate(`/report/${recheckTaskId}`, { replace: true });
      } else {
        message.error(polling.error ?? '再次检测失败');
        setRechecking(null);
        setRecheckTaskId(null);
      }
    }
  }, [polling.done, polling.status, polling.error, recheckTaskId, navigate]);

  const handleRecheck = useCallback(
    async (task: CheckTaskSummary) => {
      if (!task.plan_code) {
        message.warning('该任务缺少方案信息，无法再次检测');
        return;
      }
      setRechecking(task.task_id);
      try {
        const data = await recheck(task.task_id, { plan_code: task.plan_code });
        setRecheckTaskId(data.task_id);
      } catch (e) {
        message.error(e instanceof Error ? e.message : '再次检测失败');
        setRechecking(null);
      }
    },
    [],
  );

  const filtered = useMemo(() => {
    return items.filter((i) => {
      if (planFilter !== 'all' && i.plan_code !== planFilter) return false;
      if (statusFilter !== 'all' && i.status !== (statusFilter as CheckStatus)) return false;
      return true;
    });
  }, [items, planFilter, statusFilter]);

  return (
    <div className="history-page">
      <AppNav />
      <main className="container-narrow history-page__main">
        <div className="page-head history-page__head">
          <h1 className="page-title">历史记录</h1>
          <div className="history-page__filters">
            <Select
              value={planFilter}
              onChange={setPlanFilter}
              options={[
                { label: '全部方案', value: 'all' },
                ...plans.map((p) => ({ label: p.name, value: p.code })),
              ]}
              style={{ width: 132 }}
              aria-label="按方案筛选"
            />
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              options={STATUS_OPTIONS}
              style={{ width: 116 }}
              aria-label="按状态筛选"
            />
          </div>
        </div>

        {error ? (
          <div className="card history-page__error">
            <div>{error}</div>
            <Button type="primary" onClick={() => void load(page)}>
              重试
            </Button>
          </div>
        ) : loading ? (
          <div className="card history-page__loading">
            <div className="skeleton-block" style={{ height: 56 }} />
            <div className="skeleton-block" style={{ height: 56 }} />
            <div className="skeleton-block" style={{ height: 56 }} />
          </div>
        ) : filtered.length === 0 ? (
          <div className="card history-page__empty">
            <FileSearch size={24} aria-hidden="true" />
            <div className="history-page__empty-title">还没有查重记录，上传第一篇论文试试</div>
            <Button type="primary" onClick={() => navigate('/')}>
              上传论文
            </Button>
          </div>
        ) : (
          <div className="card history-page__list">
            {filtered.map((r) => (
              <div key={r.task_id} className="history-row">
                <FileText size={18} className="history-row__icon" aria-hidden="true" />
                <div className="history-row__main">
                  <div className="history-row__name ellipsis" title={r.file_name}>
                    {r.file_name}
                  </div>
                  <div className="history-row__meta">
                    <span className="history-row__plan">{planNameOf(plans, r.plan_code)}</span>
                    <span className="text-meta">{formatDateTime(r.created_at)}</span>
                    <span className="text-meta font-mono">{formatWordCount(r.word_count)}</span>
                  </div>
                </div>
                <StatusTag status={r.status} />
                <div className="history-row__actions">
                  {r.status === 'succeeded' && (
                    <>
                      <Button type="text" size="small" onClick={() => navigate(`/report/${r.task_id}`)}>
                        查看报告
                      </Button>
                      <Button
                        size="small"
                        icon={<RefreshCw size={14} aria-hidden="true" />}
                        loading={rechecking === r.task_id}
                        onClick={() => void handleRecheck(r)}
                      >
                        再次检测
                      </Button>
                    </>
                  )}
                  {(r.status === 'processing' || r.status === 'pending') && (
                    <span className="text-meta text-sm">检测中 · {r.progress ?? 0}%</span>
                  )}
                </div>
              </div>
            ))}

            {total > 10 && (
              <div className="history-page__pager">
                <Pagination
                  current={page}
                  total={total}
                  pageSize={10}
                  showSizeChanger={false}
                  onChange={setPage}
                />
              </div>
            )}
          </div>
        )}
      </main>
      <Disclaimer />
    </div>
  );
}
