import { useEffect, useState } from "react";
import { Button, Card, Input, Label } from "./ui";

interface Props {
  initialName?: string;
  initialBirthday?: string;
  ageLabel?: string;
  onComplete: (name: string, birthday: string) => Promise<void>;
}

function formatBirthdayRu(iso: string): string {
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${d}.${m}.${y}`;
}

export function OnboardingForm({
  initialName,
  initialBirthday,
  ageLabel,
  onComplete,
}: Props) {
  const hasProfile = Boolean(initialName && initialBirthday);
  const [name, setName] = useState(initialName ?? "");
  const [birthday, setBirthday] = useState(initialBirthday ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setName(initialName ?? "");
    setBirthday(initialBirthday ?? "");
  }, [initialName, initialBirthday]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaved(false);
    if (name.trim().length < 2) {
      setError("Имя должно быть не короче 2 символов");
      return;
    }
    setLoading(true);
    try {
      await onComplete(name.trim(), birthday);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка сохранения");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="mx-auto max-w-md p-6">
      <h2 className="mb-1 text-xl font-semibold">
        {hasProfile ? "Профиль ребёнка" : "Профиль малыша"}
      </h2>
      <p className="mb-6 text-sm text-slate-500">
        {hasProfile
          ? "Данные используются для подбора игр и шкалы Гриффитс"
          : "Укажите имя и дату рождения для подбора игр и оценки развития"}
      </p>

      {hasProfile && (
        <div className="mb-6 rounded-xl border border-brand-100 bg-brand-50/50 p-4">
          <p className="text-lg font-semibold text-slate-800">{initialName}</p>
          {ageLabel && (
            <p className="mt-1 text-sm text-brand-700">Возраст: {ageLabel}</p>
          )}
          <p className="mt-1 text-sm text-slate-500">
            Дата рождения: {formatBirthdayRu(initialBirthday!)}
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label>Имя ребёнка</Label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Миша"
            required
          />
        </div>
        <div>
          <Label>Дата рождения</Label>
          <Input
            type="date"
            value={birthday}
            onChange={(e) => setBirthday(e.target.value)}
            required
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        {saved && (
          <p className="text-sm text-green-600">Изменения сохранены</p>
        )}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading
            ? "Сохранение…"
            : hasProfile
              ? "Сохранить изменения"
              : "Продолжить"}
        </Button>
      </form>
    </Card>
  );
}
