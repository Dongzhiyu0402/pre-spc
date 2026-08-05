import { useCallback, useRef, useState } from 'react';
import { FileText, UploadCloud, X } from 'lucide-react';
import { formatFileSize, formatWordCount } from '../utils/format';
import { validateFile, type FileValidation } from '../utils/file';
import './UploadDropzone.css';

export interface DropzoneFile {
  file: File;
  wordCount?: number;
}

interface Props {
  file: DropzoneFile | null;
  error?: string;
  disabled?: boolean;
  onSelect: (item: DropzoneFile | null, validation: FileValidation) => void;
  onDisabledClick?: () => void;
}

/**
 * 拖拽上传区（核心交互）
 * 状态：default / hover·拖入 / 已选文件 / 校验失败 / 上传中(由父级展示进度) / disabled(AC-04 跳转)
 */
export default function UploadDropzone({ file, error, disabled, onSelect, onDisabledClick }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleFile = useCallback(
    async (f: File) => {
      const v = await validateFile(f);
      if (v.ok) {
        onSelect({ file: f, wordCount: v.wordCount }, v);
      } else {
        onSelect(null, v);
      }
    },
    [onSelect],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      if (disabled) {
        onDisabledClick?.();
        return;
      }
      const f = e.dataTransfer.files?.[0];
      if (f) void handleFile(f);
    },
    [disabled, handleFile, onDisabledClick],
  );

  const onPick = useCallback(() => {
    if (disabled) {
      onDisabledClick?.();
      return;
    }
    inputRef.current?.click();
  }, [disabled, onDisabledClick]);

  const inputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0];
      if (f) void handleFile(f);
      e.target.value = '';
    },
    [handleFile],
  );

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept=".docx,.txt,.md,.pdf"
        className="dropzone__input"
        onChange={inputChange}
        aria-label="选择论文文件"
      />

      {file ? (
        <div className="dropzone dropzone--selected">
          <div className="dropzone__file-row">
            <FileText size={20} className="dropzone__file-icon" aria-hidden="true" />
            <div className="dropzone__file-meta">
              <div className="dropzone__file-name font-mono ellipsis" title={file.file.name}>
                {file.file.name}
              </div>
              <div className="dropzone__file-sub">
                {formatFileSize(file.file.size)}
                {file.wordCount !== undefined && <> · {formatWordCount(file.wordCount)}</>}
              </div>
            </div>
            <button
              type="button"
              className="dropzone__remove"
              aria-label="移除文件"
              onClick={() => onSelect(null, { ok: true })}
            >
              <X size={18} aria-hidden="true" />
            </button>
          </div>
          {error && <div className="dropzone__error">{error}</div>}
        </div>
      ) : (
        <button
          type="button"
          className={`dropzone ${dragging ? 'dropzone--dragging' : ''} ${disabled ? 'dropzone--disabled' : ''} ${error ? 'dropzone--error' : ''}`}
          onClick={onPick}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <UploadCloud size={24} className="dropzone__icon" aria-hidden="true" />
          <span className="dropzone__main">
            {disabled ? '免费次数已用完，点击前往用量页' : dragging ? '松开以选择' : '拖拽论文到此处，或点击选择'}
          </span>
          <span className="dropzone__hint">支持 docx / txt / md / pdf · 单文件 ≤50MB · ≤10 万字</span>
          {error && <span className="dropzone__error">{error}</span>}
        </button>
      )}
    </div>
  );
}
