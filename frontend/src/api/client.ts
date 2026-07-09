const TOKEN_KEY = "griffiths_access_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(path, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export interface InitResponse {
  authenticated: boolean;
  email?: string;
  registered: boolean;
  baby_name?: string;
  baby_birthday?: string;
  age_label?: string;
  age_months?: number;
}

export interface AuthResponse {
  user_id: number;
  email: string;
  access_token: string;
}

export interface ProfileResponse {
  baby_name: string;
  baby_birthday: string;
  age_label: string;
  age_months: number;
  warning?: string;
}

export interface QuestionItem {
  subscale: string;
  text: string;
}

export interface AssessmentQuestionsResponse {
  questions: QuestionItem[];
  total: number;
}

export interface ScaleResultsPayload {
  locomotion: string | null;
  social: string | null;
  speech: string | null;
  eye_hand: string | null;
  play: string | null;
}

export interface ScaleResultItem {
  scale: string;
  name: string;
  skill: string | null;
  score: number;
  ball?: number | null;
  age_equivalent_months?: number | null;
}

export interface GriffithsSummaryResponse {
  chronologic_age_months: number;
  total_balls: number;
  total_age_equivalent_months: number;
  norm_total_min: number;
  norm_total_max: number;
  scales: ScaleResultItem[];
}

export interface AssessmentResultResponse {
  age_months: number;
  scales: ScaleResultItem[];
  summary: GriffithsSummaryResponse;
}

export interface AssessmentLatestResponse extends AssessmentResultResponse {
  test_date: string;
}

export interface GameResponse {
  id: number;
  title: string;
  subscale: string;
  subscale_name: string;
  age_label: string;
  focus_subscale: string;
  focus_subscale_name: string;
  develops: string;
  description: string;
  safety_rules: string;
}

export interface ProgressItem {
  subscale: string;
  name: string;
  score: number;
  bar: string;
  delta?: number | null;
  skill?: string | null;
}

export interface ProgressResponse {
  baby_name: string;
  last_test_date: string | null;
  items: ProgressItem[];
  strongest: string;
  weakest: string;
  message?: string;
}

export interface ChatMessageItem {
  role: string;
  content: string;
  created_at: string;
}

export interface ExpectedSkillBlock {
  scale: string;
  scale_name: string;
  skills: string[];
}

export interface GameSuggestion {
  title: string;
  develops: string;
  description: string;
  safety_rules: string;
}

export interface PracticeTip {
  icon: string;
  label: string;
  value: string;
}

export interface TodayPlanResponse {
  baby_name: string;
  age_label: string;
  age_months: number;
  focus_scale: string;
  focus_scale_name: string;
  focus_subscale_code: string;
  expected_skills: ExpectedSkillBlock[];
  attention_points: string[];
  games: GameSuggestion[];
  practice_tips: PracticeTip[];
  important_reminder: string;
  has_assessment: boolean;
  weakest_scale_name: string | null;
  weakest_score: number | null;
}

export interface CreatePlanPaymentResponse {
  payment_id: string;
  confirmation_url: string;
  amount_rub: number;
  status: string;
}

export interface PlanPaymentStatusResponse {
  payment_id: string;
  status: string;
  paid: boolean;
  can_download: boolean;
  amount_rub: number;
}

export const api = {
  init: () => request<InitResponse>("/api/init"),
  me: () => request<InitResponse>("/api/me"),

  register: (email: string, password: string) =>
    request<AuthResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  logout: () =>
    request<{ ok: boolean }>("/api/auth/logout", { method: "POST" }),

  forgotPassword: (email: string) =>
    request<{ message: string; email_sent: boolean; reset_url?: string | null }>(
      "/api/auth/forgot-password",
      {
        method: "POST",
        body: JSON.stringify({
          email,
          reset_base_url: window.location.origin,
        }),
      }
    ),

  resetPassword: (token: string, password: string) =>
    request<{ message: string }>("/api/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, password }),
    }),

  saveProfile: (baby_name: string, baby_birthday: string) =>
    request<ProfileResponse>("/api/profile", {
      method: "POST",
      body: JSON.stringify({ baby_name, baby_birthday }),
    }),

  getLatestAssessment: () =>
    request<AssessmentLatestResponse>("/api/assessment/latest"),

  submitAssessment: (payload: {
    age_months: number;
    results: ScaleResultsPayload;
  }) =>
    request<AssessmentResultResponse>("/api/assessment/submit", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getGameToday: () => request<GameResponse>("/api/games/today"),

  getTodayPlan: () => request<TodayPlanResponse>("/api/games/today-plan"),

  createPlanPdfPayment: () =>
    request<CreatePlanPaymentResponse>("/api/payments/plan-pdf/create", {
      method: "POST",
    }),

  getPlanPdfPaymentStatus: (paymentId: string) =>
    request<PlanPaymentStatusResponse>(
      `/api/payments/plan-pdf/${encodeURIComponent(paymentId)}`
    ),

  getLatestPlanPdfPaymentStatus: () =>
    request<PlanPaymentStatusResponse>("/api/payments/plan-pdf/latest/status"),

  markPlanPdfDownloaded: (paymentId: string) =>
    request<{ ok: boolean }>(
      `/api/payments/plan-pdf/${encodeURIComponent(paymentId)}/downloaded`,
      { method: "POST" }
    ),

  getProgress: () => request<ProgressResponse>("/api/progress"),

  getChatHistory: () =>
    request<{ messages: ChatMessageItem[] }>("/api/chat/history"),

  async *streamChat(message: string): AsyncGenerator<string, void, unknown> {
    const token = getToken();
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      credentials: "include",
      body: JSON.stringify({ message, stream: true }),
    });

    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail ?? detail;
      } catch {
        /* ignore */
      }
      throw new Error(typeof detail === "string" ? detail : "Ошибка чата");
    }

    const reader = res.body?.getReader();
    if (!reader) throw new Error("Нет потока ответа");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6).trim();
        if (payload === "[DONE]") return;
        try {
          const parsed = JSON.parse(payload) as {
            content?: string;
            error?: string;
          };
          if (parsed.error) throw new Error(parsed.error);
          if (parsed.content) yield parsed.content;
        } catch (e) {
          if (e instanceof SyntaxError) continue;
          throw e;
        }
      }
    }
  },
};
