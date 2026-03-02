// Contract-derived types from FRONTEND_CONTRACT.md
// These types are read-only mirrors of the backend contract.

export interface User {
  id: string;
  username: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
}

export interface Session {
  session_id: string;
  user_id: string;
  issued_at: string;
  expires_at: string;
  last_activity: string;
  revoked: boolean;
}

export interface ChatMessage {
  msg_id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface Document {
  id: string;
  title: string;
  visibility: 'private' | 'public';
  categories: string[];
  source: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  text: string;
  score: number;
  modality: 'text' | 'image';
}

export interface Tool {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  user_id: string | null;
  event_type: string;
  details: Record<string, unknown>;
  request_id: string | null;
}

export interface Capabilities {
  capabilities: {
    filesystem: { enabled: boolean; allowed_paths: string[] };
    web: { enabled: boolean; interact_enabled: boolean };
    comfyui: { enabled: boolean };
    tts: { enabled: boolean };
    multimodal: { enabled: boolean };
    tools: {
      exec_python: 'blocked';
      exec_shell: 'blocked';
      web_search: 'available' | 'disabled';
      web_fetch: 'available' | 'disabled';
      web_crawl: 'available' | 'disabled';
    };
  };
}

export interface WizardStatus {
  state: 'not_started' | 'needs_setup_with_existing_data' | 'completed';
  step: number | null;
  existing_data: {
    users: number;
    documents: number;
    docs_db_exists: boolean;
    audit_db_exists: boolean;
    user_dirs: number;
  } | null;
}

export interface ApiError {
  error: {
    code:
      | 'UNAUTHORIZED'
      | 'INVALID_CREDENTIALS'
      | 'SESSION_EXPIRED'
      | 'FORBIDDEN'
      | 'ACCESS_DENIED'
      | 'NOT_FOUND'
      | 'NOT_IMPLEMENTED'
      | 'VALIDATION_ERROR'
      | 'BAD_REQUEST';
    message: string;
    details?: Record<string, unknown>;
  };
}

// Auth types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  role?: 'user' | 'admin';
}

export interface AuthResponse {
  access_token: string;
  token_type: 'bearer';
  user: User;
}

export interface LogoutResponse {
  success: true;
}

export interface SessionsResponse {
  sessions: Session[];
  total: number;
}

// Chat types
export interface ChatRequest {
  message: string;
  session_id: string | null;
  images: string[] | null;
}

export interface ChatResponse {
  msg_id: string;
  session_id: string;
  role: 'user';
  content: string;
  timestamp: string;
}

export interface StreamDelta {
  type: 'assistant_delta';
  data: { content: string };
}

export interface StreamDone {
  type: 'done';
  data: Record<string, never>;
}

export interface StreamError {
  type: 'error';
  data: { message: string };
}

// Document types
export interface DocumentIngestRequest {
  title: string;
  content: string;
  visibility: 'private' | 'public';
  categories: string[];
  source: string | null;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}

export interface DocumentSearchRequest {
  query: string;
  limit?: number;
  category: string | null;
}

export interface DocumentSearchResponse {
  results: SearchResult[];
}

// Tool types
export interface ToolListResponse {
  tools: Tool[];
}

export interface ToolRunRequest {
  tool_name: string;
  arguments: Record<string, unknown>;
}

export interface ToolRunResponse {
  success: boolean;
  output: string;
  logs: Record<string, unknown>;
  error: string | null;
}

// Attachment types
export interface Attachment {
  id: string;
  filename: string;
  content_type: string;
  size: number;
  status: 'uploaded';
  created_at: string;
}

// Wizard types
export interface WizardAdminRequest {
  username: string;
  password: string;
}

export interface WizardAdminResponse {
  user_id: string;
  username: string;
}

export interface WizardCompleteRequest {
  username: string;
  password: string;
  action: 'reuse' | 'backup' | 'abort';
}

export interface WizardCompleteResponse {
  user_id: string;
  username: string;
  action_taken: string;
  backup_path: string | null;
}

// User management types
export interface UserUpdateRequest {
  username: string | null;
  password: string | null;
  role: 'admin' | 'user' | null;
  is_active: boolean | null;
}

// Config types
export interface SystemConfig {
  version: string;
  server: { host: string; port: number };
  security: { session_rolling_ttl_hours: number; session_absolute_max_days: number };
  models: {
    main: { provider: string; url: string; model: string };
    summarizer: { provider: string; url: string; model: string };
    embedding: { provider: string; url: string; model: string };
    image_embedding: { provider: string; url: string; model: string };
    tts: { provider: string; url: string; model: string };
  };
  tools: {
    filesystem: { enabled: boolean; allowed_paths: string[] };
    web: { enabled: boolean; interact_enabled: boolean };
  };
  comfyui: {
    mode: string;
    url: string;
    limits: Record<string, unknown>;
  };
}

export interface ProfileConfig {
  username: string;
  display_name: string;
  preferences: Record<string, unknown>;
}

export interface ProfileUpdateRequest {
  display_name: string | null;
  preferences: Record<string, unknown> | null;
}

// Model types
export interface ModelListResponse {
  models: {
    main: { provider: string; url: string; model: string };
    summarizer: { provider: string; url: string; model: string };
    embedding: { provider: string; url: string; model: string };
    image_embedding: { provider: string; url: string; model: string };
    tts: { provider: string; url: string; model: string };
  };
}

export interface ModelTestRequest {
  url: string;
  model: string;
  api_key: string | null;
}

export interface ModelTestResponse {
  success: boolean;
  message: string;
  latency_ms: number;
}

export interface ModelUpdateRequest {
  provider: 'openai-compatible' | 'llama-server' | 'ollama';
  url: string;
  model: string;
  api_key: string | null;
}

// ComfyUI types
export interface ComfyUIRunRequest {
  workflow: Record<string, unknown>;
  input: Record<string, unknown>;
}

export interface ComfyUIRunResponse {
  job_id: string;
  status: 'queued';
}

export interface ComfyUIStatusResponse {
  job_id: string;
  status: 'queued' | 'running' | 'completed' | 'unknown';
  progress: number | null;
  output: Record<string, unknown> | null;
}

// Audit types
export interface AuditListResponse {
  events: AuditEvent[];
  total: number;
}

// Health
export interface HealthResponse {
  status: 'healthy';
  version: string;
}
