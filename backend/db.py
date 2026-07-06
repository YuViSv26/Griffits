from __future__ import annotations

import logging
import random
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import ForeignKey, Index, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.config import get_settings
from backend.data.games_seed import GAMES_SEED

logger = logging.getLogger(__name__)

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str] = mapped_column()
    baby_name: Mapped[str | None] = mapped_column(default=None)
    baby_birthday: Mapped[date | None] = mapped_column(default=None)
    last_subscale: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    assessments: Mapped[list["SkillsAssessment"]] = relationship(back_populates="user")
    chat_messages: Mapped[list["ChatMessage"]] = relationship(back_populates="user")


class SkillsAssessment(Base):
    __tablename__ = "skills_assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    date: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    score_a: Mapped[int] = mapped_column(default=0)
    score_b: Mapped[int] = mapped_column(default=0)
    score_c: Mapped[int] = mapped_column(default=0)
    score_d: Mapped[int] = mapped_column(default=0)
    score_e: Mapped[int] = mapped_column(default=0)
    child_age_months: Mapped[int | None] = mapped_column(default=None)
    result_locomotion: Mapped[str | None] = mapped_column(default=None)
    result_social: Mapped[str | None] = mapped_column(default=None)
    result_speech: Mapped[str | None] = mapped_column(default=None)
    result_eye_hand: Mapped[str | None] = mapped_column(default=None)
    result_play: Mapped[str | None] = mapped_column(default=None)
    # Устаревшие поля прежней 4-шкальной модели
    result_gross_motor: Mapped[str | None] = mapped_column(default=None)
    result_fine_motor: Mapped[str | None] = mapped_column(default=None)

    user: Mapped["User"] = relationship(back_populates="assessments")


class Game(Base):
    __tablename__ = "games"
    __table_args__ = (
        Index("ix_games_subscale_age", "subscale", "min_age_months", "max_age_months"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    min_age_months: Mapped[int] = mapped_column()
    max_age_months: Mapped[int] = mapped_column()
    subscale: Mapped[str] = mapped_column()
    develops: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    safety_rules: Mapped[str] = mapped_column()


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="chat_messages")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token: Mapped[str] = mapped_column(unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column()
    used: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )


class PlanPayment(Base):
    __tablename__ = "plan_payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    yookassa_payment_id: Mapped[str] = mapped_column(unique=True, index=True)
    amount_rub: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(default="pending")
    product: Mapped[str] = mapped_column(default="plan_pdf")
    pdf_downloaded: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    paid_at: Mapped[datetime | None] = mapped_column(default=None)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def _migrate_columns() -> None:
    """Добавляет новые колонки в существующую SQLite-базу."""
    migrations = [
        "ALTER TABLE skills_assessments ADD COLUMN child_age_months INTEGER",
        "ALTER TABLE skills_assessments ADD COLUMN result_gross_motor TEXT",
        "ALTER TABLE skills_assessments ADD COLUMN result_fine_motor TEXT",
        "ALTER TABLE skills_assessments ADD COLUMN result_speech TEXT",
        "ALTER TABLE skills_assessments ADD COLUMN result_social TEXT",
        "ALTER TABLE skills_assessments ADD COLUMN result_locomotion TEXT",
        "ALTER TABLE skills_assessments ADD COLUMN result_eye_hand TEXT",
        "ALTER TABLE skills_assessments ADD COLUMN result_play TEXT",
    ]
    async with engine.begin() as conn:
        for stmt in migrations:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _migrate_columns()


async def get_user_by_email(email: str) -> User | None:
    async with get_session() as session:
        result = await session.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()


async def get_user_by_id(user_id: int) -> User | None:
    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


async def create_user(email: str, password_hash: str) -> User:
    async with get_session() as session:
        user = User(email=email.lower(), password_hash=password_hash)
        session.add(user)
        await session.flush()
        return user


async def update_user_profile(
    user_id: int, baby_name: str, baby_birthday: date
) -> User:
    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one()
        user.baby_name = baby_name
        user.baby_birthday = baby_birthday
        await session.flush()
        return user


async def save_assessment(user_id: int, scores: dict[str, int]) -> SkillsAssessment:
    async with get_session() as session:
        assessment = SkillsAssessment(
            user_id=user_id,
            score_a=scores.get("A", 0),
            score_b=scores.get("B", 0),
            score_c=scores.get("C", 0),
            score_d=scores.get("D", 0),
            score_e=scores.get("E", 0),
        )
        session.add(assessment)
        await session.flush()
        return assessment


async def save_assessment_v2(
    user_id: int,
    age_months: int,
    results: dict[str, str | None],
) -> SkillsAssessment:
    from backend.data.assessment_scales import SCALE_TO_GAME_SUBSCALE, skill_to_score

    scores = {
        SCALE_TO_GAME_SUBSCALE[k]: skill_to_score(k, results.get(k))
        for k in ("locomotion", "social", "speech", "eye_hand", "play")
    }
    async with get_session() as session:
        assessment = SkillsAssessment(
            user_id=user_id,
            child_age_months=age_months,
            result_locomotion=results.get("locomotion"),
            result_social=results.get("social"),
            result_speech=results.get("speech"),
            result_eye_hand=results.get("eye_hand"),
            result_play=results.get("play"),
            score_a=scores.get("A", 0),
            score_b=scores.get("B", 0),
            score_c=scores.get("C", 0),
            score_d=scores.get("D", 0),
            score_e=scores.get("E", 0),
        )
        session.add(assessment)
        await session.flush()
        return assessment


async def get_latest_assessment(user_id: int) -> SkillsAssessment | None:
    async with get_session() as session:
        result = await session.execute(
            select(SkillsAssessment)
            .where(SkillsAssessment.user_id == user_id)
            .order_by(SkillsAssessment.date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def get_assessment_history(
    user_id: int, limit: int = 10
) -> list[SkillsAssessment]:
    async with get_session() as session:
        result = await session.execute(
            select(SkillsAssessment)
            .where(SkillsAssessment.user_id == user_id)
            .order_by(SkillsAssessment.date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


def _weakest_subscale(assessment: SkillsAssessment) -> str:
    from backend.data.assessment_scales import SCALE_KEYS, SCALE_TO_GAME_SUBSCALE, skill_to_score

    if assessment.child_age_months is not None:
        scale_scores = {
            k: skill_to_score(k, getattr(assessment, f"result_{k}", None))
            for k in SCALE_KEYS
        }
        min_score = min(scale_scores.values())
        weakest_scales = [k for k, v in scale_scores.items() if v == min_score]
        return SCALE_TO_GAME_SUBSCALE[random.choice(weakest_scales)]

    scores = {
        "A": assessment.score_a,
        "B": assessment.score_b,
        "C": assessment.score_c,
        "D": assessment.score_d,
        "E": assessment.score_e,
    }
    min_score = min(scores.values())
    candidates = [k for k, v in scores.items() if v == min_score]
    return random.choice(candidates)


async def get_game_for_today(
    user: User, age_months: int, assessment: SkillsAssessment | None
) -> tuple[Game | None, str]:
    subscales = ["A", "B", "C", "D", "E"]

    if assessment is not None:
        focus = _weakest_subscale(assessment)
    elif user.last_subscale and user.last_subscale in subscales:
        idx = (subscales.index(user.last_subscale) + 1) % len(subscales)
        focus = subscales[idx]
    else:
        focus = random.choice(subscales)

    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == user.id))
        db_user = result.scalar_one()
        db_user.last_subscale = focus

        game_result = await session.execute(
            select(Game).where(
                Game.min_age_months <= age_months,
                Game.max_age_months >= age_months,
                Game.subscale == focus,
            )
        )
        games = list(game_result.scalars().all())

        if not games:
            game_result = await session.execute(
                select(Game).where(
                    Game.min_age_months <= age_months,
                    Game.max_age_months >= age_months,
                )
            )
            games = list(game_result.scalars().all())
            if games:
                focus = random.choice(games).subscale
                games = [g for g in games if g.subscale == focus] or games

        if not games:
            return None, focus

        return random.choice(games), focus


async def seed_games_if_empty() -> None:
    async with get_session() as session:
        result = await session.execute(select(Game).limit(1))
        if result.scalar_one_or_none() is not None:
            return
        for item in GAMES_SEED:
            session.add(Game(**item))
        logger.info("Seeded %d games into database", len(GAMES_SEED))


def compute_scores_from_answers(
    questions: list[dict[str, str]], answers: list[bool]
) -> dict[str, int]:
    by_subscale: dict[str, list[bool]] = defaultdict(list)
    for question, answer in zip(questions, answers):
        by_subscale[question["subscale"]].append(answer)

    scores: dict[str, int] = {}
    for subscale in ("A", "B", "C", "D", "E"):
        items = by_subscale.get(subscale, [])
        scores[subscale] = round(sum(items) / len(items) * 100) if items else 0
    return scores


async def save_chat_message(user_id: int, role: str, content: str) -> ChatMessage:
    async with get_session() as session:
        msg = ChatMessage(user_id=user_id, role=role, content=content)
        session.add(msg)
        await session.flush()
        return msg


async def get_chat_history(user_id: int, limit: int = 50) -> list[ChatMessage]:
    async with get_session() as session:
        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages


async def create_password_reset_token(user_id: int, token: str, expires_at: datetime) -> None:
    async with get_session() as session:
        reset = PasswordResetToken(
            user_id=user_id, token=token, expires_at=expires_at
        )
        session.add(reset)
        await session.flush()


async def get_valid_reset_token(token: str) -> PasswordResetToken | None:
    async with get_session() as session:
        result = await session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token == token,
                PasswordResetToken.used.is_(False),
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        expires = row.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            return None
        return row


async def update_user_password(user_id: int, password_hash: str) -> None:
    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one()
        user.password_hash = password_hash
        await session.flush()


async def mark_reset_token_used(token: str) -> None:
    async with get_session() as session:
        result = await session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == token)
        )
        row = result.scalar_one_or_none()
        if row:
            row.used = True
            await session.flush()


async def save_plan_payment(
    user_id: int,
    yookassa_payment_id: str,
    amount_rub: int,
    status: str,
    product: str,
) -> PlanPayment:
    async with get_session() as session:
        row = PlanPayment(
            user_id=user_id,
            yookassa_payment_id=yookassa_payment_id,
            amount_rub=amount_rub,
            status=status,
            product=product,
        )
        session.add(row)
        await session.flush()
        return row


async def get_plan_payment(yookassa_payment_id: str) -> PlanPayment | None:
    async with get_session() as session:
        result = await session.execute(
            select(PlanPayment).where(
                PlanPayment.yookassa_payment_id == yookassa_payment_id
            )
        )
        return result.scalar_one_or_none()


async def get_latest_plan_payment(user_id: int) -> PlanPayment | None:
    async with get_session() as session:
        result = await session.execute(
            select(PlanPayment)
            .where(PlanPayment.user_id == user_id)
            .order_by(PlanPayment.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def update_plan_payment_status(
    yookassa_payment_id: str,
    status: str,
    paid_at: datetime | None = None,
) -> PlanPayment:
    async with get_session() as session:
        result = await session.execute(
            select(PlanPayment).where(
                PlanPayment.yookassa_payment_id == yookassa_payment_id
            )
        )
        row = result.scalar_one()
        row.status = status
        if paid_at is not None:
            row.paid_at = paid_at
        await session.flush()
        return row


async def mark_plan_payment_downloaded(yookassa_payment_id: str) -> None:
    async with get_session() as session:
        result = await session.execute(
            select(PlanPayment).where(
                PlanPayment.yookassa_payment_id == yookassa_payment_id
            )
        )
        row = result.scalar_one()
        row.pdf_downloaded = True
        await session.flush()
