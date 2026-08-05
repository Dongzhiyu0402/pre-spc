import { apiDownload, apiRequest } from './client';
import type {
  CheckTaskDetail,
  CheckTaskSummary,
  ListChecksData,
  RecheckData,
  RecheckRequest,
  Report,
} from '../types/api';

export async function createCheck(file: File, planCode: string): Promise<CheckTaskSummary> {
  const form = new FormData();
  form.append('file', file);
  form.append('plan_code', planCode);
  return apiRequest<CheckTaskSummary>('POST', '/checks', { body: form, isForm: true });
}

export async function getCheck(taskId: number | string): Promise<CheckTaskDetail> {
  return apiRequest<CheckTaskDetail>('GET', `/checks/${taskId}`);
}

export async function getReport(taskId: number | string): Promise<Report> {
  return apiRequest<Report>('GET', `/checks/${taskId}/report`);
}

export async function listChecks(page = 1, limit = 20): Promise<ListChecksData> {
  return apiRequest<ListChecksData>('GET', '/checks', { params: { page, limit } });
}

export async function recheck(taskId: number | string, body: RecheckRequest): Promise<RecheckData> {
  return apiRequest<RecheckData>('POST', `/checks/${taskId}/recheck`, { body });
}

export async function exportReport(taskId: number | string, format: 'pdf' | 'html'): Promise<Blob | null> {
  return apiDownload(`/checks/${taskId}/export`, format);
}
