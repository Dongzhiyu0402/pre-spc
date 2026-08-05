import { apiRequest } from './client';
import type { Usage } from '../types/api';

export async function getMyUsage(): Promise<Usage> {
  return apiRequest<Usage>('GET', '/users/me/usage');
}
