import { useCallback, useEffect, useRef, useState } from 'react';
import { getCheck } from '../api/checks';
import type { CheckStatus } from '../types/api';

interface PollState {
  status: CheckStatus;
  progress: number;
  error?: string;
}

/**
 * 查重任务轮询：每 1.2s 拉取一次，直至 succeeded/failed（最多 90s）。
 * onDone 在终态回调（成功返回 task 摘要）。
 */
export function useCheckPolling(taskId: number | string | null) {
  const [state, setState] = useState<PollState>({ status: 'pending', progress: 0 });
  const [done, setDone] = useState(false);
  const onDoneRef = useRef<((ok: boolean) => void) | null>(null);
  const attemptsRef = useRef(0);

  useEffect(() => {
    if (taskId === null) return;
    const tid = taskId;
    let alive = true;
    attemptsRef.current = 0;

    async function tick() {
      if (!alive) return;
      try {
        const detail = await getCheck(tid);
        if (!alive) return;
        setState({ status: detail.status, progress: detail.progress ?? 0, error: detail.error });
        if (detail.status === 'succeeded' || detail.status === 'failed') {
          setDone(true);
          onDoneRef.current?.(detail.status === 'succeeded');
          return;
        }
      } catch {
        // 单次失败不中断，继续轮询直到超时
      }
      attemptsRef.current += 1;
      if (attemptsRef.current > 75) {
        if (alive) {
          setState((s) => ({ ...s, status: 'failed', error: '查询超时，请稍后重试' }));
          setDone(true);
          onDoneRef.current?.(false);
        }
        return;
      }
      window.setTimeout(tick, 1200);
    }

    void tick();
    return () => {
      alive = false;
    };
  }, [taskId]);

  const onDone = useCallback((cb: (ok: boolean) => void) => {
    onDoneRef.current = cb;
  }, []);

  return { ...state, done, onDone };
}
