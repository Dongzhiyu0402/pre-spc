import { Link, useNavigate } from 'react-router-dom';
import { Button } from 'antd';
import { Gauge, History, LogOut, Wallet } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import './AppNav.css';

/** 顶部极简导航：Logo(文字标) | 历史 | 用量 | 登录/退出 */
export default function AppNav() {
  const { authed, user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="app-nav">
      <div className="container app-nav__inner">
        <Link to="/" className="app-nav__logo">
          <Gauge size={20} strokeWidth={2} aria-hidden="true" />
          <span className="app-nav__brand">预查重</span>
        </Link>

        <nav className="app-nav__links" aria-label="主导航">
          <Link to="/" className="app-nav__link">
            <span className="app-nav__link-label">首页</span>
          </Link>
          <Link to="/history" className="app-nav__link">
            <History size={16} aria-hidden="true" />
            <span className="app-nav__link-label">历史记录</span>
          </Link>
          <Link to="/usage" className="app-nav__link">
            <Wallet size={16} aria-hidden="true" />
            <span className="app-nav__link-label">用量与账户</span>
          </Link>
        </nav>

        <div className="app-nav__auth">
          {authed && user ? (
            <div className="app-nav__user">
              <Link to="/usage" className="app-nav__user-name">
                {user.nickname}
              </Link>
              <Button
                type="text"
                size="small"
                icon={<LogOut size={16} aria-hidden="true" />}
                onClick={() => {
                  logout();
                  navigate('/');
                }}
              >
                退出
              </Button>
            </div>
          ) : (
            <div className="app-nav__auth-btns">
              <Link to="/login">
                <Button type="text">登录</Button>
              </Link>
              <Link to="/register">
                <Button type="primary" size="middle">
                  免费注册
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
