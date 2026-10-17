export type UserPayload = {
  id: string;
  name: string;
  email: string;
  created_at: string;
};

export type AnalysisItem = {
  id: string;
  title: string;
  status: string;
  original_filename: string;
  duration_seconds: number | null;
  language: string | null;
  analysis_goal: string | null;
  created_at: string;
};

export type AnalysisReport = {
  analysis_id: string;
  overall_score: number;
  summary: string;
  highlights: string[];
  metrics: Record<string, string | number | boolean | null>;
};

export type LoginResponse = {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
};

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getErrorMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object' || !('detail' in payload)) {
    return fallback;
  }

  const { detail } = payload;
  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    for (const item of detail) {
      if (!item || typeof item !== 'object' || !('msg' in item) || typeof item.msg !== 'string') {
        continue;
      }

      if (item.msg === 'String should have at least 8 characters') {
        return 'A senha precisa ter pelo menos 8 caracteres.';
      }

      return item.msg;
    }
  }

  return fallback;
}

function getAuthHeader(): HeadersInit | undefined {
  const token = localStorage.getItem('voxmind_token');
  return token ? { Authorization: `Bearer ${token}` } : undefined;
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  includeAuth = true,
): Promise<T> {
  const headers = new Headers(init.headers ?? {});
  if (includeAuth) {
    const authHeader = getAuthHeader();
    if (authHeader && 'Authorization' in authHeader) {
      headers.set('Authorization', String(authHeader.Authorization));
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(getErrorMessage(payload, 'Erro na requisição'));
  }

  return payload as T;
}

export async function registerUser(input: { name: string; email: string; password: string }): Promise<UserPayload> {
  return request<UserPayload>('/api/v1/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  }, false);
}

export async function loginUser(input: { email: string; password: string }): Promise<LoginResponse> {
  return request<LoginResponse>('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  }, false);
}

export async function getCurrentUser(): Promise<UserPayload> {
  return request<UserPayload>('/api/v1/users/me');
}

export async function listAnalyses(): Promise<AnalysisItem[]> {
  return request<AnalysisItem[]>('/api/v1/analyses');
}

export async function getAnalysisReport(analysisId: string): Promise<AnalysisReport> {
  return request<AnalysisReport>(`/api/v1/analyses/${analysisId}/report`);
}

export async function generateAnalysisReport(
  analysisId: string,
  input: { segments: Array<{ start: number; end: number; text: string }>; language?: string },
): Promise<AnalysisReport> {
  return request<AnalysisReport>(`/api/v1/analyses/${analysisId}/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
}

export async function transcribeAndGenerateReport(analysisId: string): Promise<AnalysisReport> {
  return request<AnalysisReport>(`/api/v1/analyses/${analysisId}/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
}

export async function uploadAnalysis(formData: FormData): Promise<AnalysisItem> {
  const token = localStorage.getItem('voxmind_token');
  const response = await fetch(`${API_BASE_URL}/api/v1/analyses/upload`, {
    method: 'POST',
    body: formData,
    ...(token ? { headers: { Authorization: `Bearer ${token}` } } : {}),
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(getErrorMessage(payload, 'Erro no upload'));
  }

  return payload as AnalysisItem;
}

export function saveToken(token: string) {
  localStorage.setItem('voxmind_token', token);
}

export function clearToken() {
  localStorage.removeItem('voxmind_token');
}
