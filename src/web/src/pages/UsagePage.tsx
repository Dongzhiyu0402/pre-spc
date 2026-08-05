import { useCallback, useEffect, useState } from 'react';
import { Button, InputNumber, Select, Upload, message } from 'antd';
import { Coins, RotateCcw, Settings2, ShieldCheck, UploadCloud } from 'lucide-react';
import type { UploadFile } from 'antd';
import AppNav from '../components/AppNav';
import Disclaimer from '../components/Disclaimer';
import { useSchoolThreshold } from '../hooks/useSchoolThreshold';
import { getCalibrationStatus, submitCalibrationReport } from '../api/calibration';
import { getMyUsage } from '../api/usage';
import type { CalibrationStatus, Usage } from '../types/api';
import './UsagePage.css';

const PLATFORM_OPTIONS = [
  { label: '知网（CNKI）', value: 'cnki' },
  { label: '维普（VIP）', value: 'vip' },
  { label: '万方（Wanfang）', value: 'wanfang' },
];

export default function UsagePage() {
  const { threshold, setThreshold } = useSchoolThreshold();
  const [usage, setUsage] = useState<Usage | null>(null);
  const [calib, setCalib] = useState<CalibrationStatus | null>(null);
  const [thresholdDraft, setThresholdDraft] = useState<number>(threshold);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [platform, setPlatform] = useState('cnki');
  const [realRate, setRealRate] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(() => {
    void getMyUsage().then(setUsage).catch(() => undefined);
    void getCalibrationStatus().then(setCalib).catch(() => undefined);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    setThresholdDraft(threshold);
  }, [threshold]);

  const saveThreshold = () => {
    setThreshold(thresholdDraft);
    message.success('阈值已更新，报告页将按新阈值显示'); // AC-07 联动
  };

  const submitReport = async () => {
    const file = fileList[0]?.originFileObj;
    if (!file) {
      message.warning('请选择真实查重报告文件');
      return;
    }
    if (realRate === null) {
      message.warning('请填写真实查重率（0-100）');
      return;
    }
    setSubmitting(true);
    try {
      await submitCalibrationReport({
        file,
        platform,
        real_rate: realRate,
        task_id: 0, // 联调时由后端解析关联任务；Mock 阶段传 0
      });
      message.success('回传成功，样本待校验，已送 1 次免费查重'); // AC-14 激励
      setFileList([]);
      setRealRate(null);
      load();
    } catch (e) {
      message.error(e instanceof Error ? e.message : '回传失败，请重试');
    } finally {
      setSubmitting(false);
    }
  };

  const sampleReady = calib !== null && calib.sample_count >= 30;

  return (
    <div className="usage-page">
      <AppNav />
      <main className="container-narrow usage-page__main">
        <div className="page-head">
          <h1 className="page-title">用量与账户</h1>
        </div>

        {/* 账户概览 */}
        <section className="grid-quota usage-page__quota" aria-label="账户概览">
          <div className="card usage-quota-card">
            <div className="usage-quota-card__label text-muted text-sm">免费查重次数</div>
            <div className="usage-quota-card__value font-mono">
              {usage?.free_quota ?? '—'}
              <span className="usage-quota-card__unit">次剩余</span>
            </div>
          </div>
          <div className="card usage-quota-card">
            <div className="usage-quota-card__label text-muted text-sm">
              <Coins size={14} aria-hidden="true" /> 积分
            </div>
            <div className="usage-quota-card__value font-mono">
              {usage?.points ?? '—'}
              <span className="usage-quota-card__unit">查重优先扣积分</span>
            </div>
          </div>
          <div className="card usage-quota-card">
            <div className="usage-quota-card__label text-muted text-sm">校准样本数</div>
            <div className="usage-quota-card__value font-mono">
              {calib?.sample_count ?? '—'}
              <span className="usage-quota-card__unit">条（距 30 条训练阈值）</span>
            </div>
          </div>
          <div className="card usage-quota-card">
            <div className="usage-quota-card__label text-muted text-sm">预估精度</div>
            <div className="usage-quota-card__value font-mono">
              {calib?.mae !== null && calib?.mae !== undefined ? `±${calib.mae.toFixed(1)}%` : '—'}
              <span className="usage-quota-card__unit">
                {calib?.model_version ? `模型 ${calib.model_version}` : '模型积累中'}
              </span>
            </div>
          </div>
        </section>

        {/* 学校阈值设置 */}
        <section className="card usage-page__block" aria-label="学校阈值设置">
          <h2 className="usage-page__block-title">
            <Settings2 size={16} aria-hidden="true" /> 学校查重率阈值
          </h2>
          <p className="usage-page__block-desc">报告页的学校阈值线将按此绘制</p>
          <div className="usage-page__threshold">
            <InputNumber
              min={5}
              max={50}
              value={thresholdDraft}
              onChange={(v) => setThresholdDraft(v ?? 20)}
              addonAfter="%"
              style={{ width: 160 }}
              aria-label="学校查重率阈值"
            />
            <Button type="primary" onClick={saveThreshold}>
              保存
            </Button>
          </div>
        </section>

        {/* 校准报告回传 */}
        <section className="card usage-page__block usage-page__calib" aria-label="校准报告回传">
          <h2 className="usage-page__block-title">
            <UploadCloud size={16} aria-hidden="true" /> 回传真实查重报告，让预估更准
          </h2>
          <p className="usage-page__block-desc">
            上传你在知网/维普/万方的真实查重报告，我们只提取查重率数字用于校准，回传 1 份送 1 次免费查重
          </p>

          <div className="usage-page__form">
            <Upload
              maxCount={1}
              fileList={fileList}
              beforeUpload={() => false}
              onChange={({ fileList: fl }) => setFileList(fl)}
              accept=".pdf,.html,.doc,.docx"
            >
              <Button icon={<UploadCloud size={16} aria-hidden="true" />}>选择报告文件</Button>
            </Upload>
            <Select
              value={platform}
              onChange={setPlatform}
              options={PLATFORM_OPTIONS}
              style={{ width: 180 }}
              aria-label="选择平台"
            />
            <InputNumber
              min={0}
              max={100}
              value={realRate}
              onChange={setRealRate}
              addonAfter="%"
              placeholder="真实查重率"
              style={{ width: 160 }}
              aria-label="真实查重率"
            />
            <Button type="primary" icon={<RotateCcw size={16} aria-hidden="true" />} loading={submitting} onClick={submitReport}>
              回传
            </Button>
          </div>

          <div className="usage-page__calib-status">
            {sampleReady ? (
              <span className="badge">校准模型已就绪，区间更精确</span>
            ) : (
              <span className="text-muted text-sm">
                样本积累中，预估区间较宽，结果仅供参考（回传 1 份送 1 次免费查重）
              </span>
            )}
          </div>
          <div className="usage-page__privacy">
            <ShieldCheck size={16} aria-hidden="true" />
            <span>报告文件加密存储，仅用于校准，不会公开</span>
          </div>
        </section>
      </main>
      <Disclaimer />
    </div>
  );
}
