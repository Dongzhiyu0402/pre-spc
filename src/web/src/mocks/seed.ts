import type {
  CalibrationStatus,
  CheckTaskSummary,
  Plan,
  Report,
  Segment,
  Usage,
  User,
} from '../types/api';

/**
 * Mock 种子数据（后端联调后移除）
 * 原则：数字真实可信（符合产品语境），禁虚构大数字；文案非空洞占位。
 */

export const seedUser: User = {
  id: 1,
  email: 'demo@pre-spc.cn',
  nickname: '林晓（演示）',
  role: 'user',
  free_quota: 3,
  points: 120,
  created_at: '2026-08-01T10:00:00+08:00',
};

export const seedPlans: Plan[] = [
  {
    code: 'cnki_sim',
    name: '知网模拟',
    type: 'engine',
    enabled: true,
    price_info: { price_text: '免费 · 消耗 1 次额度', consumes_free: true },
  },
  {
    code: 'vip_sim',
    name: '维普模拟',
    type: 'engine',
    enabled: true,
    price_info: { price_text: '免费 · 消耗 1 次额度', consumes_free: true },
  },
  {
    code: 'wanfang_sim',
    name: '万方模拟',
    type: 'engine',
    enabled: true,
    price_info: { price_text: '免费 · 消耗 1 次额度', consumes_free: true },
  },
  {
    code: 'api_placeholder',
    name: '第三方 API',
    type: 'api',
    enabled: true,
    price_info: { price_text: '积分 100 / 次', consumes_points: 100 },
  },
];

export const seedChecks: CheckTaskSummary[] = [
  {
    task_id: 11,
    status: 'succeeded',
    progress: 100,
    plan_code: 'cnki_sim',
    file_name: '论文开题报告.docx',
    word_count: 12000,
    created_at: '2026-08-05T21:30:00+08:00',
  },
  {
    task_id: 10,
    status: 'succeeded',
    progress: 100,
    plan_code: 'vip_sim',
    file_name: '实验方法.docx',
    word_count: 8000,
    created_at: '2026-08-05T20:10:00+08:00',
  },
  {
    task_id: 9,
    status: 'processing',
    progress: 62,
    plan_code: 'cnki_sim',
    file_name: '文献综述.md',
    word_count: 5000,
    created_at: '2026-08-05T19:40:00+08:00',
  },
  {
    task_id: 8,
    status: 'failed',
    progress: 100,
    plan_code: 'wanfang_sim',
    file_name: '结论部分.txt',
    word_count: 3000,
    created_at: '2026-08-04T18:20:00+08:00',
  },
  {
    task_id: 7,
    status: 'succeeded',
    progress: 100,
    plan_code: 'cnki_sim',
    file_name: '摘要与创新点.md',
    word_count: 4000,
    created_at: '2026-08-04T16:05:00+08:00',
  },
];

export const seedUsage: Usage = { free_quota: 3, points: 120 };

export const seedCalibration: CalibrationStatus = {
  sample_count: 12,
  model_version: null,
  mae: null,
  model_status: 'cold_start',
};

// ---------- 报告种子：由段落构建，offset 用 indexOf 计算保证与 segments 对齐 ----------
const paragraphs: string[] = [
  '摘要\n本文针对传统图像识别方法在复杂场景下泛化能力不足的问题，提出一种基于深度学习的图像识别算法。实验结果表明，该方法在公开数据集上的平均识别准确率达到 91.3%，较传统方法提升约 6 个百分点。',
  '关键词：深度学习；图像识别；卷积神经网络',
  '一、引言\n近年来，深度学习在计算机视觉领域取得了显著进展。卷积神经网络凭借其强大的特征提取能力，被广泛应用于图像分类、目标检测与语义分割等任务。本文在前人研究基础上，聚焦小样本条件下的识别精度提升问题。',
  '二、相关工作\n文献[1]提出基于残差结构的深度网络，有效缓解了深层网络的梯度消失问题。文献[2]在注意力机制方面进行了探索，增强了模型对关键区域的关注。上述工作为本研究提供了重要参考。',
  '三、研究方法\n本研究采用卷积神经网络作为主干网络，引入数据增强与迁移学习策略。训练过程中使用 Adam 优化器，初始学习率设置为 0.001，批次大小为 32。为防止过拟合，在训练时加入权重衰减与随机丢弃层。',
  '四、实验结果与分析\n在 CIFAR-10 数据集上的对比实验中，本文方法的识别准确率为 91.3%，高于基线模型的 85.2%。消融实验表明，数据增强策略贡献了约 3 个百分点的提升。同时，模型在遮挡与光照变化场景下仍保持较好的鲁棒性。',
  '五、结论\n本文提出的算法在公开数据集上取得了优于基线方法的效果，验证了深度学习在图像识别任务中的有效性。后续工作将探索更轻量化的网络结构，以适应移动端部署需求。',
];

const SEGMENT_SPECS: Array<{
  text: string;
  type: Segment['highlight_type'];
  source: string;
  similarity: number;
  detail: { title: string; author: string; venue: string; year: number; is_cited: boolean };
}> = [
  {
    text: '卷积神经网络凭借其强大的特征提取能力',
    type: 'high',
    source: '语料库',
    similarity: 94,
    detail: {
      title: '基于深度卷积神经网络的图像分类方法研究',
      author: '陈志远',
      venue: '计算机学报',
      year: 2021,
      is_cited: false,
    },
  },
  {
    text: '为防止过拟合，在训练时加入权重衰减与随机丢弃层',
    type: 'mid',
    source: '语料库',
    similarity: 78,
    detail: {
      title: '深度网络正则化策略综述',
      author: '王慧敏',
      venue: '软件学报',
      year: 2020,
      is_cited: false,
    },
  },
  {
    text: '文献[1]提出基于残差结构的深度网络',
    type: 'cite',
    source: '用户库',
    similarity: 62,
    detail: {
      title: 'Deep Residual Learning for Image Recognition',
      author: 'K. He',
      venue: 'CVPR',
      year: 2016,
      is_cited: true,
    },
  },
  {
    text: '在 CIFAR-10 数据集上的对比实验中',
    type: 'high',
    source: '语料库',
    similarity: 91,
    detail: {
      title: '小样本图像识别方法对比研究',
      author: '赵一鸣',
      venue: '自动化学报',
      year: 2022,
      is_cited: false,
    },
  },
  {
    text: '数据增强策略贡献了约 3 个百分点的提升',
    type: 'mid',
    source: '未知',
    similarity: 71,
    detail: {
      title: '数据增强在图像识别中的应用分析',
      author: '刘思远',
      venue: '模式识别与人工智能',
      year: 2021,
      is_cited: false,
    },
  },
  {
    text: '文献[2]在注意力机制方面进行了探索',
    type: 'cite',
    source: '用户库',
    similarity: 58,
    detail: {
      title: 'Attention Is All You Need',
      author: 'A. Vaswani',
      venue: 'NeurIPS',
      year: 2017,
      is_cited: true,
    },
  },
];

export const seedFullText = paragraphs.join('\n\n');

function buildSegments(): Segment[] {
  const segs: Segment[] = [];
  for (const spec of SEGMENT_SPECS) {
    const start = seedFullText.indexOf(spec.text);
    if (start === -1) continue;
    segs.push({
      start_offset: start,
      end_offset: start + spec.text.length,
      highlight_type: spec.type,
      matched_source: spec.source,
      similarity: spec.similarity,
      source_detail: spec.detail,
    });
  }
  return segs;
}

export const seedSegments = buildSegments();

export function buildReport(taskId: number, planCode: string, fileName: string): Report {
  const byPlan: Record<string, { median: number; low: number; high: number; conf: number }> = {
    cnki_sim: { median: 18.6, low: 14, high: 24, conf: 82 },
    vip_sim: { median: 15.2, low: 11, high: 20, conf: 78 },
    wanfang_sim: { median: 12.8, low: 9, high: 17, conf: 75 },
    api_placeholder: { median: 16.4, low: 12, high: 22, conf: 80 },
  };
  const v = byPlan[planCode] ?? byPlan.cnki_sim;
  return {
    task_id: taskId,
    plan_code: planCode,
    est_median: v.median,
    est_low: v.low,
    est_high: v.high,
    confidence: v.conf,
    segments: seedSegments,
    sources: [
      { source: '语料库', count: 3 },
      { source: '用户库', count: 2 },
      { source: '未知', count: 1 },
    ],
    disclaimer: '预估仅供参考，非官方检测报告',
    created_at: new Date().toISOString(),
    file_name: fileName,
    full_text: seedFullText,
    metrics: {
      removal_cite_rate: 9.2,
      removal_self_rate: 17.1,
      max_single_source_rate: 6.4,
    },
    chapters: [
      { title: '摘要', rate: 6, start: 0, end: 1 },
      { title: '引言', rate: 14, start: 1, end: 2 },
      { title: '相关工作', rate: 35, start: 2, end: 3 },
      { title: '研究方法', rate: 16, start: 3, end: 4 },
      { title: '实验与结果', rate: 24, start: 4, end: 5 },
      { title: '结论', rate: 4, start: 5, end: 6 },
    ],
  };
}
