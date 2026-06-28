/**
 * Движок адаптивного опроса по шкале Гриффитс (Кешишян).
 * «Да» — к более сложному пункту, «Нет» — к более простому;
 * результат — последний пункт с ответом «Да» (по баллу).
 */

import {
  AGE_BANDS,
  MAX_AGE_MONTHS,
  type ScaleDefinition,
  type ScaleKey,
  type SkillQuestion,
} from "../data/assessmentScales";

export interface AgeValidation {
  ok: boolean;
  months: number;
  label: string;
  warning?: string;
}

export interface ScaleSessionState {
  scaleKey: ScaleKey;
  currentIndex: number;
  answers: Record<number, boolean>;
  finished: boolean;
  resultSkill: string | null;
}

export type ScaleResults = Record<ScaleKey, string | null>;

/** Возраст в полных месяцах; шкала рассчитана на 0–24 мес. */
export function calculateAge(birthdayIso: string, today = new Date()): AgeValidation {
  const birth = new Date(birthdayIso);
  const t = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const b = new Date(birth.getFullYear(), birth.getMonth(), birth.getDate());

  if (b > t) {
    return {
      ok: false,
      months: 0,
      label: "",
      warning: "Дата рождения не может быть в будущем.",
    };
  }

  let months =
    (t.getFullYear() - b.getFullYear()) * 12 + (t.getMonth() - b.getMonth());
  if (t.getDate() < b.getDate()) months -= 1;
  if (months < 0) months = 0;

  const extraDays = Math.max(
    0,
    Math.floor((t.getTime() - b.getTime()) / (1000 * 60 * 60 * 24)) % 30
  );

  if (months > MAX_AGE_MONTHS) {
    return {
      ok: false,
      months,
      label: `${months} мес.`,
      warning: `Возраст больше ${MAX_AGE_MONTHS} месяцев. Шкала Гриффитс из методички рассчитана на детей 0–2 лет.`,
    };
  }

  return {
    ok: true,
    months,
    label: `${months} мес. ${extraDays} дн.`,
  };
}

export function getAgeBand(months: number) {
  for (let i = AGE_BANDS.length - 1; i >= 0; i--) {
    const band = AGE_BANDS[i];
    if (months >= band.min) return band;
  }
  return AGE_BANDS[0];
}

/**
 * Стартовый пункт — ближайший к возрасту ребёнка по полю maxMonths,
 * иначе пункт с минимальной разницей по возрасту.
 */
export function getInitialQuestionIndex(
  questions: SkillQuestion[],
  ageMonths: number
): number {
  const inBand = questions.findIndex(
    (q) => ageMonths >= q.minMonths && ageMonths <= q.maxMonths
  );
  if (inBand >= 0) return inBand;

  let best = 0;
  let bestDist = Infinity;
  for (let i = 0; i < questions.length; i++) {
    const dist = Math.abs(questions[i].maxMonths - ageMonths);
    if (dist < bestDist) {
      bestDist = dist;
      best = i;
    }
  }
  return best;
}

export function getHardestYesSkill(
  questions: SkillQuestion[],
  answers: Record<number, boolean>
): string | null {
  let bestIndex = -1;
  for (const [idxStr, yes] of Object.entries(answers)) {
    const idx = Number(idxStr);
    if (yes && idx > bestIndex) bestIndex = idx;
  }
  return bestIndex >= 0 ? questions[bestIndex].text : null;
}

export function createScaleSession(
  scale: ScaleDefinition,
  ageMonths: number
): ScaleSessionState {
  return {
    scaleKey: scale.key,
    currentIndex: getInitialQuestionIndex(scale.questions, ageMonths),
    answers: {},
    finished: false,
    resultSkill: null,
  };
}

export function processAnswer(
  scale: ScaleDefinition,
  state: ScaleSessionState,
  answerYes: boolean
): ScaleSessionState {
  const questions = scale.questions;
  const i = state.currentIndex;
  const answers = { ...state.answers, [i]: answerYes };

  if (answerYes) {
    if (i >= questions.length - 1) {
      return {
        ...state,
        answers,
        finished: true,
        resultSkill: questions[i].text,
      };
    }
    return { ...state, answers, currentIndex: i + 1 };
  }

  if (i === 0) {
    return {
      ...state,
      answers,
      finished: true,
      resultSkill: null,
    };
  }

  const prevIndex = i - 1;
  if (prevIndex in answers) {
    return {
      ...state,
      answers,
      finished: true,
      resultSkill: getHardestYesSkill(questions, answers),
    };
  }

  return { ...state, answers, currentIndex: prevIndex };
}

export interface RecommendedGame {
  title: string;
  scale: string;
  description: string;
}

/** Игры по слабым/сильным сторонам пяти субшкал Гриффитс */
export function getGames(
  results: ScaleResults,
  ageMonths: number
): RecommendedGame[] {
  const games: RecommendedGame[] = [];
  const add = (scale: string, title: string, description: string) => {
    if (!games.some((g) => g.title === title)) {
      games.push({ scale, title, description });
    }
  };

  if (!results.locomotion) {
    add("Моторика", "Животик-время", "Укрепление шеи и спины на мягкой поверхности.");
  } else if (ageMonths < 9) {
    add("Моторика", "Ползание к игрушке", "Поощряйте добраться до любимой игрушки.");
  } else {
    add("Моторика", "Мячик и движение", "Катайте мягкий мяч, ходите вдоль опоры.");
  }

  if (!results.social) {
    add("Социальная адаптация", "Глаза в глаза", "Спокойный контакт, улыбки и мимика.");
  } else if (ageMonths < 12) {
    add("Социальная адаптация", 'Игра "ку-ку"', "Классическая игра с платком.");
  } else {
    add("Социальная адаптация", "Сюжетная игра", "Кормите куклу, разыгрывайте бытовые сцены.");
  }

  if (!results.speech) {
    add("Слух и речь", "Эхо малыша", "Повторяйте звуки ребёнка, пойте колыбельные.");
  } else if (ageMonths < 12) {
    add("Слух и речь", 'Игра "Где мячик?"', "Спрашивайте и показывайте знакомые предметы.");
  } else {
    add("Слух и речь", "Книжка с картинками", "Называйте предметы на картинке.");
  }

  if (!results.eye_hand) {
    add("Глаза и руки", "Погремушка в ладошке", "Лёгкая погремушка для хвата.");
  } else if (ageMonths < 12) {
    add("Глаза и руки", "Кольца на пирамидке", "Надевание колец с поддержкой.");
  } else {
    add("Глаза и руки", "Башня из кубиков", "Стройте башню вместе.");
  }

  if (!results.play) {
    add("Способность к игре", "Разные фактуры", "Дайте безопасные предметы разной формы.");
  } else if (ageMonths < 12) {
    add("Способность к игре", "Коробочка с сюрпризом", "Прячьте и находите игрушку.");
  } else {
    add("Способность к игре", "Сортировка форм", "Вкладывайте фигуры в подходящие отверстия.");
  }

  return games;
}
