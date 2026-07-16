export function validateBirthParts(
  day: string,
  month: string,
  year: string,
): string | null {
  const d = Number(day);
  const m = Number(month);
  const y = Number(year);
  if (!Number.isInteger(d) || !Number.isInteger(m) || !Number.isInteger(y)) {
    return "Укажите дату рождения числами";
  }
  if (y < 1920 || y > new Date().getFullYear()) {
    return "Укажите корректный год рождения";
  }
  const parsed = new Date(y, m - 1, d);
  if (
    parsed.getFullYear() !== y ||
    parsed.getMonth() !== m - 1 ||
    parsed.getDate() !== d
  ) {
    return "Некорректная дата рождения";
  }
  return null;
}

export type LoginCodeAuthPayload = {
  login_code: string;
  birth_day: number;
  birth_month: number;
  birth_year: number;
};

export function toLoginCodeAuthPayload(
  loginCode: string,
  day: string,
  month: string,
  year: string,
): LoginCodeAuthPayload | { error: string } {
  const code = loginCode.trim().toUpperCase();
  if (code.length !== 6) {
    return { error: "ФИО должно содержать ровно 6 знаков" };
  }

  const birthError = validateBirthParts(day, month, year);
  if (birthError) return { error: birthError };

  return {
    login_code: code,
    birth_day: Number(day),
    birth_month: Number(month),
    birth_year: Number(year),
  };
}
