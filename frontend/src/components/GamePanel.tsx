import { useEffect, useRef, useState } from "react";
import { api, type TodayPlanResponse } from "../api/client";
import { exportElementToPdf } from "../lib/exportPdf";
import { Button, Card, Spinner } from "./ui";

const PLAN_PRICE_RUB = 199;

export function GamePanel() {
  const [plan, setPlan] = useState<TodayPlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);
  const [paid, setPaid] = useState(false);
  const printRef = useRef<HTMLDivElement>(null);

  const load = () => {
    setLoading(true);
    setError("");
    api
      .getTodayPlan()
      .then(setPlan)
      .catch((e) => {
        setPlan(null);
        setError(e.message);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handlePayAndPdf = async () => {
    if (!plan || !printRef.current) return;

    if (!paid) {
      const ok = window.confirm(
        `Стоимость персонального плана: ${PLAN_PRICE_RUB} ₽.\n\n` +
          "Демо-режим: реальная оплата не подключена. Продолжить и сохранить PDF бесплатно?"
      );
      if (!ok) return;
      setPaid(true);
    }

    setExporting(true);
    try {
      const date = new Date().toISOString().slice(0, 10);
      await exportElementToPdf(
        printRef.current,
        `plan-${plan.baby_name}-${date}.pdf`
      );
    } catch {
      setError("Не удалось создать PDF. Попробуйте ещё раз.");
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <Card className="flex items-center justify-center p-12">
        <Spinner />
      </Card>
    );
  }

  if (error && !plan) {
    return (
      <Card className="p-6 text-center">
        <p className="text-slate-600">{error}</p>
        <Button className="mt-4" onClick={load}>
          Попробовать снова
        </Button>
      </Card>
    );
  }

  if (!plan) return null;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div ref={printRef} className="space-y-6 bg-white p-1">
        <Card className="overflow-hidden border-brand-100">
          <div className="bg-gradient-to-r from-brand-600 to-brand-700 px-6 py-5 text-white">
            <p className="text-sm opacity-90">План на сегодня</p>
            <h2 className="text-2xl font-semibold">{plan.baby_name}</h2>
            <p className="mt-1 text-sm opacity-90">
              Возраст: {plan.age_label} · Фокус: {plan.focus_scale_name}
            </p>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-slate-800">
            1. Что обычно умеют в {plan.age_months} мес. (шкала Гриффитс)
          </h3>
          <p className="mt-1 text-sm text-slate-500">
            Ориентиры по методике Кешишян — сравните с вашим малышом
          </p>
          <div className="mt-4 space-y-4">
            {plan.expected_skills.map((block) => (
              <div key={block.scale}>
                <p className="font-medium text-brand-700">{block.scale_name}</p>
                <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-slate-600">
                  {block.skills.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </Card>

        <Card className="border-amber-100 bg-amber-50/50 p-6">
          <h3 className="text-lg font-semibold text-amber-900">
            2. На что обратить внимание
          </h3>
          <ul className="mt-3 space-y-2 text-sm text-amber-950">
            {plan.attention_points.map((p) => (
              <li key={p} className="flex gap-2">
                <span className="text-amber-600">•</span>
                <span>{p}</span>
              </li>
            ))}
          </ul>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-slate-800">
            3. Игры для развития «{plan.focus_scale_name}»
          </h3>
          <div className="mt-4 space-y-4">
            {plan.games.map((game) => (
              <div
                key={game.title}
                className="rounded-xl border border-slate-100 bg-slate-50/80 p-4"
              >
                <p className="font-semibold text-slate-800">{game.title}</p>
                <p className="mt-1 text-xs text-brand-600">{game.develops}</p>
                <p className="mt-2 text-sm text-slate-600">{game.description}</p>
                <p className="mt-2 rounded-lg bg-amber-50 p-2 text-xs text-amber-900">
                  {game.safety_rules}
                </p>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-slate-800">
            4. Как заниматься
          </h3>
          <div className="mt-4 overflow-hidden rounded-xl border border-slate-200">
            <table className="w-full text-sm">
              <tbody>
                {plan.practice_tips.map((tip) => (
                  <tr key={tip.label} className="border-b border-slate-100 last:border-0">
                    <td className="w-36 bg-slate-50 px-4 py-3 font-medium text-slate-700">
                      {tip.icon} {tip.label}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{tip.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card className="border-violet-100 bg-violet-50/40 p-6">
          <h3 className="text-lg font-semibold text-violet-900">
            5. Важно помнить
          </h3>
          <p className="mt-3 text-sm leading-relaxed text-violet-950">
            {plan.important_reminder}
          </p>
        </Card>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex flex-col gap-3 sm:flex-row">
        <Button
          className="flex-1 bg-brand-600 hover:bg-brand-700"
          onClick={handlePayAndPdf}
          disabled={exporting}
        >
          {exporting ? (
            <Spinner />
          ) : paid ? (
            "Сохранить в PDF"
          ) : (
            `Оплатить ${PLAN_PRICE_RUB} ₽ и сохранить в PDF`
          )}
        </Button>
        <Button variant="secondary" onClick={load}>
          Обновить план
        </Button>
      </div>
    </div>
  );
}
