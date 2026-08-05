import { apiRequest } from './client';
import type {
  AuthResponseData,
  LoginRequest,
  RegisterRequest,
  Tokens,
  User,
} from '../types/api';

export async function register(body: RegisterRequest): Promise<AuthResponseData> {
  return apiRequest<AuthResponseData>('POST', '/auth/register', { body });
}

export async function login(body: LoginRequest): Promise<AuthResponseData> {
  return apiRequest<AuthResponseData>('POST', '/auth/login', { body });
}

export async function refreshToken(refresh_token: string): Promise<Tokens> {
  return apiRequest<Tokens>('POST', '/auth/refresh', { body: { refresh_token } });
}

export async function getMe(): Promise<User> {
  return apiRequest<User>('GET', '/auth/me');
}
