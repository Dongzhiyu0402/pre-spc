import { handleMock } from '../mocks/handler';

/**
 * API 客户端 —— 唯一请求出口（openapi.yaml 契约）
 * - baseURL: VITE_API_BASE_URL || '/api/v1'（Vite dev 已配 /api 代理到 localhost:8000）
 * - JWT 注入 + 401 自动刷新重试一次
 * - 统一信封 {code,data,message} 解析：code!==0 抛 ApiError
 * - Mock 模式：VITE_USE_MOCK 未显式设为 'false' 时启用（后端联调后设为 false）
 */

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api/v1';

export const USE_MOCK = (import.meta.env.VITE_USE_MOCK as string | undefined) !== 'false';

const ACCESS_KEY = 'pre_spc_access';
const REFRESH_KEY = 'pre_spc_refresh';

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}
export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}
export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem('pre_spc_user');
}

export class ApiError extends Error {
  status: number;
  code: number;
  constructor(status: number, code: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export interface RequestOptions {
  params?: Record<string, string | number | undefined>;
  body?: unknown;
  /** body 为 FormData（multipart 上传） */
  isForm?: boolean;
}

async function parseEnvelope<T>(res: Response): Promise<T> {
  let payload: unknown = null;
  try {
    payload = await res.json();
  } catch {
    payload = null;
  }
  if (!res.ok) {
    const err = payload as { code?: number; message?: string; errors?: unknown } | null;
    throw new ApiError(res.status, err?.code ?? res.status, err?.message ?? `请求失败（${res.status}）`);
  }
  const env = payload as { code?: number; message?: string; data: T } | null;
  if (env && typeof env.code === 'number' && env.code !== 0) {
    throw new ApiError(res.status, env.code, env.message ?? '业务错误');
  }
  return env ? env.data : (payload as T);
}

async function realRequest<T>(method: string, path: string, options: RequestOptions): Promise<T> {
  const headers: Record<string, string> = {};
  const token = getAccessToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const query = options.params
    ? '?' +
      Object.entries(options.params)
        .filter(([, v]) => v !== undefined && v !== '')
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
        .join('&')
    : '';

  let body: BodyInit | undefined;
  if (options.isForm) {
    body = options.body as FormData;
  } else if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(options.body);
  }

  const fetchOptions: RequestInit = { method, headers, body };
  const res = await fetch(`${BASE_URL}${path}${query}`, fetchOptions);

  if (res.status === 401 && getRefreshToken()) {
    // 刷新一次并重试
    const refreshed = await tryRefresh();
    if (refreshed) return realRequest<T>(method, path, options);
  }
  return parseEnvelope<T>(res);
}

async function tryRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    const env = await res.json();
    if (res.ok && env.code === 0) {
      setTokens(env.data.access_token, env.data.refresh_token);
      return true;
    }
    clearTokens();
    return false;
  } catch {
    return false;
  }
}

/** 统一请求入口：mock 模式分发到本地 handler，否则走真实 HTTP */
export async function apiRequest<T>(method: string, path: string, options: RequestOptions = {}): Promise<T> {
  if (USE_MOCK) {
    return handleMock<T>(method, path, options);
  }
  return realRequest<T>(method, path, options);
}

/** 导出类请求（文件流）：mock 模式下返回 null，由调用方本地生成；真实模式返回 Blob */
export async function apiDownload(path: string, format: 'pdf' | 'html'): Promise<Blob | null> {
  if (USE_MOCK) return null;
  const token = getAccessToken();
  const headers: Record<string, string> = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${BASE_URL}${path}?format=${format}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new ApiError(res.status, err?.code ?? res.status, err?.message ?? '导出失败');
  }
  return res.blob();
}
