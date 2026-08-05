import type { Report } from '../types/api';

/**
 * 客户端导出 HTML（AC-09：导出含免责声明常驻）
 * Mock 模式下后端无文件流，前端生成含完整报告 + 免责声明页脚的 HTML 下载。
 * 真实联调后由 GET /checks/{id}/export 返回 PDF/HTML 文件流。
 *
 * 注：此函数生成「独立导出的 HTML 文档」（用户下载后自包含展示），
 * 无法引用应用内 CSS 变量，因此内联样式使用与 design-tokens 一致的常量值；
 * 该常量值仅用于导出文档，不属于应用 UI 的硬编码。
 */
export function generateExportHtml(report: Report, threshold?: number): string {
  const { est_median, est_low, est_high, confidence, segments, full_text, disclaimer } = report;

  const hlColor: Record<string, string> = {
    high: 'rgba(220,38,38,0.13)',
    mid: 'rgba(234,88,12,0.12)',
    cite: 'rgba(180,83,9,0.16)',
    exclude: 'rgba(107,114,128,0.10)',
  };

  let body = full_text ?? '';
  if (full_text && segments.length > 0) {
    const sorted = [...segments].sort((a, b) => a.start_offset - b.start_offset);
    let html = '';
    let cursor = 0;
    for (const seg of sorted) {
      const s = Math.max(0, Math.min(full_text.length, seg.start_offset));
      const e = Math.max(s, Math.min(full_text.length, seg.end_offset));
      if (e <= cursor) continue;
      html += escapeHtml(full_text.slice(cursor, s));
      html += `<mark style="background:${hlColor[seg.highlight_type] ?? 'transparent'};border-radius:2px;padding:0 2px;">${escapeHtml(full_text.slice(s, e))}</mark>`;
      cursor = e;
    }
    html += escapeHtml(full_text.slice(cursor));
    body = html;
  } else {
    body = escapeHtml(full_text ?? '（全文暂不可用）');
  }

  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<title>预查重报告 · 任务 ${report.task_id}</title>
<style>
  body{font-family:"Inter","Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;color:#1F2937;max-width:760px;margin:32px auto;padding:0 20px;line-height:1.8;}
  h1{font-size:20px;} .muted{color:#6B7280;font-size:14px;}
  .median{font-family:"JetBrains Mono",monospace;font-size:40px;font-weight:600;color:#0D9488;}
  .range{font-family:"JetBrains Mono",monospace;color:#4B5563;}
  table{border-collapse:collapse;margin:16px 0;width:100%;font-size:14px;}
  th,td{border:1px solid #E5E7EB;padding:8px 12px;text-align:left;}
  th{background:#F1F2F4;color:#4B5563;}
  .disclaimer{margin-top:40px;padding-top:12px;border-top:1px solid #E5E7EB;color:#6B7280;font-size:13px;}
  .guidance{margin:12px 0;padding:10px 14px;background:#F0FDFA;color:#0D9488;border-radius:8px;font-size:14px;}
</style>
</head>
<body>
  <h1>查重报告 · 预估仅供参考</h1>
  <p class="muted">任务 #${report.task_id} · 方案 ${report.plan_code}</p>
  <div class="median">${est_median.toFixed(1)}%</div>
  <div class="range">预估区间 ${est_low.toFixed(0)}% – ${est_high.toFixed(0)}% · 置信度 ${confidence.toFixed(0)}%</div>
  ${threshold !== undefined && report.est_high > threshold ? `<div class="guidance">你的预估区间跨过学校阈值 ${threshold}%，建议优先修改高亮片段。</div>` : ''}
  <h2>全文相似片段</h2>
  <div>${body}</div>
  <h2>来源分布</h2>
  <table><thead><tr><th>来源</th><th>命中片段</th></tr></thead><tbody>
    ${report.sources.map((s) => `<tr><td>${escapeHtml(s.source)}</td><td>${s.count}</td></tr>`).join('')}
  </tbody></table>
  <div class="disclaimer">${escapeHtml(disclaimer || '预估仅供参考，非官方检测报告')} · 本报告由预查重工具生成</div>
</body>
</html>`;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export function downloadTextFile(filename: string, content: string, mime = 'text/html'): void {
  const blob = new Blob([content], { type: `${mime};charset=utf-8` });
  saveBlob(blob, filename);
}

export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
