import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Button, Form, Input, message } from 'antd';
import AuthLayout from '../components/AuthLayout';
import { useAuth } from '../hooks/useAuth';
import type { RegisterRequest } from '../types/api';
import './AuthPage.css';

interface RegisterForm extends RegisterRequest {
  confirm: string;
}

function strengthOf(pwd: string): { score: number; label: string; cls: string } {
  let score = 0;
  if (pwd.length >= 8) score += 1;
  if (pwd.length >= 12) score += 1;
  if (/[A-Za-z]/.test(pwd) && /\d/.test(pwd)) score += 1;
  if (/[^A-Za-z0-9]/.test(pwd)) score += 1;
  if (score <= 1) return { score, label: '弱', cls: 'auth-strength--weak' };
  if (score <= 3) return { score, label: '中', cls: 'auth-strength--mid' };
  return { score, label: '强', cls: 'auth-strength--strong' };
}

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string>();
  const [form] = Form.useForm<RegisterForm>();
  const pwd = Form.useWatch('password', form) ?? '';
  const strength = strengthOf(pwd);

  const onFinish = async (values: RegisterForm) => {
    setSubmitting(true);
    setFormError(undefined);
    try {
      await register({ email: values.email, password: values.password, nickname: values.nickname });
      message.success('注册成功，已赠送 3 次免费查重'); // AC-12
      const redirect = params.get('redirect');
      navigate(redirect ? decodeURIComponent(redirect) : '/', { replace: true });
    } catch (e) {
      const msg = e instanceof Error ? e.message : '注册失败，请重试';
      if (msg.includes('邮箱')) {
        form.setFields([{ name: 'email', errors: [msg] }]);
      }
      setFormError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout title="创建账号" subtitle="注册即送 3 次免费查重，送检前先预估">
      <Form<RegisterForm> form={form} layout="vertical" onFinish={onFinish} requiredMark={false}>
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
          label="昵称"
          name="nickname"
          rules={[
            { required: true, message: '请输入昵称' },
            { max: 30, message: '昵称不超过 30 字' },
          ]}
        >
          <Input size="large" placeholder="怎么称呼你" autoComplete="nickname" />
        </Form.Item>
        <Form.Item
          label="密码"
          name="password"
          rules={[
            { required: true, message: '请输入密码' },
            { min: 8, message: '密码至少 8 位' },
          ]}
          extra={null}
        >
          <Input.Password size="large" placeholder="至少 8 位，建议含字母和数字" autoComplete="new-password" />
        </Form.Item>

        {pwd.length > 0 && (
          <div className="auth-strength" aria-label={`密码强度：${strength.label}`}>
            <div className="auth-strength__bars">
              {[1, 2, 3, 4].map((i) => (
                <span
                  key={i}
                  className={`auth-strength__bar ${i <= strength.score ? strength.cls : ''}`}
                />
              ))}
            </div>
            <span className={`auth-strength__label ${strength.cls}`}>密码强度 {strength.label}</span>
          </div>
        )}

        <Form.Item
          label="确认密码"
          name="confirm"
          dependencies={['password']}
          rules={[
            { required: true, message: '请再次输入密码' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) return Promise.resolve();
                return Promise.reject(new Error('两次输入的密码不一致'));
              },
            }),
          ]}
        >
          <Input.Password size="large" placeholder="再次输入密码" autoComplete="new-password" />
        </Form.Item>

        {formError && <div className="auth-form__error">{formError}</div>}

        <Button type="primary" htmlType="submit" size="large" block loading={submitting}>
          注册并领取免费查重次数
        </Button>
      </Form>

      <div className="auth-switch">
        已有账号？
        <Link to="/login">直接登录</Link>
      </div>
    </AuthLayout>
  );
}
