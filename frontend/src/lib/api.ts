import type {
  AuthResponse,
  Capabilities,
  ChatRequest,
  ChatResponse,
  Document,
  DocumentIngestRequest,
  DocumentListResponse,
  DocumentSearchRequest,
  DocumentSearchResponse,
  LogoutResponse,
  SessionsResponse,
  ToolListResponse,
  ToolRunRequest,
  ToolRunResponse,
  User,
  WizardStatus,
  WizardAdminRequest,
  WizardAdminResponse,
  WizardCompleteRequest,
  WizardCompleteResponse,
  AuditListResponse,
  HealthResponse,
  UserUpdateRequest,
  Attachment,
  ProfileConfig,
  ProfileUpdateRequest,
  StreamDelta,
  StreamDone,
  StreamError,
  SystemConfig,
  ModelListResponse,
  ModelTestRequest,
  ModelTestResponse,
  ModelUpdateRequest,
  ComfyUIRunRequest,
  ComfyUIRunResponse,
  ComfyUIStatusResponse,
} from '@/types/api';

const BASE_URL = '/api/v1';

async function safeJson<T>(res: Response): Promise<T | null> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

export class ApiError extends Error {
  code: string;
  details?: Record<string, unknown>;

  constructor(code: string, message: string, details?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.details = details;
  }
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (response.status === 401) {
    const isAuthEndpoint = endpoint === '/auth/login' || endpoint === '/auth/register';
    if (!isAuthEndpoint && typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login';
    }
    throw new ApiError('UNAUTHORIZED', 'Not authenticated');
  }

  if (response.status === 501) {
    const data = await safeJson<{ error?: { message?: string } }>(response);
    throw new ApiError('NOT_IMPLEMENTED', data?.error?.message || 'Feature not available');
  }

  if (!response.ok) {
    const data = await safeJson<{ error?: { code?: string; message?: string; details?: Record<string, unknown> } }>(response);
    if (data?.error) {
      throw new ApiError(data.error.code || 'BAD_REQUEST', data.error.message || `HTTP ${response.status}`, data.error.details);
    }
    throw new ApiError('BAD_REQUEST', `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export async function apiFetchResult<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<{ ok: true; data: T } | { ok: false; error: ApiError }> {
  try {
    const data = await apiFetch<T>(endpoint, options);
    return { ok: true, data };
  } catch (err) {
    if (err instanceof ApiError) {
      return { ok: false, error: err };
    }
    const message = err instanceof Error ? err.message : 'Unknown error';
    return { ok: false, error: new ApiError('UNKNOWN', message) };
  }
}

// Auth
export async function login(username: string, password: string): Promise<AuthResponse> {
  return apiFetch<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export async function register(username: string, password: string, role?: 'user' | 'admin'): Promise<User> {
  return apiFetch<User>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password, role }),
  });
}

export async function logout(): Promise<LogoutResponse> {
  return apiFetch<LogoutResponse>('/auth/logout', { method: 'POST' });
}

export async function getCurrentUser(): Promise<User> {
  return apiFetch<User>('/auth/me');
}

// Sessions
export async function getSessions(): Promise<SessionsResponse> {
  return apiFetch<SessionsResponse>('/sessions');
}

export async function deleteSession(sessionId: string): Promise<void> {
  return apiFetch<void>(`/sessions/${sessionId}`, { method: 'DELETE' });
}

export async function deleteAllSessions(): Promise<void> {
  return apiFetch<void>('/sessions', { method: 'DELETE' });
}

// Chat
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  return apiFetch<ChatResponse>('/chat/message', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export type StreamEvent = StreamDelta | StreamDone | StreamError;

export async function* streamChat(
  message: string,
  sessionId?: string,
  images?: string[],
  signal?: AbortSignal
): AsyncGenerator<StreamEvent, void, unknown> {
  const response = await fetch(`${BASE_URL}/chat/stream`, {
    method: 'POST',
    credentials: 'include',
    signal,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId, images }),
  });

  if (!response.ok) {
    const data = await safeJson<{ error?: { message?: string } }>(response);
    throw new ApiError('BAD_REQUEST', data?.error?.message || `Stream failed: ${response.status}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new ApiError('BAD_REQUEST', 'No response body');
  }

  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6)) as StreamEvent;
          yield data;
        } catch {
          // Skip malformed JSON
        }
      }
    }
  }
}

// Documents
export async function ingestDocument(doc: DocumentIngestRequest): Promise<Document> {
  return apiFetch<Document>('/docs/ingest', {
    method: 'POST',
    body: JSON.stringify(doc),
  });
}

export async function listDocuments(visibility?: string, category?: string, skip = 0, limit = 100): Promise<DocumentListResponse> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (visibility) params.set('visibility', visibility);
  if (category) params.set('category', category);
  return apiFetch<DocumentListResponse>(`/docs?${params}`);
}

export async function getDocument(docId: string): Promise<Document> {
  return apiFetch<Document>(`/docs/${docId}`);
}

export async function updateDocument(docId: string, updates: Partial<DocumentIngestRequest>): Promise<Document> {
  return apiFetch<Document>(`/docs/${docId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });
}

export async function deleteDocument(docId: string): Promise<void> {
  return apiFetch<void>(`/docs/${docId}`, { method: 'DELETE' });
}

export async function searchDocuments(request: DocumentSearchRequest): Promise<DocumentSearchResponse> {
  return apiFetch<DocumentSearchResponse>('/docs/search', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// Tools
export async function listTools(): Promise<ToolListResponse> {
  return apiFetch<ToolListResponse>('/tools/list');
}

export async function runTool(request: ToolRunRequest): Promise<ToolRunResponse> {
  return apiFetch<ToolRunResponse>('/tools/run', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// Attachments
export async function uploadAttachment(file: File): Promise<Attachment> {
  const formData = new FormData();
  formData.append('file', file);
  return apiFetch<Attachment>('/attachments', {
    method: 'POST',
    body: formData,
    headers: {},
  });
}

export async function getAttachment(attachmentId: string): Promise<Attachment> {
  return apiFetch<Attachment>(`/attachments/${attachmentId}`);
}

export async function deleteAttachment(attachmentId: string): Promise<void> {
  return apiFetch<void>(`/attachments/${attachmentId}`, { method: 'DELETE' });
}

// Wizard
export async function getWizardStatus(): Promise<WizardStatus> {
  return apiFetch<WizardStatus>('/wizard/status');
}

export async function createWizardAdmin(request: WizardAdminRequest): Promise<WizardAdminResponse> {
  return apiFetch<WizardAdminResponse>('/wizard/admin', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function completeWizard(request: WizardCompleteRequest): Promise<WizardCompleteResponse> {
  return apiFetch<WizardCompleteResponse>('/wizard/complete', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// Users (admin)
export async function listUsers(skip = 0, limit = 100): Promise<User[]> {
  return apiFetch<User[]>(`/users?skip=${skip}&limit=${limit}`);
}

export async function getUser(userId: string): Promise<User> {
  return apiFetch<User>(`/users/${userId}`);
}

export async function updateUser(userId: string, updates: UserUpdateRequest): Promise<User> {
  return apiFetch<User>(`/users/${userId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });
}

export async function deleteUser(userId: string): Promise<void> {
  return apiFetch<void>(`/users/${userId}`, { method: 'DELETE' });
}

// Config
export async function getCapabilities(): Promise<Capabilities> {
  return apiFetch<Capabilities>('/config/capabilities');
}

// Audit
export async function listAuditEvents(
  skip = 0,
  limit = 100,
  eventType?: string,
  userId?: string
): Promise<AuditListResponse> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (eventType) params.set('event_type', eventType);
  if (userId) params.set('user_id', userId);
  return apiFetch<AuditListResponse>(`/audit?${params}`);
}

// Health
export async function healthCheck(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health');
}

// Profile
export async function getProfile(): Promise<ProfileConfig> {
  return apiFetch<ProfileConfig>('/config/profile');
}

export async function updateProfile(updates: ProfileUpdateRequest): Promise<ProfileConfig> {
  return apiFetch<ProfileConfig>('/config/profile', {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });
}

// System Config (admin)
export async function getSystemConfig(): Promise<SystemConfig> {
  return apiFetch<SystemConfig>('/config/system');
}

export async function updateSystemConfig(config: Partial<SystemConfig>): Promise<{ success: true }> {
  return apiFetch<{ success: true }>('/config/system', {
    method: 'PATCH',
    body: JSON.stringify(config),
  });
}

// Models (admin)
export async function listModels(): Promise<ModelListResponse> {
  return apiFetch<ModelListResponse>('/models/list');
}

export async function testModel(request: ModelTestRequest): Promise<ModelTestResponse> {
  return apiFetch<ModelTestResponse>('/models/test', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function updateModel(role: string, request: ModelUpdateRequest): Promise<{ success: true }> {
  return apiFetch<{ success: true }>(`/models/update?role=${role}`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// ComfyUI
export async function runComfyUI(request: ComfyUIRunRequest): Promise<ComfyUIRunResponse> {
  return apiFetch<ComfyUIRunResponse>('/comfyui/run', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

export async function getComfyUIStatus(jobId: string): Promise<ComfyUIStatusResponse> {
  return apiFetch<ComfyUIStatusResponse>(`/comfyui/status/${jobId}`);
}
