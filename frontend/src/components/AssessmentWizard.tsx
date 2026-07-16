import { useState } from "react";
import { api, type ScaleResultItem } from "../api/client";
import { SCALES, type ScaleKey } from "../data/assessmentScales";
import {
  calculateAge,
  createScaleSession,
  processAnswer,
  type ScaleResults,
  type ScaleSessionState,
} from "../lib/assessmentEngine";
import { Button, Card, Input, Label, Spinner } from "./ui";

type Phase = "start" | "testing" | "results";

interface Props {
  babyBirthday?: string;
  onComplete: () => void;
  onSkip: () => void;
}

function resultsFromScales(scales: ScaleResultItem[]): ScaleResults {
  const empty: ScaleResults = {
    locomotion: null,
    social: null,
    speech: null,
    eye_hand: null,
    play: null,
  };
  for (const row of scales) {
    if (row.scale in empty) {
      empty[row.scale as ScaleKey] = row.skill;
    }
  }
  return empty;
}

export function AssessmentWizard({
  babyBirthday,
  onComplete,
  onSkip,
}: Props) {
  const [phase, setPhase] = useState<Phase>("start");
  const [birthday, setBirthday] = useState(babyBirthday ?? "");
  const [ageMonths, setAgeMonths] = useState(0);
  const [ageLabel, setAgeLabel] = useState("");
  const [warning, setWarning] = useState("");

  const [scaleIndex, setScaleIndex] = useState(0);
  const [session, setSession] = useState<ScaleSessionState | null>(null);
  const [allResults, setAllResults] = useState<Partial<ScaleResults>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const [isReadOnly, setIsReadOnly] = useState(false);
  const [testDate, setTestDate] = useState<string | null>(null);
  const [loadingLatest, setLoadingLatest] = useState(false);
  const [latestError, setLatestError] = useState("");

  const currentScale = SCALES[scaleIndex];
  const currentQuestion = session
    ? currentScale?.questions[session.currentIndex]
    : null;

  const resetToStart = () => {
    setIsReadOnly(false);
    setTestDate(null);
    setAllResults({});
    setLatestError("");
    setError("");
    setPhase("start");
  };

  const startAssessment = () => {
    setError("");
    setIsReadOnly(false);
    setTestDate(null);
    const age = calculateAge(birthday);
    if (!age.ok) {
      setWarning(age.warning ?? "Некорректная дата");
      return;
    }
    setWarning("");
    setAgeMonths(age.months);
    setAgeLabel(age.label);
    setScaleIndex(0);
    setAllResults({});
    setSession(createScaleSession(SCALES[0], age.months));
    setPhase("testing");
  };

  const showLatestAssessment = async () => {
    setLoadingLatest(true);
    setLatestError("");
    try {
      const data = await api.getLatestAssessment();
      setAgeMonths(data.age_months);
      setAgeLabel(`${data.age_months} мес.`);
      setAllResults(resultsFromScales(data.scales));
      setTestDate(data.test_date);
      setIsReadOnly(true);
      setPhase("results");
    } catch (e) {
      setLatestError(
        e instanceof Error ? e.message : "Не удалось загрузить оценку"
      );
    } finally {
      setLoadingLatest(false);
    }
  };

  const saveAndShowResults = async (updated: Partial<ScaleResults>) => {
    setSubmitting(true);
    setError("");
    setAllResults(updated);
    setSession(null);
    try {
      await api.submitAssessment({
        age_months: ageMonths,
        results: updated as ScaleResults,
      });
      setPhase("results");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка сохранения");
      setPhase("testing");
    } finally {
      setSubmitting(false);
    }
  };

  const finishScale = (result: string | null) => {
    const key = currentScale.key;
    const updated = { ...allResults, [key]: result };

    if (scaleIndex + 1 >= SCALES.length) {
      void saveAndShowResults(updated);
      return;
    }

    setAllResults(updated);
    const nextIndex = scaleIndex + 1;
    setScaleIndex(nextIndex);
    setSession(createScaleSession(SCALES[nextIndex], ageMonths));
  };

  const handleAnswer = (yes: boolean) => {
    if (!session || !currentScale || submitting) return;
    const next = processAnswer(currentScale, session, yes);
    setSession(next);
    if (next.finished) {
      finishScale(next.resultSkill);
    }
  };

  if (phase === "results") {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <Card className="border-violet-200 bg-gradient-to-b from-violet-50/60 to-white p-6 text-center">
          <h2 className="text-xl font-semibold text-violet-900">
            {isReadOnly ? "План по последней оценке" : "Тест завершён"}
          </h2>
          {isReadOnly && testDate && (
            <p className="mt-1 text-sm text-violet-600">Дата теста: {testDate}</p>
          )}
          <p className="mt-3 text-sm text-slate-600">Результаты сохранены.</p>
        </Card>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex gap-3">
          {isReadOnly ? (
            <>
              <Button
                className="flex-1 bg-violet-600 hover:bg-violet-700"
                onClick={resetToStart}
              >
                Пройти тест заново
              </Button>
              <Button variant="secondary" onClick={onSkip}>
                Закрыть
              </Button>
            </>
          ) : (
            <>
              <Button
                className="flex-1 bg-violet-600 hover:bg-violet-700"
                onClick={onComplete}
              >
                Ввести организацию и отправить результат лечащему доктору
              </Button>
              <Button variant="secondary" onClick={onSkip}>
                Закрыть
              </Button>
            </>
          )}
        </div>
      </div>
    );
  }
  if (phase === "start") {
    return (
      <Card className="mx-auto max-w-lg border-violet-100 bg-gradient-to-b from-violet-50/80 to-white p-6">
        <h2 className="text-xl font-semibold text-violet-900">
          Шкала Гриффитс
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          Адаптивный опрос по методике Кешишян (0–2 года): моторика, социальная
          адаптация, слух и речь, глаза и руки, способность к игре.
        </p>
        <div className="mt-6 space-y-4">
          <div>
            <Label>Дата рождения ребёнка</Label>
            {babyBirthday ? (
              <p className="mt-1.5 rounded-xl border border-violet-100 bg-violet-50/50 px-3 py-2 text-sm text-slate-700">
                {birthday.split("-").reverse().join(".")}
              </p>
            ) : (
              <Input
                type="date"
                value={birthday}
                onChange={(e) => setBirthday(e.target.value)}
                required
              />
            )}
          </div>
          {warning && (
            <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-800">
              {warning}
            </p>
          )}
          {latestError && (
            <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-800">
              {latestError}
            </p>
          )}
          <Button
            type="button"
            className="w-full bg-violet-600 hover:bg-violet-700"
            onClick={startAssessment}
            disabled={!birthday}
          >
            Начать оценку
          </Button>
          <button
            type="button"
            onClick={showLatestAssessment}
            disabled={loadingLatest}
            className="w-full text-center text-sm text-violet-700 hover:text-violet-900 disabled:opacity-50"
          >
            {loadingLatest ? "Загрузка…" : "Получить план по последней оценке"}
          </button>
        </div>
      </Card>
    );
  }

  if (phase === "testing" && session && currentQuestion) {
    return (
      <Card className="mx-auto max-w-lg border-violet-100 bg-gradient-to-b from-violet-50/50 to-white p-6">
        <div className="mb-4 flex items-center justify-between text-sm">
          <span className="font-medium text-violet-800">
            {currentScale.name} — шкала {scaleIndex + 1}/{SCALES.length}
          </span>
          <span className="text-slate-500">Возраст: {ageLabel}</span>
        </div>
        <div className="mb-2 h-2 overflow-hidden rounded-full bg-violet-100">
          <div
            className="h-full bg-violet-500 transition-all"
            style={{
              width: `${((scaleIndex + 1) / SCALES.length) * 100}%`,
            }}
          />
        </div>
        <p className="mb-8 mt-6 text-center text-lg font-medium leading-relaxed text-slate-800">
          {currentQuestion.text}
        </p>
        <p className="mb-6 text-center text-xs text-slate-400">
          Балл по шкале: {currentQuestion.ball}
        </p>
        <div className="flex gap-4">
          <button
            type="button"
            onClick={() => handleAnswer(true)}
            disabled={submitting}
            className="flex-1 rounded-xl bg-emerald-500 py-4 text-lg font-semibold text-white shadow-sm transition hover:bg-emerald-600 disabled:opacity-50"
          >
            Да
          </button>
          <button
            type="button"
            onClick={() => handleAnswer(false)}
            disabled={submitting}
            className="flex-1 rounded-xl bg-rose-400 py-4 text-lg font-semibold text-white shadow-sm transition hover:bg-rose-500 disabled:opacity-50"
          >
            Нет
          </button>
        </div>
        {submitting && (
          <div className="mt-4 flex items-center justify-center gap-2 text-sm text-violet-700">
            <Spinner />
            Сохраняем результаты…
          </div>
        )}
        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      </Card>
    );
  }

  return (
    <Card className="flex items-center justify-center p-12">
      <Spinner />
    </Card>
  );
}
