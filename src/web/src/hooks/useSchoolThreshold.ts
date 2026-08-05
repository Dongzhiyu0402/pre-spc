import { useCallback, useState } from 'react';

const THRESHOLD_KEY = 'pre_spc_school_threshold';
const DEFAULT_THRESHOLD = 20;

/**
 * 学校阈值配置（5-50%，默认 20%）。
 * 用量页可改，报告页读取同一 localStorage key，实现 AC-07 联动。
 */
export function useSchoolThreshold() {
  const [threshold, setThresholdState] = useState<number>(() => {
    const raw = localStorage.getItem(THRESHOLD_KEY);
    const n = raw === null ? NaN : Number(raw);
    return Number.isNaN(n) ? DEFAULT_THRESHOLD : Math.min(50, Math.max(5, n));
  });

  const setThreshold = useCallback((value: number) => {
    const clamped = Math.min(50, Math.max(5, Math.round(value)));
    localStorage.setItem(THRESHOLD_KEY, String(clamped));
    setThresholdState(clamped);
  }, []);

  return { threshold, setThreshold, defaultThreshold: DEFAULT_THRESHOLD };
}
