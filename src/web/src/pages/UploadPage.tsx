import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Progress, Tag } from 'antd';
import { ArrowRight, History as HistoryIcon, ShieldCheck } from 'lucide-react';
import AppNav from '../components/AppNav';
import UploadDropzone, { type DropzoneFile } from '../components/UploadDropzone';
import ReportCardMock from '../components/ReportCardMock';
import StatusTag from '../components/StatusTag';
import Disclaimer from '../components/Disclaimer';
import { useAuth } from '../hooks/useAuth';
import { useCheckPolling } from '../hooks/useCheckPolling';
import { ApiError } from '../api/client';
import { createCheck, listChecks } from '../api/checks';
import { listPlans } from '../api/plans';
import { getMyUsage } from '../api/usage';
import type { CheckTaskSummary, Plan, Usage } from '../types/api';
import { formatDateTime, planNameOf } from '../utils/format';
import './UploadPage.css';

export default function UploadPage() {
  const { authed } = useAuth();
  const navigate = useNavigate();

  const [plans, setPlans] = useState<Plan[]>([]);
  const [planCode, setPlanCode] = useState('cnki_sim');
  const [dropFile, setDropFile] = useState<DropzoneFile | null>(null);
  const [error, setError] = useState<string>();
  const [usage, setUsage] = useState<Usage | null>(null);
  const [recent, setRecent] = useState<CheckTaskSummary[]>([]);
  const [taskId, setTaskId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  const polling = useCheckPolling(taskId);
  const quotaZero = usage !== null && usage.free_quota <= 0;

  // 数据加载
  useEffect(() => {
    let alive = true;
    void listPlans()
      .then((data) => {
        if (!alive) return;
        setPlans(data);
        setPlanCode((cur) => (data.some((p) => p.code === cur) ? cur : (data[0]?.code ?? cur)));
      })
      .catch(() => {
        if (alive) setPlans([]);
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (!authed) return;
    void getMyUsage().then(setUsage).catch(() => undefined);
    void listChecks(1, 5)
      .then((d) => setRecent(d.items))
      .catch(() => undefined);
  }, [authed]);

  // 轮询完成 → 跳转报告页
  useEffect(() => {
    if (polling.done) {
      if (polling.status === 'succeeded' && taskId !== null) {
        navigate(`/report/${taskId}`, { replace: true });
      } else {
        setBusy(false);
        setError(polling.error ?? '检测失败，请重试');
        setTaskId(null);
      }
    }
  }, [polling.done, polling.status, polling.error, taskId, navigate]);

  const handleSubmit = useCallback(async () => {
    setError(undefined);
    if (!authed) {
      navigate('/login?redirect=/');
      return;
    }
    if (!dropFile) {
      setError('请先选择论文文件');
      return;
    }
    if (quotaZero) {
      navigate('/usage'); // AC-04：免费次数为 0 跳转用量页
      return;
    }
    setBusy(true);
    try {
      const task = await createCheck(dropFile.file, planCode);
      setTaskId(task.task_id);
    } catch (e) {
      setBusy(false);
      if (e instanceof ApiError && e.status === 402) {
        navigate('/usage'); // AC-04：真实后端免费次数耗尽 → 跳用量页
        return;
      }
      setError(e instanceof Error ? e.message : '创建检测任务失败');
    }
  }, [authed, dropFile, planCode, quotaZero, navigate]);

  return (
    <div className="upload-page">
      <AppNav />
      <main className="container upload-page__main">
        <div className="grid-home">
          {/* 左栏 */}
          <section className="upload-page__left" aria-label="上传检测">
            <h1 className="upload-page__h1">上传论文，预估查重率</h1>
            <p className="upload-page__sub">
              送检前先预估，输出预估区间与置信度，省下反复送检的钱
            </p>

            <UploadDropzone
              file={dropFile}
              error={error}
              disabled={quotaZero}
              onSelect={(item, validation) => {
                setDropFile(item);
                setError(validation.ok ? undefined : validation.error);
              }}
              onDisabledClick={() => navigate('/usage')}
            />

            <div className="upload-page__plans">
              <div className="upload-page__plans-title">检测方案</div>
              <div className="grid-plans">
                {plans.map((p) => {
                  const selected = p.code === planCode;
                  return (
                    <button
                      key={p.code}
                      type="button"
                      className={`plan-card ${selected ? 'plan-card--selected' : ''}`}
                      onClick={() => setPlanCode(p.code)}
                      aria-pressed={selected}
                    >
                      <span className="plan-card__name">{p.name}</span>
                      <span className="plan-card__type">
                        {p.type === 'engine' ? '自研模拟' : 'API'}
                      </span>
                      <span className="plan-card__price">
                        {String(p.price_info?.price_text ?? '免费')}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {busy ? (
              <div className="upload-page__busy">
                <Progress percent={polling.progress} status="active" />
                <div className="text-muted text-sm">正在排队检测，约 30 秒内出结果</div>
              </div>
            ) : (
              <Button
                type="primary"
                size="large"
                className="upload-page__cta"
                icon={<ArrowRight size={18} aria-hidden="true" />}
                onClick={handleSubmit}
              >
                开始检测
              </Button>
            )}

            <div className="upload-page__privacy">
              <ShieldCheck size={16} aria-hidden="true" />
              <span>文档默认脱敏后入库，可随时删除</span>
            </div>

            {/* 历史记录（首页缩略） */}
            <section className="upload-page__recent" aria-label="最近检测">
              <div className="upload-page__recent-head">
                <span className="eyebrow">最近检测</span>
                <button
                  type="button"
                  className="upload-page__link"
                  onClick={() => navigate('/history')}
                >
                  查看全部
                </button>
              </div>
              {recent.length === 0 ? (
                <div className="upload-page__empty">
                  <HistoryIcon size={20} aria-hidden="true" />
                  <span>还没有检测记录，上传你的第一篇论文试试</span>
                </div>
              ) : (
                <ul className="upload-page__recent-list">
                  {recent.map((r) => (
                    <li key={r.task_id} className="upload-page__recent-item">
                      <span className="upload-page__recent-name ellipsis" title={r.file_name}>
                        {r.file_name}
                      </span>
                      <Tag className="upload-page__recent-plan">
                        {planNameOf(plans, r.plan_code)}
                      </Tag>
                      <span className="upload-page__recent-time text-meta">
                        {formatDateTime(r.created_at)}
                      </span>
                      <StatusTag status={r.status} />
                      {r.status === 'succeeded' && (
                        <button
                          type="button"
                          className="upload-page__link"
                          onClick={() => navigate(`/report/${r.task_id}`)}
                        >
                          查看报告
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </section>

          {/* 右栏：真实报告卡 mockup */}
          <aside className="upload-page__right" aria-label="示例报告">
            <ReportCardMock />
          </aside>
        </div>
      </main>
      <Disclaimer />
    </div>
  );
}
