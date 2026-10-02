/**
 * Solar Operations OS — Typed API Client
 *
 * Centralised HTTP layer for all backend calls.
 * - Attaches Bearer token from localStorage
 * - Handles 401 → silent token refresh → retry once
 * - Throws typed ApiError on HTTP failures
 */

const BASE_URL = '/v1';

// ── Stored auth state ──────────────────────────────────────────────────────────
export interface AuthSession {
  accessToken: string;
  sessionId: string;
  expiresAt: number; // unix ms
}

const TOKEN_KEY = 'solar_os_session';

export function getSession(): AuthSession | null {
  const raw = localStorage.getItem(TOKEN_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    return null;
  }
}

export function setSession(session: AuthSession): void {
  localStorage.setItem(TOKEN_KEY, JSON.stringify(session));
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// ── Error class ────────────────────────────────────────────────────────────────
export class ApiError extends Error {
  status: number;
  detail: string;
  code?: string;

  constructor(status: number, detail: string, code?: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
    this.code = code;
  }
}

// ── Core fetch wrapper ─────────────────────────────────────────────────────────
async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  retried = false,
): Promise<T> {
  const session = getSession();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (session?.accessToken) {
    headers['Authorization'] = `Bearer ${session.accessToken}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    credentials: 'include', // for httponly refresh_token cookie
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  // Silent token refresh on first 401
  if (response.status === 401 && !retried && session) {
    const refreshed = await attemptRefresh();
    if (refreshed) {
      return request<T>(method, path, body, true);
    } else {
      clearSession();
      window.dispatchEvent(new CustomEvent('solar-os:unauthorized'));
      throw new ApiError(401, 'Session expired. Please log in again.');
    }
  }

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    let code: string | undefined;
    try {
      const err = await response.json();
      detail = err.detail ?? err.message ?? detail;
      code = err.code;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(response.status, detail, code);
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

async function attemptRefresh(): Promise<boolean> {
  try {
    const resp = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!resp.ok) return false;
    const data = await resp.json() as TokenResponse;
    setSession({
      accessToken: data.access_token,
      sessionId: data.session_id,
      expiresAt: Date.now() + data.expires_in * 1000,
    });
    return true;
  } catch {
    return false;
  }
}

// ── HTTP helpers ───────────────────────────────────────────────────────────────
export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
  patch: <T>(path: string, body: unknown) => request<T>('PATCH', path, body),
  delete: <T>(path: string) => request<T>('DELETE', path),
};

// ── Auth API ───────────────────────────────────────────────────────────────────
export interface LoginRequest {
  email: string;
  password: string;
  organization_slug: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  requires_totp: boolean;
  session_id: string;
}

export const authApi = {
  login: (body: LoginRequest) => api.post<TokenResponse>('/auth/login', body),
  logout: () => api.post<void>('/auth/logout'),
  refresh: () => api.post<TokenResponse>('/auth/refresh'),
  verifyTotp: (totp_code: string) =>
    api.post<TokenResponse>('/auth/totp/verify', { totp_code }),
};

// ── CRM / Customer API ─────────────────────────────────────────────────────────
export interface CustomerRead {
  id: string;
  organization_id: string;
  name: string;
  type: string;
  email?: string | null;
  phone?: string | null;
  gstin?: string | null;
  pan?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  pincode?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface SiteRead {
  id: string;
  customer_id: string;
  name: string;
  address: string;
  city?: string | null;
  state: string;
  pincode?: string | null;
  discom_name?: string | null;
  consumer_number?: string | null;
  sanctioned_load_kw?: number | null;
  rooftop_area_sqm?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  is_active: boolean;
  created_at: string;
}

export const crmApi = {
  listCustomers: (limit = 50, query?: string) =>
    api.get<CustomerRead[]>(`/crm/customers?limit=${limit}${query ? `&query=${encodeURIComponent(query)}` : ''}`),
  getCustomer: (id: string) =>
    api.get<CustomerRead>(`/crm/customers/${id}`),
  listSites: (customerId?: string, limit = 50) =>
    api.get<SiteRead[]>(`/crm/sites?limit=${limit}${customerId ? `&customer_id=${customerId}` : ''}`),
  getSite: (id: string) => api.get<SiteRead>(`/crm/sites/${id}`),
};

// ── Projects API ───────────────────────────────────────────────────────────────
export interface ProjectRead {
  id: string;
  plant_id?: string | null;
  name: string;
  customer_id: string;
  site_id: string;
  stage: string;
  capacity_kwp_dc: number;
  capacity_kw_ac?: number | null;
  state_code: string;
  created_at: string;
  commissioned_at?: string | null;
}

export const projectApi = {
  list: (stage?: string, limit = 50) =>
    api.get<ProjectRead[]>(`/projects?limit=${limit}${stage ? `&stage=${stage}` : ''}`),
  get: (id: string) => api.get<ProjectRead>(`/projects/${id}`),
  transition: (id: string, target_stage: string, reason?: string) =>
    api.post<ProjectRead>(`/projects/${id}/transition`, { target_stage, reason }),
};

// ── Telemetry API ──────────────────────────────────────────────────────────────
export interface GenerationRecordOut {
  id: string;
  plant_id: string;
  interval_start: string;
  interval_end: string;
  energy_kwh: number;
  peak_power_kw: number;
  avg_power_kw: number;
  irradiance_wm2?: number | null;
  performance_ratio?: number | null;
}

export interface GenerationSummaryOut {
  plant_id: string;
  total_kwh: number;
  peak_kw: number;
  avg_power_kw: number;
  record_count: number;
  start_time?: string | null;
  end_time?: string | null;
}

export interface TelemetryAlarmOut {
  id: string;
  plant_id: string;
  alarm_code: string;
  severity: string;
  message: string;
  status: string;
  triggered_at: string;
  acknowledged_at?: string | null;
  resolved_at?: string | null;
}

export const telemetryApi = {
  getGenerationSummary: (plantId: string, startTime?: string, endTime?: string) => {
    const params = new URLSearchParams({ plant_id: plantId });
    if (startTime) params.set('start_time', startTime);
    if (endTime) params.set('end_time', endTime);
    return api.get<GenerationSummaryOut>(`/telemetry/generation/summary?${params}`);
  },
  listGenerationRecords: (plantId: string, limit = 100, startTime?: string) => {
    const params = new URLSearchParams({ plant_id: plantId, limit: String(limit) });
    if (startTime) params.set('start_time', startTime);
    return api.get<GenerationRecordOut[]>(`/telemetry/generation?${params}`);
  },
  listAlarms: (plantId?: string, status?: string) => {
    const params = new URLSearchParams();
    if (plantId) params.set('plant_id', plantId);
    if (status) params.set('status', status);
    return api.get<TelemetryAlarmOut[]>(`/telemetry/alarms?${params}`);
  },
};

// ── Compliance API ─────────────────────────────────────────────────────────────
export interface ComplianceRunOut {
  id: string;
  project_id: string;
  rule_set_id: string;
  status: string;
  passed: number;
  failed: number;
  warned: number;
  waived: number;
  triggered_at: string;
  completed_at?: string | null;
}

export const complianceApi = {
  listRuns: (projectId: string) =>
    api.get<ComplianceRunOut[]>(`/compliance/runs?project_id=${projectId}`),
  triggerRun: (projectId: string, ruleSetId: string) =>
    api.post<ComplianceRunOut>('/compliance/runs', { project_id: projectId, rule_set_id: ruleSetId }),
};

// ── O&M / Service Tickets API ─────────────────────────────────────────────────
export interface ServiceTicketOut {
  id: string;
  number: string;
  plant_id: string;
  title: string;
  category: string;
  priority: string;
  status: string;
  assignee_user_id?: string | null;
  created_at: string;
  resolved_at?: string | null;
}

export const oamApi = {
  listTickets: (plantId?: string, status?: string, limit = 50) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (plantId) params.set('plant_id', plantId);
    if (status) params.set('status', status);
    return api.get<ServiceTicketOut[]>(`/oam/tickets?${params}`);
  },
};
