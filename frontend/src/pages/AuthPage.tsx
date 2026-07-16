import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Button, Card, Input, Label } from "../components/ui";
import { toLoginCodeAuthPayload } from "../lib/nameAuth";

type Mode = "login" | "register";

export function AuthPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [loginCode, setLoginCode] = useState("");
  const [birthDay, setBirthDay] = useState("");
  const [birthMonth, setBirthMonth] = useState("");
  const [birthYear, setBirthYear] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const clearMessages = () => setError("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessages();

    const payload = toLoginCodeAuthPayload(
      loginCode,
      birthDay,
      birthMonth,
      birthYear,
    );

    if ("error" in payload) {
      setError(payload.error);
      return;
    }

    setLoading(true);
    try {
      if (mode === "login") {
        await login(payload);
      } else {
        await register(payload);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-50 via-white to-slate-100 p-4">
      <Card className="w-full max-w-md p-8">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 text-2xl text-white">
            👶
          </div>
          <h1 className="text-2xl font-bold">Нейроконсультант Гриффитс</h1>
          <p className="mt-2 text-sm text-slate-500">
            Развивающие игры для малышей 0–2 лет
          </p>
        </div>

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

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label>ФИО ребёнка (6 знаков)</Label>
            <Input
              value={loginCode}
              onChange={(e) => setLoginCode(e.target.value.toUpperCase())}
              required
              minLength={6}
              maxLength={6}
              autoComplete="username"
              placeholder="Например: ЮЛАЛСВ"
              className="uppercase tracking-widest"
            />
            <p className="mt-1.5 text-xs text-slate-500">
              2 буквы имени + 2 отчества + 2 фамилии
            </p>
          </div>

          <div>
            <Label>Дата рождения ребёнка</Label>
            <div className="mt-1.5 grid grid-cols-3 gap-2">
              <Input
                type="number"
                min={1}
                max={31}
                value={birthDay}
                onChange={(e) => setBirthDay(e.target.value)}
                required
                placeholder="День"
                aria-label="День рождения"
              />
              <Input
                type="number"
                min={1}
                max={12}
                value={birthMonth}
                onChange={(e) => setBirthMonth(e.target.value)}
                required
                placeholder="Месяц"
                aria-label="Месяц рождения"
              />
              <Input
                type="number"
                min={1920}
                max={new Date().getFullYear()}
                value={birthYear}
                onChange={(e) => setBirthYear(e.target.value)}
                required
                placeholder="Год"
                aria-label="Год рождения"
              />
            </div>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading
              ? "Загрузка…"
              : mode === "login"
                ? "Войти"
                : "Создать аккаунт"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
