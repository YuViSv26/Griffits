/**
 * Сумма баллов и возрастной эквивалент по нормативным таблицам Гриффитс (Кешишян).
 */

import {
  SCALES,
  SCALE_NAMES,
  type ScaleKey,
} from "../data/assessmentScales";
import { SUBSCALE_NORM_BY_MONTH, TOTAL_NORM_BY_MONTH } from "../data/griffithsNorms";
import type { ScaleResults } from "./assessmentEngine";

export interface ScaleSummaryItem {
  scaleKey: ScaleKey;
  name: string;
  skill: string | null;
  ball: number | null;
  ageEquivalentMonths: number | null;
}

export interface GriffithsSummary {
  chronologicAgeMonths: number;
  totalBalls: number;
  totalAgeEquivalentMonths: number;
  normTotalAtAge: { month: number; min: number; max: number };
  scales: ScaleSummaryItem[];
}

const BALL_BY_TEXT: Record<ScaleKey, Map<string, number>> = {
  locomotion: new Map(),
  social: new Map(),
  speech: new Map(),
  eye_hand: new Map(),
  play: new Map(),
};

const NORM_MONTH_BY_TEXT: Record<ScaleKey, Map<string, number>> = {
  locomotion: new Map(),
  social: new Map(),
  speech: new Map(),
  eye_hand: new Map(),
  play: new Map(),
};

for (const scale of SCALES) {
  for (const q of scale.questions) {
    BALL_BY_TEXT[scale.key].set(q.text, q.ball);
    NORM_MONTH_BY_TEXT[scale.key].set(q.text, q.normMonth);
  }
}

/** Нормативная сумма баллов для хронологического возраста (сводная таблица PDF). */
export function totalNormForAge(ageMonths: number): {
  month: number;
  min: number;
  max: number;
} {
  const month = Math.max(1, Math.min(24, ageMonths > 0 ? ageMonths : 1));
  const row = TOTAL_NORM_BY_MONTH.find((r) => r.month === month)!;
  return { month, min: row.min, max: row.max };
}

/** Возрастной эквивалент по сумме баллов всех субшкал. */
export function ageEquivalentFromTotal(total: number): number {
  if (total <= 0) return 0;
  for (const row of TOTAL_NORM_BY_MONTH) {
    if (total >= row.min && total <= row.max) return row.month;
  }
  if (total < TOTAL_NORM_BY_MONTH[0].min) return 1;
  if (total > TOTAL_NORM_BY_MONTH[TOTAL_NORM_BY_MONTH.length - 1].max) return 24;

  let bestMonth = 1;
  let bestDist = Infinity;
  for (const row of TOTAL_NORM_BY_MONTH) {
    const mid = (row.min + row.max) / 2;
    const dist = Math.abs(total - mid);
    if (dist < bestDist) {
      bestDist = dist;
      bestMonth = row.month;
    }
  }
  return bestMonth;
}

/** Возрастной эквивалент субшкалы по достигнутому баллу. */
export function ageEquivalentFromSubscaleBall(
  scaleKey: ScaleKey,
  ball: number | null
): number | null {
  if (!ball || ball <= 0) return null;
  const norms = SUBSCALE_NORM_BY_MONTH[scaleKey];
  let best = 1;
  for (let m = 1; m <= 24; m++) {
    if ((norms[m] ?? 0) <= ball) best = m;
  }
  return best;
}

/** Полный итог оценки: баллы, эквиваленты, сравнение с нормой. */
export function computeGriffithsSummary(
  results: ScaleResults,
  chronologicAgeMonths: number
): GriffithsSummary {
  const scales: ScaleSummaryItem[] = [];
  let totalBalls = 0;

  for (const key of Object.keys(SCALE_NAMES) as ScaleKey[]) {
    const skill = results[key];
    const ball = skill ? (BALL_BY_TEXT[key].get(skill) ?? null) : null;
    if (ball) totalBalls += ball;

    scales.push({
      scaleKey: key,
      name: SCALE_NAMES[key],
      skill,
      ball,
      ageEquivalentMonths: skill
        ? (NORM_MONTH_BY_TEXT[key].get(skill) ?? null)
        : null,
    });
  }

  return {
    chronologicAgeMonths,
    totalBalls,
    totalAgeEquivalentMonths: ageEquivalentFromTotal(totalBalls),
    normTotalAtAge: totalNormForAge(chronologicAgeMonths),
    scales,
  };
}

export function formatAgeMonths(months: number): string {
  if (months <= 0) return "—";
  const n = months % 100;
  const mod10 = n % 10;
  const mod100 = n % 100;
  let word = "месяцев";
  if (mod10 === 1 && mod100 !== 11) word = "месяц";
  else if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20))
    word = "месяца";
  return `${months} ${word}`;
}
