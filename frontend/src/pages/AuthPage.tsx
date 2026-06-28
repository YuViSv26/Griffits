import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { Button, Card, Input, Label } from "../components/ui";

type Mode = "login" | "register" | "forgot" | "reset";

function getResetTokenFromUrl(): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get("reset");
}

export function AuthPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [devResetUrl, setDevResetUrl] = useState<string | null>(null);

  useEffect(() => {
    const token = getResetTokenFromUrl();
    if (token) {
      setResetToken(token);
      setMode("reset");
    }
  }, []);

  const clearMessages = () => {
    setError("");
    setInfo("");
    setDevResetUrl(null);
  };

  const handleLoginRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessages();
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  const handleForgot = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessages();
    setLoading(true);
    try {
      const res = await api.forgotPassword(email);
      setInfo(res.message);
      if (res.reset_url) {
        setDevResetUrl(res.reset_url);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessages();
    if (password !== password2) {
      setError("Пароли не совпадают");
      return;
    }
    setLoading(true);
    try {
      const res = await api.resetPassword(resetToken, password);
      setInfo(res.message);
      setMode("login");
      setPassword("");
      setPassword2("");
      window.history.replaceState({}, "", window.location.pathname);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  const title =
    mode === "forgot"
      ? "Восстановление пароля"
      : mode === "reset"
        ? "Новый пароль"
        : "Нейроконсультант Гриффитс";

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-50 via-white to-slate-100 p-4">
      <Card className="w-full max-w-md p-8">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 text-2xl text-white">
            👶
          </div>
          <h1 className="text-2xl font-bold">{title}</h1>
          {mode === "login" || mode === "register" ? (
            <p className="mt-2 text-sm text-slate-500">
              Развивающие игры для малышей 0–2 лет
            </p>
          ) : null}
        </div>

        {(mode === "login" || mode === "register") && (
          <div className="mb-6 flex rounded-xl bg-slate-100 p-1">
            <button
              type="button"
              className={`flex-1 rounded-lg py-2 text-sm font-medium ${
                mode === "login" ? "bg-white shadow-sm" : "text-slate-500"
              }`}
              onClick={() => {
                setMode("login");
                clearMessages();
              }}
            >
              Вход
            </button>
            <button
              type="button"
              className={`flex-1 rounded-lg py-2 text-sm font-medium ${
                mode === "register" ? "bg-white shadow-sm" : "text-slate-500"
              }`}
              onClick={() => {
                setMode("register");
                clearMessages();
              }}
            >
              Регистрация
            </button>
          </div>
        )}

        {mode === "forgot" && (
          <form onSubmit={handleForgot} className="space-y-4">
            <p className="text-sm text-slate-500">
              Введите email — мы отправим ссылку для сброса пароля.
            </p>
            <div>
              <Label>Email</Label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            {info && <p className="text-sm text-green-700">{info}</p>}
            {devResetUrl && (
              <a
                href={devResetUrl}
                className="block break-all rounded-xl bg-brand-50 p-3 text-sm text-brand-700 underline"
              >
                Открыть ссылку для сброса пароля
              </a>
            )}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Отправка…" : "Отправить ссылку"}
            </Button>
            <button
              type="button"
              className="w-full text-sm text-slate-500 hover:text-slate-700"
              onClick={() => {
                setMode("login");
                clearMessages();
              }}
            >
              ← Вернуться ко входу
            </button>
          </form>
        )}

        {mode === "reset" && (
          <form onSubmit={handleReset} className="space-y-4">
            <p className="text-sm text-slate-500">Придумайте новый пароль.</p>
            <div>
              <Label>Новый пароль</Label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                autoComplete="new-password"
              />
            </div>
            <div>
              <Label>Повторите пароль</Label>
              <Input
                type="password"
                value={password2}
                onChange={(e) => setPassword2(e.target.value)}
                required
                minLength={6}
                autoComplete="new-password"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            {info && <p className="text-sm text-green-700">{info}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Сохранение…" : "Сохранить пароль"}
            </Button>
          </form>
        )}

        {(mode === "login" || mode === "register") && (
          <form onSubmit={handleLoginRegister} className="space-y-4">
            <div>
              <Label>Email</Label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <Label>Пароль</Label>
                {mode === "login" && (
                  <button
                    type="button"
                    className="text-xs text-brand-600 hover:text-brand-700"
                    onClick={() => {
                      setMode("forgot");
                      clearMessages();
                    }}
                  >
                    Восстановить пароль
                  </button>
                )}
              </div>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                autoComplete={
                  mode === "login" ? "current-password" : "new-password"
                }
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            {info && <p className="text-sm text-green-700">{info}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading
                ? "Загрузка…"
                : mode === "login"
                  ? "Войти"
                  : "Создать аккаунт"}
            </Button>
          </form>
        )}
      </Card>
    </div>
  );
}
