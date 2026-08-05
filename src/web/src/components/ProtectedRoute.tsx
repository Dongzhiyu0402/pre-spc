import { Navigate, useLocation } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuth } from '../hooks/useAuth';

/** 登录守卫：未登录跳 /login?redirect=当前路径，登录后回跳 */
export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { authed, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '96px 0' }}>
        <Spin tip="正在恢复登录状态…">
          <div style={{ width: 120, height: 40 }} />
        </Spin>
      </div>
    );
  }
  if (!authed) {
    const redirect = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?redirect=${redirect}`} replace />;
  }
  return <>{children}</>;
}
