import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Button, Form, Input } from 'antd';
import AuthLayout from '../components/AuthLayout';
import { useAuth } from '../hooks/useAuth';
import type { LoginRequest } from '../types/api';
import './AuthPage.css';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string>();
  const [form] = Form.useForm<LoginRequest>();

  const onFinish = async (values: LoginRequest) => {
    setSubmitting(true);
    setFormError(undefined);
    try {
      await login(values);
      const redirect = params.get('redirect');
      navigate(redirect ? decodeURIComponent(redirect) : '/', { replace: true });
    } catch (e) {
      const msg = e instanceof Error ? e.message : '登录失败，请重试';
      // 错误就近显示：定位到邮箱字段
      form.setFields([{ name: 'email', errors: [msg] }]);
      setFormError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout title="登录" subtitle="登录后继续查看你的查重报告">
      <Form<LoginRequest> form={form} layout="vertical" onFinish={onFinish} requiredMark={false}>
        <Form.Item
          label="邮箱"
          name="email"
          rules={[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '邮箱格式不正确' },
          ]}
        >
          <Input size="large" placeholder="you@example.com" autoComplete="email" />
        </Form.Item>
        <Form.Item
          label="密码"
          name="password"
          rules={[{ required: true, message: '请输入密码' }]}
        >
          <Input.Password size="large" placeholder="请输入密码" autoComplete="current-password" />
        </Form.Item>

        {formError && <div className="auth-form__error">{formError}</div>}

        <Button type="primary" htmlType="submit" size="large" block loading={submitting}>
          登录
        </Button>
      </Form>

      <div className="auth-switch">
        没有账号？
        <Link to="/register">免费注册，领取 3 次查重</Link>
      </div>
    </AuthLayout>
  );
}
