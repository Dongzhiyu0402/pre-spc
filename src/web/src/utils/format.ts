/** 格式化工具（展示层） */

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDateTime(iso?: string): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  const hh = String(d.getHours()).padStart(2, '0');
  const mi = String(d.getMinutes()).padStart(2, '0');
  return `${mm}-${dd} ${hh}:${mi}`;
}

export function formatWordCount(n?: number): string {
  if (n === undefined || n === null) return '—';
  if (n >= 10000) {
    const w = (n / 10000).toFixed(1);
    return `${w.replace(/\.0$/, '')} 万字`;
  }
  return `${n} 字`;
}

export function formatRate(n?: number): string {
  if (n === undefined || n === null || Number.isNaN(n)) return '—';
  return `${Math.round(n * 10) / 10}%`;
}

export function planNameOf(plans: Array<{ code: string; name: string }>, code?: string): string {
  if (!code) return '—';
  return plans.find((p) => p.code === code)?.name ?? code;
}

/** 根据重复率取等级 key（章节条/进度条着色） */
export function rateLevel(rate: number): 'low' | 'ok' | 'mid' | 'high' {
  if (rate <= 10) return 'low';
  if (rate <= 20) return 'ok';
  if (rate <= 30) return 'mid';
  return 'high';
}
