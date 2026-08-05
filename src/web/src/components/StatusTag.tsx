import { Tag } from 'antd';
import type { CheckStatus } from '../types/api';

const STATUS_MAP: Record<CheckStatus, { color: string; text: string }> = {
  pending: { color: 'default', text: '排队中' },
  processing: { color: 'processing', text: '检测中' },
  succeeded: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
};

export default function StatusTag({ status }: { status: CheckStatus }) {
  const s = STATUS_MAP[status] ?? { color: 'default', text: status };
  return <Tag color={s.color}>{s.text}</Tag>;
}
