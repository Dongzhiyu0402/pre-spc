import { apiRequest } from './client';
import type { Plan } from '../types/api';

export async function listPlans(): Promise<Plan[]> {
  return apiRequest<Plan[]>('GET', '/plans');
}
