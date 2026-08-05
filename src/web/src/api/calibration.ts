import { apiRequest } from './client';
import type { CalibrationStatus, SubmitCalibrationData } from '../types/api';

export async function getCalibrationStatus(): Promise<CalibrationStatus> {
  return apiRequest<CalibrationStatus>('GET', '/calibration/status');
}

export async function submitCalibrationReport(params: {
  file: File;
  platform: string;
  real_rate: number;
  task_id: number;
}): Promise<SubmitCalibrationData> {
  const form = new FormData();
  form.append('file', params.file);
  form.append('platform', params.platform);
  form.append('real_rate', String(params.real_rate));
  form.append('task_id', String(params.task_id));
  return apiRequest<SubmitCalibrationData>('POST', '/calibration/reports', {
    body: form,
    isForm: true,
  });
}
