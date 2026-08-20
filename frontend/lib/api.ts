/**
 * Thin typed client for the PANGAEA backend (localhost demo).
 * Access token lives in localStorage; a 401 triggers one cookie-based refresh.
 */

// The backend follows the host the page was opened from, so a phone on the
// same network reaching http://<mac-ip>:3000 talks to <mac-ip>:8000 without
// any configuration. NEXT_PUBLIC_API_BASE still overrides when set.
function apiBase(): string {
  if (process.env.NEXT_PUBLIC_API_BASE) return process.env.NEXT_PUBLIC_API_BASE;
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return "http://localhost:8000";
}
const API_BASE = apiBase();
const TOKEN_KEY = "pangaea_access";

export type Trust = { value: number | null; status: string; is_demo?: boolean };
export type ProfileCard = {
  id: string;
  display_name: string;
  initials: string;
  palette: number;
  kind: string;
  locale: string;
  timezone: string;
  city_code: string | null;
  local_time: string;
  headline: string;
  verified_count: number;
  trust?: Trust;
};
export type SignalRole = {
  id: string;
  label: string;
  headcount: number | null;
  filled_count: number;
  form_position: number;
};
export type Signal = {
  id: string;
  signal_type: "HELP" | "WORK" | "CIRCLE" | "BOOKING";
  status: string;
  raw_text: string;
  urgency: string;
  requires_physical_presence: boolean;
  source_language: string;
  team_cardinality: string;
  target_is_team: boolean;
  duration_weeks: number | null;
  duration_origin: string;
  compensation: {
    is_paid: boolean;
    amount_minor: number | null;
    currency: string | null;
    origin: string;
  };
  license_risk: { flagged: boolean; kind: string; acknowledged: boolean };
  required_credentials: string[];
  disclaimers: string[];
  area_hint: string | null;
  published_at: string | null;
  created_at: string;
  requester: ProfileCard | null;
  roles: SignalRole[];
  skills: { name: string; origin: string; confirmation_status: string }[];
  accepted_count: number;
  accept_latency_seconds: number | null;
  member_faces: { initials: string; palette: number }[];
};
export type SignalMutation = {
  raw_text: string;
  roles_form: { label: string; headcount: number | null; form_position: number }[];
  edits?: Record<string, unknown>;
};
export type ParseData = {
  signal_type: string;
  urgency: string;
  roles_requested: { label: string; headcount: number | null; form_position: number }[];
  skills: { name: string; origin: string; evidence_span: string }[];
  duration: { weeks: number | null; origin: string; evidence_span: string | null };
  team_shape: { cardinality: string; headcount_hint: number | null; target_is_team: boolean };
  compensation: { is_paid: boolean; amount_krw: number | null; origin: string };
  license_risk: { flagged: boolean; kind: string; rationale: string | null };
  required_credentials: string[];
  disclaimers: string[];
  crisis_notice?: string;
};
export type AiEnvelope<T> = {
  ok: boolean;
  data: T;
  degraded: boolean;
  degrade_reason: string | null;
  meta: { module: string; mode: string; schema_version: string };
};
export type GuardData = {
  display: boolean;
  rewritten_text: string | null;
  risk: string;
  phenomenon: string;
  reader_reading: string | null;
  suggestion: string | null;
  kb_ids: string[];
  guard_token: string;
};
export type Candidate = {
  rank: number;
  profile: ProfileCard;
  role_fit: "MATCHED" | "DIFFERENT";
  overlap_hours_per_day: number;
  verified_relevant_count: number;
  why: string | null;
};
export type Recommendations = {
  explain: { policy_version: string; criteria: string[]; exclusions: string[] };
  candidates: Candidate[];
};
export type ChatMessage = {
  id: string;
  mine: boolean;
  sender: { id: string; name: string; locale: string };
  source_text: string;
  source_lang: string;
  delivery_status: string;
  created_at: string;
  shown_text: string;
  original_line: string | null;
  translation_status: string | null;
  help: { heading: string; level: string; annotation: string; kb_ids: string[] } | null;
  guard_badge: string | null;
  receipts: { name: string; text: string }[];
  crisis_notice?: string;
};
export type ConversationSummary = {
  id: string;
  collaboration_id: string;
  title: string;
  status: string;
  member_count: number;
  member_names: string[];
  member_cities: string[];
  translation_on: boolean;
};
export type DepositParty = {
  profile_id: string;
  name: string;
  agreed: boolean;
  funded: boolean;
  refunded: boolean;
  me: boolean;
};
export type Deposit = {
  id: string;
  status: string;
  currency: string;
  amount_minor_per_party: number;
  total_minor: number;
  terms_hash: string;
  parties: DepositParty[];
} | null;
export type CollabMember = {
  profile_id: string;
  name: string;
  initials: string;
  palette: number;
  role_label: string;
  is_requester: boolean;
  me: boolean;
  city_code: string | null;
  locale: string;
  trust: { value: number | null; status: string; before_completion: number | null };
};
export type Collaboration = {
  id: string;
  title: string;
  status: string;
  deposit_applies: boolean;
  signal_id: string;
  signal_type: string | null;
  duration_weeks: number | null;
  conversation_id: string | null;
  members: CollabMember[];
  deposit: Deposit;
  deliverables: { id: string; file_name: string; hash_prefix: string }[];
  my_confirmation: boolean;
  confirmed_count: number;
  completed_at: string | null;
  my_review_targets: string[];
};
export type HomeData = {
  profile: ProfileCard | null;
  cities: { code: string; local_time: string; state: string; member_count: number }[];
  signals: Signal[];
  open_count: number;
  my_collaboration_count: number;
};
export type ProfileDetail = ProfileCard & {
  bio: string;
  skills: { name: string; normalized: string; years: number | null; verified: boolean }[];
  languages: { code: string; proficiency: string }[];
  availability: { weekday: number; start: string; end: string; timezone: string }[];
  overlap_hours_per_day: number;
  reviews: {
    id: string;
    rating: string;
    tags: string[];
    comment: string;
    reviewer_name: string;
    created_at: string;
  }[];
};
export type ApplicationItem = {
  id: string;
  signal_id: string;
  signal_text: string;
  signal_type: string | null;
  direction: string;
  status: string;
  message: string;
  role_label: string | null;
  applicant: ProfileCard | null;
  created_at: string;
};
export type NotificationItem = {
  id: string;
  kind: string;
  payload: Record<string, string>;
  resource_type: string | null;
  resource_id: string | null;
  read: boolean;
  created_at: string;
};
export type KbSheet = {
  id: string;
  claim: string;
  scope_locale: string;
  scope_context: string;
  sources: { url: string; title: string }[];
  verified_at: string;
  base_confidence: number;
  effective_confidence: number;
  level: string | null;
  dispute_count: number;
};
export type SearchResult = { terms: string[]; results: ProfileCard[]; total: number };
export type Me = {
  user_id: string;
  email: string;
  locale: string;
  unread_notifications: number;
  profile: ProfileCard | null;
};

export class ApiError extends Error {
  code: string;
  status: number;
  details: unknown;
  constructor(code: string, message: string, status: number, details: unknown) {
    super(message);
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

async function refreshToken(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (!response.ok) return false;
    const body = await response.json();
    setToken(body.data.access_token);
    return true;
  } catch {
    return false;
  }
}

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; retry?: boolean } = {},
): Promise<T> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method ?? "GET",
    headers,
    credentials: "include",
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });
  if (response.status === 401 && options.retry !== false) {
    if (await refreshToken()) return request<T>(path, { ...options, retry: false });
    setToken(null);
    if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
      const locale = window.location.pathname.split("/")[1] || "ko";
      window.location.href = `/${locale}/login`;
    }
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = body?.error ?? {};
    throw new ApiError(
      error.code ?? "UNKNOWN",
      error.message ?? "request failed",
      response.status,
      error.details,
    );
  }
  // AI routes return the E3 envelope unwrapped; everything else uses {data}.
  return (
    body?.data !== undefined && body?.ok !== undefined && !path.startsWith("/api/v1/ai")
      ? body.data
      : body
  ) as T;
}

export const api = {
  async login(email: string, password: string) {
    const data = await request<{ access_token: string }>("/api/v1/auth/login", {
      method: "POST",
      body: { email, password },
      retry: false,
    });
    setToken(data.access_token);
    return data;
  },
  async register(email: string, password: string, locale: string) {
    const data = await request<{ access_token: string }>("/api/v1/auth/register", {
      method: "POST",
      body: { email, password, default_locale: locale },
      retry: false,
    });
    setToken(data.access_token);
    return data;
  },
  async logout() {
    await request("/api/v1/auth/logout", { method: "POST", retry: false }).catch(() => null);
    setToken(null);
  },
  me: () => request<Me>("/api/v1/me"),
  myProfile: () => request<ProfileDetail>("/api/v1/me/profile"),
  patchProfile: (body: Record<string, string>) =>
    request<ProfileCard>("/api/v1/me/profile", { method: "PATCH", body }),
  putSkills: (skills: { name: string; years: number | null }[]) =>
    request("/api/v1/me/skills", { method: "PUT", body: skills }),
  putLanguages: (languages: { code: string; proficiency: string }[]) =>
    request("/api/v1/me/languages", { method: "PUT", body: languages }),
  putAvailability: (rules: { weekday: number; start: string; end: string }[]) =>
    request("/api/v1/me/availability", { method: "PUT", body: rules }),
  home: () => request<HomeData>("/api/v1/home"),
  profile: (id: string) => request<ProfileDetail>(`/api/v1/profiles/${id}`),
  trust: (id: string) => request<Trust & { profile_id: string }>(`/api/v1/profiles/${id}/trust`),
  parse: (
    raw_text: string,
    roles_form: { label: string; headcount: number | null; form_position: number }[],
  ) =>
    request<AiEnvelope<ParseData>>("/api/v1/ai/parse", {
      method: "POST",
      body: { raw_text, roles_form },
    }),
  createSignal: (body: SignalMutation) =>
    request<Signal>("/api/v1/signals", { method: "POST", body }),
  updateSignal: (
    id: string,
    body: SignalMutation & {
      inferred_confirmed: boolean;
      license_acknowledged: boolean;
      high_risk_acknowledged: boolean;
    },
  ) => request<Signal>(`/api/v1/signals/${id}`, { method: "PATCH", body }),
  deleteSignal: (id: string) => request<void>(`/api/v1/signals/${id}`, { method: "DELETE" }),
  publishSignal: (id: string, confirmations: Record<string, boolean>) =>
    request<Signal>(`/api/v1/signals/${id}/publish`, { method: "POST", body: confirmations }),
  signal: (id: string) => request<Signal>(`/api/v1/signals/${id}`),
  signals: (params?: { type?: string; mine?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.type) query.set("type", params.type);
    if (params?.mine) query.set("mine", "true");
    const suffix = query.toString() ? `?${query}` : "";
    return request<Signal[]>(`/api/v1/signals${suffix}`);
  },
  recommendations: (signalId: string) =>
    request<Recommendations>(`/api/v1/signals/${signalId}/recommendations`),
  searchProfiles: (q: string) =>
    request<SearchResult>(`/api/v1/search/profiles?q=${encodeURIComponent(q)}`),
  apply: (
    signalId: string,
    body: {
      role_id?: string | null;
      message?: string;
      direction?: string;
      invitee_profile_id?: string;
    },
  ) =>
    request<{ id: string }>(`/api/v1/signals/${signalId}/applications`, {
      method: "POST",
      body,
    }),
  applications: (box: "received" | "sent") =>
    request<ApplicationItem[]>(`/api/v1/applications?box=${box}`),
  acceptApplication: (id: string) =>
    request<{ collaboration_id: string; conversation_id: string | null }>(
      `/api/v1/applications/${id}/accept`,
      { method: "POST" },
    ),
  rejectApplication: (id: string) =>
    request(`/api/v1/applications/${id}/reject`, { method: "POST" }),
  withdrawApplication: (id: string) =>
    request(`/api/v1/applications/${id}/withdraw`, { method: "POST" }),
  collaborations: () => request<Collaboration[]>("/api/v1/collaborations"),
  collaboration: (id: string) => request<Collaboration>(`/api/v1/collaborations/${id}`),
  proposeDeposit: (collaborationId: string, amountMinor: number) =>
    request<{
      agreement: NonNullable<Deposit>;
      draft: { clauses: { key: string; text: string }[]; notice: string };
    }>(`/api/v1/collaborations/${collaborationId}/deposit-proposals`, {
      method: "POST",
      body: { amount_minor: amountMinor },
    }),
  agreeDeposit: (agreementId: string) =>
    request<NonNullable<Deposit>>(`/api/v1/deposit-agreements/${agreementId}/agree`, {
      method: "POST",
    }),
  fundDeposit: (agreementId: string) =>
    request<NonNullable<Deposit>>(`/api/v1/deposit-agreements/${agreementId}/fund`, {
      method: "POST",
    }),
  confirmCompletion: (collaborationId: string) =>
    request<{ completed: boolean; collaboration: Collaboration }>(
      `/api/v1/collaborations/${collaborationId}/completion-confirmations`,
      { method: "POST" },
    ),
  createReview: (
    collaborationId: string,
    body: { reviewee_profile_id: string; rating: string; tags: string[]; comment: string },
  ) => request(`/api/v1/collaborations/${collaborationId}/reviews`, { method: "POST", body }),
  conversations: () => request<ConversationSummary[]>("/api/v1/conversations"),
  conversation: (id: string) => request<ConversationSummary>(`/api/v1/conversations/${id}`),
  messages: (conversationId: string) =>
    request<ChatMessage[]>(`/api/v1/conversations/${conversationId}/messages`),
  sendMessage: (
    conversationId: string,
    body: {
      client_message_id: string;
      text: string;
      guard_token?: string;
      guard_choice?: string;
    },
  ) =>
    request<ChatMessage>(`/api/v1/conversations/${conversationId}/messages`, {
      method: "POST",
      body,
    }),
  guard: (conversationId: string, text: string) =>
    request<AiEnvelope<GuardData>>("/api/v1/ai/guard", {
      method: "POST",
      body: { conversation_id: conversationId, text },
    }),
  kb: (id: string) => request<KbSheet>(`/api/v1/kb/${id}`),
  disputeKb: (id: string, comment: string) =>
    request<KbSheet>(`/api/v1/kb/${id}/disputes`, { method: "POST", body: { comment } }),
  notifications: () => request<NotificationItem[]>("/api/v1/notifications"),
  readNotification: (id: string) => request(`/api/v1/notifications/${id}/read`, { method: "POST" }),
};

export function formatKrw(amountMinor: number | null): string {
  if (amountMinor === null) return "";
  return `${amountMinor.toLocaleString("ko-KR")}원`;
}
