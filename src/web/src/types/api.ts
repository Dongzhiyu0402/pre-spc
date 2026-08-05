/**
 * API 类型 —— 由 docs/plagiarism-precheck/api/openapi.yaml 生成（规格即契约）
 * 手工维护，与 openapi.yaml 保持一致；禁止手写偏差。
 *
 * 说明：部分类型带「UI 扩展」字段（full_text / metrics / chapters / source_detail），
 * 为前端报告页渲染所需（openapi 的 Report 未包含原文/指标/章节，详见 pages/02-report.md）。
 * 后端联调时这些字段为可选，缺失时前端优雅降级（显示 "—" / 隐藏区块），不造假。
 */

// ---------- 统一信封 ----------
export interface ApiEnvelope<T> {
  code: number;
  message: string;
  data: T;
}

export interface ApiErrorItem {
  loc?: string[];
  msg?: string;
  type?: string;
}

export interface ErrorResponse {
  code: number;
  message: string;
  errors?: ApiErrorItem[];
}

// ---------- 认证 ----------
export type UserRole = 'user' | 'admin';

export interface User {
  id: number;
  email: string;
  nickname: string;
  role: UserRole;
  free_quota: number;
  points: number;
  created_at?: string;
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterRequest {
  email: string;
  password: string;
  nickname: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface AuthResponseData {
  user: User;
  tokens: Tokens;
}

// ---------- 方案 ----------
export type PlanType = 'engine' | 'api';

export interface Plan {
  code: string;
  name: string;
  type: PlanType;
  price_info: Record<string, unknown>;
  enabled?: boolean;
}

// ---------- 查重任务 ----------
export type CheckStatus = 'pending' | 'processing' | 'succeeded' | 'failed';

export interface CheckTaskSummary {
  task_id: number;
  status: CheckStatus;
  progress?: number;
  plan_code?: string;
  file_name?: string;
  word_count?: number;
  created_at?: string;
}

export interface CheckResultSummary {
  est_median?: number;
  est_low?: number;
  est_high?: number;
  confidence?: number;
}

export interface CheckTaskDetail extends CheckTaskSummary {
  error?: string;
  result?: CheckResultSummary;
}

export interface ListChecksData {
  items: CheckTaskSummary[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

// ---------- 报告 ----------
export type HighlightType = 'high' | 'mid' | 'cite' | 'exclude';

export interface Segment {
  start_offset: number;
  end_offset: number;
  highlight_type: HighlightType;
  matched_source: string;
  similarity: number;
  /** UI 扩展：来源详情（篇名/作者/出处/年份/是否引用） */
  source_detail?: {
    title: string;
    author: string;
    venue: string;
    year: number;
    is_cited?: boolean;
  };
}

export interface Source {
  source: string;
  count: number;
}

export interface ChapterStat {
  title: string;
  rate: number;
  start: number;
  end: number;
}

export interface Report {
  task_id: number;
  plan_code: string;
  est_median: number;
  est_low: number;
  est_high: number;
  confidence: number;
  segments: Segment[];
  sources: Source[];
  disclaimer: string;
  created_at?: string;
  /** UI 扩展：论文文件名（页面标题用） */
  file_name?: string;
  /** UI 扩展：论文全文（高亮渲染必需；后端需在 report 返回，缺失时隐藏高亮视图） */
  full_text?: string;
  /** UI 扩展：三指标（去除引用率 / 去除本人率 / 单篇最大复制比），缺失显示 "—" */
  metrics?: {
    removal_cite_rate?: number;
    removal_self_rate?: number;
    max_single_source_rate?: number;
  };
  /** UI 扩展：章节重复率（后端可返回；缺失时前端由 full_text+segments 推导） */
  chapters?: ChapterStat[];
}

// ---------- 再次检测 ----------
export interface RecheckRequest {
  plan_code: string;
}

export interface RecheckData {
  task_id: number;
  status: CheckStatus;
}

// ---------- 校准 ----------
export type CalibrationModelStatus = 'cold_start' | 'linear' | 'gbdt';

export interface CalibrationStatus {
  sample_count: number;
  model_version: string | null;
  mae: number | null;
  model_status: CalibrationModelStatus;
}

export interface SubmitCalibrationData {
  sample_id: number;
  status: string;
}

// ---------- 用量 ----------
export interface Usage {
  free_quota: number;
  points: number;
}
