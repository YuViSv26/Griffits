import { useMemo, useState } from "react";
import { api, type ScaleResultItem } from "../api/client";
import { SCALES, type ScaleKey } from "../data/assessmentScales";
import {
  calculateAge,
  createScaleSession,
  getGames,
  processAnswer,
  type ScaleResults,
  type ScaleSessionState,
} from "../lib/assessmentEngine";
import {
  computeGriffithsSummary,
  formatAgeMonths,
} from "../lib/griffithsScoring";
import { Button, Card, Input, Label, Spinner } from "./ui";
import { PlanPaymentPrompt } from "./PlanPaymentPrompt";

type Phase = "start" | "testing" | "results";

interface Props {
  babyBirthday?: string;
  userEmail?: string;
  returnFromPayment?: boolean;
  paymentId?: string;
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
  userEmail,
  returnFromPayment = false,
  paymentId,
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
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const [isReadOnly, setIsReadOnly] = useState(false);
  const [testDate, setTestDate] = useState<string | null>(null);
  const [loadingLatest, setLoadingLatest] = useState(false);
  const [latestError, setLatestError] = useState("");

  const currentScale = SCALES[scaleIndex];
  const currentQuestion = session
    ? currentScale?.questions[session.currentIndex]
    : null;

  const recommendedGames = useMemo(() => {
    if (phase !== "results") return [];
    return getGames(allResults as ScaleResults, ageMonths);
  }, [phase, allResults, ageMonths]);

  const summary = useMemo(() => {
    if (phase !== "results") return null;
    return computeGriffithsSummary(allResults as ScaleResults, ageMonths);
  }, [phase, allResults, ageMonths]);

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

  const finishScale = (result: string | null) => {
    const key = currentScale.key;
    const updated = { ...allResults, [key]: result };

    if (scaleIndex + 1 >= SCALES.length) {
      setAllResults(updated);
      setPhase("results");
      setSession(null);
      return;
    }

    setAllResults(updated);
    const nextIndex = scaleIndex + 1;
    setScaleIndex(nextIndex);
    setSession(createScaleSession(SCALES[nextIndex], ageMonths));
  };

  const handleAnswer = (yes: boolean) => {
    if (!session || !currentScale) return;
    const next = processAnswer(currentScale, session, yes);
    setSession(next);
    if (next.finished) {
      finishScale(next.resultSkill);
    }
  };

  const saveResults = async () => {
    setSubmitting(true);
    setError("");
    try {
      await api.submitAssessment({
        age_months: ageMonths,
        results: allResults as ScaleResults,
      });
      setSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка сохранения");
    } finally {
      setSubmitting(false);
    }
  };

  if (returnFromPayment) {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <PlanPaymentPrompt
          userEmail={userEmail}
          returnFromPayment={returnFromPayment}
          paymentId={paymentId}
          onDone={onComplete}
        />
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
            <Input
              type="date"
              value={birthday}
              onChange={(e) => setBirthday(e.target.value)}
              required
            />
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
            {loadingLatest ? "Загрузка…" : "Показать крайнюю оценку"}
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
            className="flex-1 rounded-xl bg-emerald-500 py-4 text-lg font-semibold text-white shadow-sm transition hover:bg-emerald-600"
          >
            Да
          </button>
          <button
            type="button"
            onClick={() => handleAnswer(false)}
            className="flex-1 rounded-xl bg-rose-400 py-4 text-lg font-semibold text-white shadow-sm transition hover:bg-rose-500"
          >
            Нет
          </button>
        </div>
      </Card>
    );
  }

  if (phase === "results" && summary) {
    const norm = summary.normTotalAtAge;
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <Card className="border-violet-200 bg-gradient-to-b from-violet-50/60 to-white p-6">
          <h2 className="text-xl font-semibold text-violet-900">
            {isReadOnly ? "Последняя сохранённая оценка" : "Итог по шкале Гриффитс"}
          </h2>
          {isReadOnly && testDate && (
            <p className="mt-1 text-sm text-violet-600">Дата теста: {testDate}</p>
          )}
          <p className="mt-1 text-sm text-slate-500">
            Возраст на момент теста: {ageLabel}
          </p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl bg-white p-4 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                Сумма баллов
              </p>
              <p className="mt-1 text-2xl font-semibold text-violet-900">
                {summary.totalBalls}
                <span className="ml-2 text-sm font-normal text-slate-500">
                  (норма к {formatAgeMonths(norm.month)}: {norm.min}
                  {norm.min !== norm.max ? `–${norm.max}` : ""})
                </span>
              </p>
            </div>
            <div className="rounded-xl bg-white p-4 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                Общий возрастной эквивалент
              </p>
              <p className="mt-1 text-2xl font-semibold text-violet-900">
                {formatAgeMonths(summary.totalAgeEquivalentMonths)}
              </p>
              {!isReadOnly && summary.totalAgeEquivalentMonths < ageMonths && (
                <p className="mt-1 text-xs text-amber-700">
                  Ниже хронологического возраста на{" "}
                  {ageMonths - summary.totalAgeEquivalentMonths}{" "}
                  {ageMonths - summary.totalAgeEquivalentMonths === 1
                    ? "месяц"
                    : "мес."}
                </p>
              )}
            </div>
          </div>
        </Card>

        <Card className="border-violet-100 p-6">
          <h3 className="text-lg font-semibold text-violet-900">
            Результаты по субшкалам
          </h3>
          <table className="mt-4 w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="pb-2 pr-3 font-medium">Субшкала</th>
                <th className="pb-2 pr-3 font-medium">Балл</th>
                <th className="pb-2 pr-3 font-medium">Возр. экв.</th>
                <th className="pb-2 font-medium">Навык</th>
              </tr>
            </thead>
            <tbody>
              {summary.scales.map((row) => (
                <tr key={row.scaleKey} className="border-b border-slate-100">
                  <td className="py-3 pr-3 font-medium text-slate-700">
                    {row.name}
                  </td>
                  <td className="py-3 pr-3 text-slate-600">
                    {row.ball ?? "—"}
                  </td>
                  <td className="py-3 pr-3 text-slate-600">
                    {row.ageEquivalentMonths
                      ? formatAgeMonths(row.ageEquivalentMonths)
                      : "—"}
                  </td>
                  <td className="py-3 text-slate-600">
                    {row.skill ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card className="border-emerald-100 bg-emerald-50/40 p-6">
          <h3 className="text-lg font-semibold text-emerald-900">
            Рекомендуемые игры
          </h3>
          <ul className="mt-4 space-y-3">
            {recommendedGames.map((g) => (
              <li
                key={g.title}
                className="rounded-xl bg-white p-4 shadow-sm"
              >
                <p className="font-medium text-slate-800">{g.title}</p>
                <p className="text-xs text-violet-600">{g.scale}</p>
                <p className="mt-1 text-sm text-slate-600">{g.description}</p>
              </li>
            ))}
          </ul>
        </Card>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {(saved || isReadOnly) && (
          <PlanPaymentPrompt userEmail={userEmail} onDone={onComplete} />
        )}

        <div className="flex gap-3">
          {isReadOnly ? (
            <>
              <Button
                className="flex-1 bg-violet-600 hover:bg-violet-700"
                onClick={resetToStart}
              >
                Начать новую оценку
              </Button>
              <Button variant="secondary" onClick={onSkip}>
                Закрыть
              </Button>
            </>
          ) : saved ? (
            <Button variant="secondary" onClick={onComplete}>
              Перейти к прогрессу
            </Button>
          ) : (
            <>
              <Button
                className="flex-1 bg-violet-600 hover:bg-violet-700"
                onClick={saveResults}
                disabled={submitting}
              >
                {submitting ? (
                  <Spinner />
                ) : (
                  "Сохранить и получить план на email"
                )}
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

  return (
    <Card className="flex items-center justify-center p-12">
      <Spinner />
    </Card>
  );
}
