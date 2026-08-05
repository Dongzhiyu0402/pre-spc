import { Gauge } from 'lucide-react';
import { Link } from 'react-router-dom';
import './AuthLayout.css';

interface Props {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}

/** 登录/注册居中卡片布局（极简、中性） */
export default function AuthLayout({ title, subtitle, children }: Props) {
  return (
    <div className="auth-layout">
      <div className="auth-card">
        <Link to="/" className="auth-card__logo">
          <Gauge size={24} aria-hidden="true" />
          <span>预查重</span>
        </Link>
        <h1 className="auth-card__title">{title}</h1>
        {subtitle && <p className="auth-card__sub">{subtitle}</p>}
        {children}
        <div className="auth-card__privacy text-muted text-sm">你的论文与账号信息受保护</div>
      </div>
    </div>
  );
}
