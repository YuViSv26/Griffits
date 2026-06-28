"""Генерирует frontend/src/data/assessmentScales.ts и griffithsNorms.ts."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = json.loads((Path(__file__).parent / "griffiths_scale.json").read_text(encoding="utf-8"))

# --- assessmentScales.ts ---
lines = [
    "/** Шкала психомоторного развития по Гриффитс (перевод Кешишян Е.С.), 0–2 года */",
    'export type ScaleKey = "locomotion" | "social" | "speech" | "eye_hand" | "play";',
    "",
    "export interface SkillQuestion {",
    "  text: string;",
    "  ball: number;",
    "  normMonth: number;",
    "  minMonths: number;",
    "  maxMonths: number;",
    "}",
    "",
    "export interface ScaleDefinition {",
    "  key: ScaleKey;",
    "  name: string;",
    "  questions: SkillQuestion[];",
    "}",
    "",
    "export const MAX_AGE_MONTHS = 24;",
    "",
    "export const AGE_BANDS: { min: number; max: number; label: string }[] = [",
    '  { min: 0, max: 3, label: "0–3 мес" },',
    '  { min: 3, max: 6, label: "3–6 мес" },',
    '  { min: 6, max: 9, label: "6–9 мес" },',
    '  { min: 9, max: 12, label: "9–12 мес" },',
    '  { min: 12, max: 18, label: "12–18 мес" },',
    '  { min: 18, max: 24, label: "18–24 мес" },',
    "];",
    "",
    "export const SCALE_NAMES: Record<ScaleKey, string> = {",
]
for k, n in DATA["scaleNames"].items():
    lines.append(f'  {k}: "{n}",')
lines.append("};")
lines.append("")
lines.append("export const SCALES: ScaleDefinition[] = [")

for key in ("locomotion", "social", "speech", "eye_hand", "play"):
    items = DATA["scales"][key]
    name = DATA["scaleNames"][key]
    lines.append("  {")
    lines.append(f'    key: "{key}",')
    lines.append(f'    name: "{name}",')
    lines.append("    questions: [")
    for q in items:
        text = q["text"].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(
            f'      {{ ball: {q["ball"]}, normMonth: {q["normMonth"]}, '
            f'minMonths: {q["minMonths"]}, maxMonths: {q["maxMonths"]}, text: "{text}" }},'
        )
    lines.append("    ],")
    lines.append("  },")
lines.append("];")
lines.append("")

(ROOT / "frontend" / "src" / "data" / "assessmentScales.ts").write_text(
    "\n".join(lines), encoding="utf-8"
)

# --- griffithsNorms.ts ---
norm_lines = [
    "/** Нормативные таблицы суммы баллов — PDF, сводные таблицы №1 и №2 */",
    "export interface TotalNormRow {",
    "  month: number;",
    "  min: number;",
    "  max: number;",
    "}",
    "",
    "export const TOTAL_NORM_BY_MONTH: TotalNormRow[] = [",
]
for row in DATA["totalNormByMonth"]:
    norm_lines.append(
        f'  {{ month: {row["month"]}, min: {row["min"]}, max: {row["max"]} }},'
    )
norm_lines.append("];")
norm_lines.append("")
norm_lines.append(
    "export const SUBSCALE_NORM_BY_MONTH: Record<string, Record<number, number>> = {"
)
for key, months in DATA["subscaleNormByMonth"].items():
    norm_lines.append(f'  "{key}": {{')
    for m, ball in sorted(months.items(), key=lambda x: int(x[0])):
        norm_lines.append(f"    {m}: {ball},")
    norm_lines.append("  },")
norm_lines.append("};")
norm_lines.append("")

(ROOT / "frontend" / "src" / "data" / "griffithsNorms.ts").write_text(
    "\n".join(norm_lines), encoding="utf-8"
)

print("generated assessmentScales.ts and griffithsNorms.ts")
