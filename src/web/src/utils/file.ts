/** 文件校验（AC-03：超限/空文件 → 明确错误，不消耗次数） */

export const ALLOWED_EXTENSIONS = ['docx', 'txt', 'md', 'pdf'];
export const MAX_SIZE_MB = 50;
export const MAX_WORDS = 100000;

export interface FileValidation {
  ok: boolean;
  error?: string;
  wordCount?: number;
}

export function extensionOf(name: string): string {
  const i = name.lastIndexOf('.');
  return i === -1 ? '' : name.slice(i + 1).toLowerCase();
}

export async function validateFile(file: File): Promise<FileValidation> {
  const ext = extensionOf(file.name);
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return { ok: false, error: `暂不支持 ${ext || '该'} 格式，请上传 docx / txt / md / pdf` };
  }
  if (file.size === 0) {
    return { ok: false, error: '文件为空，请重新选择' };
  }
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    return { ok: false, error: `文件超过 ${MAX_SIZE_MB}MB 上限，请压缩后重试` };
  }

  let wordCount: number | undefined;
  if (ext === 'txt' || ext === 'md') {
    try {
      const text = await file.text();
      wordCount = text.replace(/\s/g, '').length;
      if (wordCount > MAX_WORDS) {
        return { ok: false, error: `超过 10 万字上限（当前约 ${wordCount.toLocaleString()} 字）` };
      }
    } catch {
      wordCount = undefined;
    }
  } else {
    // docx/pdf 客户端无法可靠读字数，交由后端精确统计；估算仅作展示
    wordCount = Math.round(file.size / 4);
  }

  return { ok: true, wordCount };
}
