import Gauge from './Gauge';
import './ReportCardMock.css';

/**
 * 首页右侧「真实报告卡 mockup」（反千篇一律 Hero）
 * 静态展示具体数字：18.6% + 区间 14–24% + 量规 + 章节条 + 标红片段 + 置信度徽标。
 */
export default function ReportCardMock() {
  return (
    <div className="card card-hoverable mock-card" aria-label="示例报告预览">
      <div className="mock-card__head">
        <span className="eyebrow">示例报告 · 知网模拟</span>
        <span className="badge">置信度 82%</span>
      </div>

      <div className="mock-card__median">
        <div className="mock-card__median-num font-mono">18.6%</div>
        <div className="mock-card__median-label">预估查重率 · 区间 14% – 24%</div>
      </div>

      <Gauge median={18.6} low={14} high={24} threshold={20} />

      <div className="mock-card__chapters">
        <div className="mock-card__chapter">
          <span className="mock-card__chapter-name">文献综述</span>
          <div className="chapter-track">
            <div className="chapter-fill mock-fill--high" style={{ width: '35%' }} />
          </div>
          <span className="mock-card__chapter-rate font-mono">35%</span>
        </div>
        <div className="mock-card__chapter">
          <span className="mock-card__chapter-name">实验与结果</span>
          <div className="chapter-track">
            <div className="chapter-fill mock-fill--mid" style={{ width: '24%' }} />
          </div>
          <span className="mock-card__chapter-rate font-mono">24%</span>
        </div>
      </div>

      <p className="mock-card__quote">
        卷积神经网络凭借其强大的特征提取能力，被广泛应用于图像分类、目标检测与语义分割等任务。
        <span className="mock-card__quote-high">在 CIFAR-10 数据集上的对比实验中</span>
        本文方法识别准确率为 91.3%，高于基线模型的 85.2%。
      </p>

      <div className="mock-card__foot text-meta text-xs">
        送检前先预估，省下反复送检的钱
      </div>
    </div>
  );
}
