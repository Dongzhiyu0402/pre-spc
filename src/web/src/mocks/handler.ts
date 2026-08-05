import type { RequestOptions } from '../api/client';
import type {
  AuthResponseData,
  CalibrationStatus,
  CheckTaskDetail,
  CheckTaskSummary,
  ListChecksData,
  RecheckData,
  Report,
  SubmitCalibrationData,
  Usage,
  User,
} from '../types/api';
import {
  buildReport,
  seedCalibration,
  seedChecks,
  seedPlans,
  seedSegments,
  seedUsage,
  seedUser,
} from './seed';

/**
 * Mock 请求处理器（后端联调后移除）
 * 模拟异步查重：创建任务 → 2.6s 后 succeeded → 报告可用。
 */

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

interface MockTask extends CheckTaskSummary {
  report?: Report;
  error?: string;
}

const tasks = new Map<number, MockTask>();
for (const c of seedChecks) {
  tasks.set(c.task_id, { ...c });
}
let nextTaskId = 100;
let nextSampleId = 50;

function tokenFor(user: User): AuthResponseData['tokens'] {
  return {
    access_token: `mock_access_${user.id}`,
    refresh_token: `mock_refresh_${user.id}`,
    token_type: 'bearer',
    expires_in: 900,
  };
}

function authData(user: User): AuthResponseData {
  return { user, tokens: tokenFor(user) };
}

function planName(code: string): string {
  return seedPlans.find((p) => p.code === code)?.name ?? '未知方案';
}

async function readWordCount(file: File): Promise<number> {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
  if (ext === 'txt' || ext === 'md') {
    const text = await file.text();
    return text.replace(/\s/g, '').length;
  }
  return Math.round(file.size / 4); // docx/pdf 估算（后端为准）
}

function createMockTask(file: File, planCode: string): MockTask {
  const taskId = nextTaskId++;
  const task: MockTask = {
    task_id: taskId,
    status: 'pending',
    progress: 5,
    plan_code: planCode,
    file_name: file.name,
    created_at: new Date().toISOString(),
  };
  tasks.set(taskId, task);

  // 模拟异步引擎：processing(1.4s) → succeeded(2.6s)
  setTimeout(() => {
    task.status = 'processing';
    task.progress = 62;
  }, 1400);
  setTimeout(async () => {
    task.status = 'succeeded';
    task.progress = 100;
    const words = await readWordCount(file);
    task.word_count = words;
    task.report = buildReport(taskId, planCode, file.name);
  }, 2600);
  return task;
}

export async function handleMock<T>(method: string, path: string, options: RequestOptions): Promise<T> {
  await delay(180 + Math.random() * 220);
  const { params, body } = options;

  // ---- auth ----
  if (method === 'POST' && path === '/auth/register') {
    const b = body as { email: string; password: string; nickname: string };
    if (b.email === seedUser.email) {
      throw Object.assign(new Error('邮箱已注册，请直接登录'), { status: 409, code: 409 });
    }
    const user: User = {
      id: nextTaskId++,
      email: b.email,
      nickname: b.nickname,
      role: 'user',
      free_quota: 3, // AC-12 注册赠送
      points: 0,
      created_at: new Date().toISOString(),
    };
    return authData(user) as unknown as T;
  }

  if (method === 'POST' && path === '/auth/login') {
    const b = body as { email: string; password: string };
    if (b.email !== seedUser.email || b.password.length < 8) {
      throw Object.assign(new Error('邮箱或密码不正确'), { status: 401, code: 401 });
    }
    return authData(seedUser) as unknown as T;
  }

  if (method === 'GET' && path === '/auth/me') {
    return seedUser as unknown as T;
  }

  // ---- plans ----
  if (method === 'GET' && path === '/plans') {
    return seedPlans.filter((p) => p.enabled !== false) as unknown as T;
  }

  // ---- checks ----
  if (method === 'POST' && path === '/checks') {
    const form = body as FormData;
    const file = form.get('file') as File;
    const planCode = String(form.get('plan_code') ?? 'cnki_sim');
    if (!file || file.size === 0) {
      throw Object.assign(new Error('文件为空，请重新选择'), { status: 400, code: 400 });
    }
    const task = createMockTask(file, planCode);
    return { task_id: task.task_id, status: task.status, progress: task.progress } as unknown as T;
  }

  if (method === 'GET' && path === '/checks') {
    const page = Number(params?.page ?? 1);
    const limit = Number(params?.limit ?? 20);
    const all = [...tasks.values()].sort((a, b) => b.task_id - a.task_id);
    const items = all.slice((page - 1) * limit, page * limit);
    const data: ListChecksData = {
      items,
      total: all.length,
      page,
      limit,
      hasMore: page * limit < all.length,
    };
    return data as unknown as T;
  }

  const reportMatch = path.match(/^\/checks\/(\d+)\/report$/);
  if (method === 'GET' && reportMatch) {
    const task = tasks.get(Number(reportMatch[1]));
    if (!task) throw Object.assign(new Error('报告不存在或已删除'), { status: 404, code: 404 });
    if (task.status !== 'succeeded' || !task.report) {
      throw Object.assign(new Error('任务尚未完成，报告暂不可用'), { status: 409, code: 409 });
    }
    return task.report as unknown as T;
  }

  const checkMatch = path.match(/^\/checks\/(\d+)$/);
  if (method === 'GET' && checkMatch) {
    const task = tasks.get(Number(checkMatch[1]));
    if (!task) throw Object.assign(new Error('任务不存在'), { status: 404, code: 404 });
    const detail: CheckTaskDetail = {
      task_id: task.task_id,
      status: task.status,
      progress: task.progress,
      plan_code: task.plan_code,
      file_name: task.file_name,
      word_count: task.word_count,
      created_at: task.created_at,
      error: task.error,
      result:
        task.status === 'succeeded' && task.report
          ? {
              est_median: task.report.est_median,
              est_low: task.report.est_low,
              est_high: task.report.est_high,
              confidence: task.report.confidence,
            }
          : undefined,
    };
    return detail as unknown as T;
  }

  const recheckMatch = path.match(/^\/checks\/(\d+)\/recheck$/);
  if (method === 'POST' && recheckMatch) {
    const original = tasks.get(Number(recheckMatch[1]));
    const planCode = (body as { plan_code?: string }).plan_code ?? original?.plan_code ?? 'cnki_sim';
    const fileName = original?.file_name ?? '未命名文档';
    const fakeFile = new File([''], fileName, { type: 'text/plain' });
    const task = createMockTask(fakeFile, planCode);
    const data: RecheckData = { task_id: task.task_id, status: task.status };
    return data as unknown as T;
  }

  // ---- calibration ----
  if (method === 'GET' && path === '/calibration/status') {
    const status: CalibrationStatus = { ...seedCalibration };
    return status as unknown as T;
  }

  if (method === 'POST' && path === '/calibration/reports') {
    const form = body as FormData;
    const realRate = Number(form.get('real_rate'));
    if (Number.isNaN(realRate) || realRate < 0 || realRate > 100) {
      throw Object.assign(new Error('真实查重率需为 0-100 的数字'), { status: 400, code: 400 });
    }
    const data: SubmitCalibrationData = { sample_id: nextSampleId++, status: 'pending_validation' };
    return data as unknown as T;
  }

  // ---- usage ----
  if (method === 'GET' && path === '/users/me/usage') {
    const usage: Usage = { ...seedUsage };
    return usage as unknown as T;
  }

  throw Object.assign(new Error(`Mock 未实现：${method} ${path}`), { status: 404, code: 404 });
}

export function mockPreviewSegments(): Report['segments'] {
  return seedSegments;
}

export function mockPlanName(code: string): string {
  return planName(code);
}
