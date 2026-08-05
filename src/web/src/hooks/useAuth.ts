import { useCallback, useEffect, useState } from 'react';
import * as authApi from '../api/auth';
import { clearTokens, getAccessToken, setTokens } from '../api/client';
import type { LoginRequest, RegisterRequest, User } from '../types/api';

interface AuthState {
  user: User | null;
  /** 初始加载中（尝试用本地 token 拉取 /me） */
  loading: boolean;
}

/**
 * 认证状态 hook：本地 token → /auth/me 恢复会话；login/register/logout 统一出口。
 */
export function useAuth() {
  const [state, setState] = useState<AuthState>({ user: null, loading: true });

  useEffect(() => {
    let alive = true;
    async function restore() {
      if (!getAccessToken()) {
        if (alive) setState({ user: null, loading: false });
        return;
      }
      try {
        const user = await authApi.getMe();
        if (alive) setState({ user, loading: false });
      } catch {
        clearTokens();
        if (alive) setState({ user: null, loading: false });
      }
    }
    void restore();
    return () => {
      alive = false;
    };
  }, []);

  const login = useCallback(async (body: LoginRequest) => {
    const data = await authApi.login(body);
    setTokens(data.tokens.access_token, data.tokens.refresh_token);
    setState({ user: data.user, loading: false });
    return data.user;
  }, []);

  const register = useCallback(async (body: RegisterRequest) => {
    const data = await authApi.register(body);
    setTokens(data.tokens.access_token, data.tokens.refresh_token);
    setState({ user: data.user, loading: false });
    return data.user;
  }, []);

  const logout = useCallback(() => {
    clearTokens();
    setState({ user: null, loading: false });
  }, []);

  return {
    user: state.user,
    loading: state.loading,
    authed: state.user !== null,
    login,
    register,
    logout,
  };
}

export type UseAuthReturn = ReturnType<typeof useAuth>;
