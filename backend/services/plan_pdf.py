"""Генерация PDF плана развития на сервере."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

from backend.schemas.today_plan import TodayPlanResponse

_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "fonts"
_FONT_CANDIDATES = [
    (_DATA_DIR / "Arial.ttf", _DATA_DIR / "Arial-Bold.ttf"),
    (_DATA_DIR / "DejaVuSans.ttf", _DATA_DIR / "DejaVuSans-Bold.ttf"),
    (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ),
]


def _resolve_fonts() -> tuple[str, str]:
    for regular, bold in _FONT_CANDIDATES:
        if regular.is_file() and bold.is_file():
            return str(regular), str(bold)
    raise FileNotFoundError(
        "Не найдены шрифты для PDF. Установите fonts-dejavu-core или добавьте TTF в backend/data/fonts/"
    )


class _PlanPDF(FPDF):
    def __init__(self) -> None:
        super().__init__()
        regular, bold = _resolve_fonts()
        self.add_font("PlanFont", "", regular)
        self.add_font("PlanFont", "B", bold)
        self.set_auto_page_break(auto=True, margin=15)


def _title(pdf: _PlanPDF, text: str, size: int = 14) -> None:
    pdf.set_font("PlanFont", "B", size)
    pdf.multi_cell(pdf.epw, 8, text)
    pdf.ln(2)


def _text(pdf: _PlanPDF, text: str, size: int = 11, bold: bool = False) -> None:
    pdf.set_font("PlanFont", "B" if bold else "", size)
    pdf.multi_cell(pdf.epw, 6, text)
    pdf.ln(1)


def _bullet_list(pdf: _PlanPDF, items: list[str], size: int = 10) -> None:
    pdf.set_font("PlanFont", "", size)
    for item in items:
        pdf.multi_cell(pdf.epw, 5, f"• {item}")
    pdf.ln(2)


def generate_plan_pdf(plan: TodayPlanResponse) -> bytes:
    pdf = _PlanPDF()
    pdf.add_page()

    pdf.set_font("PlanFont", "", 12)
    pdf.cell(0, 8, "План на сегодня", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("PlanFont", "B", 18)
    pdf.cell(0, 10, plan.baby_name, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("PlanFont", "", 12)
    pdf.cell(
        0,
        8,
        f"Возраст: {plan.age_label} · Фокус: {plan.focus_scale_name}",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(6)

    _title(
        pdf,
        f"1. Что обычно умеют в {plan.age_months} мес. (шкала Гриффитс)",
    )
    _text(
        pdf,
        "Ориентиры по методике Кешишян — сравните с вашим малышом",
        size=10,
    )
    for block in plan.expected_skills:
        _text(pdf, block.scale_name, size=11, bold=True)
        _bullet_list(pdf, block.skills)

    _title(pdf, "2. На что обратить внимание")
    _bullet_list(pdf, plan.attention_points)

    _title(pdf, f"3. Игры для развития «{plan.focus_scale_name}»")
    for game in plan.games:
        _text(pdf, game.title, size=12, bold=True)
        _text(pdf, game.develops, size=9)
        _text(pdf, game.description, size=10)
        _text(pdf, f"Безопасность: {game.safety_rules}", size=9)
        pdf.ln(3)

    _title(pdf, "4. Как заниматься")
    for tip in plan.practice_tips:
        _text(pdf, f"{tip.icon} {tip.label}: {tip.value}", size=10)

    _title(pdf, "5. Важно помнить")
    _text(pdf, plan.important_reminder, size=10)

    return bytes(pdf.output())
