/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Mock 模式开关：未显式设为 'false' 时启用本地 mock；后端联调后设为 false */
  readonly VITE_USE_MOCK?: string;
  /** 后端 API base URL（默认 /api/v1） */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
